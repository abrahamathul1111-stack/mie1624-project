"""Build calibrated policy-impact matrices from recommendation mappings."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import re

import pandas as pd


DEFAULT_IMPACT_MAPPING_PATH = Path("data") / "processed" / "impact_matrix_long.csv"
DEFAULT_EFFECT_CALIBRATION_PATH = Path("data") / "calibration" / "calibration_effects.csv"
DEFAULT_LAG_CALIBRATION_PATH = Path("data") / "calibration" / "calibration_lags.csv"
DEFAULT_BASELINE_KPI_PATH = Path("outputs") / "tables" / "baseline_kpi_scores.csv"
DEFAULT_OUTPUT_DIR = Path("outputs") / "tables"

REQUIRED_MAPPING_COLUMNS = [
    "recommendation",
    "lever",
    "KPI",
    "effect_strength",
    "lag_class",
    "directness",
    "rationale",
]
REQUIRED_EFFECT_COLUMNS = [
    "recommendation_id",
    "lever_id",
    "lever_name",
    "kpi",
    "effect_direction",
    "effect_low",
    "effect_base",
    "effect_high",
    "source",
    "rationale",
    "confidence",
]
REQUIRED_LAG_COLUMNS = [
    "recommendation_id",
    "lever_id",
    "kpi",
    "lag_quarters_low",
    "lag_quarters_base",
    "lag_quarters_high",
    "ramp_type",
    "source",
    "rationale",
    "confidence",
]
REQUIRED_BASELINE_COLUMNS = ["kpi_order", "kpi"]

STRENGTH_BASE_COEFFICIENTS = {
    0: 0.0000,
    1: 0.0100,
    2: 0.0250,
    3: 0.0400,
}
CONFIDENCE_FACTORS = {
    "weak": 0.85,
    "weak-to-medium": 0.925,
    "medium": 1.00,
    "medium on direction, weak on size": 0.90,
}
COEFFICIENT_SCALE = "normalized_0_to_1_additive_delta_at_full_adoption"

RECOMMENDATION_ID_BY_KEY = {
    "buildcareermoatsfortalent": "rec1",
    "buildtheconditionstoscaleaiincanada": "rec2",
    "stimulateb2bdemandviaadoptioncredits": "rec3",
}
LEVER_CONFIG_BY_KEY = {
    "eliteequitytaxexemptionforprincipallevelaiengineers": {
        "lever_id": "rec1_detail_1",
        "default_effect_archetype": "rec1_lever2",
        "default_lag_archetype": "rec1_lever2",
        "mapping_note": "Borrowed compensation/retention calibration because no exact equity-tax anchor row exists.",
    },
    "11salarymatchingtaxcreditfortopaihires": {
        "lever_id": "rec1_detail_2",
        "default_effect_archetype": "rec1_lever2",
        "default_lag_archetype": "rec1_lever2",
        "mapping_note": "Borrowed compensation/retention calibration because no exact salary-match anchor row exists.",
    },
    "aielitefasttrackvisaandpermanentresidencystream": {
        "lever_id": "rec1_detail_3",
        "default_effect_archetype": "rec1_lever1",
        "default_lag_archetype": "rec1_lever1",
        "mapping_note": "Matched to the immigration fast-track calibration row.",
    },
    "computeutilizationsubsidyfordomesticaifirms": {
        "lever_id": "rec2_detail_1",
        "default_effect_archetype": "rec2_lever1",
        "default_lag_archetype": "rec2_lever1",
        "mapping_note": "Commercial rows borrow commercialization-stage support; R&D rows borrow commercialization-ready R&D funding.",
    },
    "growthstagecoinvestmentandlaterstagescaleupcapital": {
        "lever_id": "rec2_detail_2",
        "default_effect_archetype": "rec2_lever1",
        "default_lag_archetype": "rec2_lever1",
        "mapping_note": "Commercial rows borrow co-investment calibration; patent/development rows borrow commercialization-ready R&D funding.",
    },
    "federalprocurementchallengeandpilottocontractconversionprogram": {
        "lever_id": "rec2_detail_3",
        "default_effect_archetype": "rec3_lever2",
        "default_lag_archetype": "rec3_lever2",
        "mapping_note": "Borrowed demand-pull procurement calibration because this lever is contract-conversion driven.",
    },
    "3040refundablefirstcustomeraiadoptiontaxcredit": {
        "lever_id": "rec3_detail_1",
        "default_effect_archetype": "rec3_lever1",
        "default_lag_archetype": "rec3_lever1",
        "mapping_note": "Matched to the adoption-subsidy calibration row for adoption and borrowed demand-pull calibration for downstream commercial spillovers.",
    },
    "eligibilityrulesfavorcanadianownedipandcanadianaiscaleups": {
        "lever_id": "rec3_detail_2",
        "default_effect_archetype": "rec3_lever2",
        "default_lag_archetype": "rec3_lever2",
        "mapping_note": "Borrowed demand-pull calibration because this lever governs which firms benefit from the adoption-credit bundle.",
    },
    "18monthconversionmandateandclawbackforfailedpilots": {
        "lever_id": "rec3_detail_3",
        "default_effect_archetype": "rec3_lever2",
        "default_lag_archetype": "rec3_lever2",
        "mapping_note": "Matched to the contract-conversion / demand-pull calibration row.",
    },
}

RESEARCH_DEVELOPMENT_KPIS = {
    "Tortoise Research Score",
    "AI Publications (Total)",
    "AI Citations (% of World Total)",
    "Notable AI Models",
    "Academia-Industry Concentration",
    "Tortoise Development Score",
    "AI Patent Grants (per 100k)",
}
COMMERCIAL_KPIS = {
    "Tortoise Commercial Score",
    "AI Investment Activity",
    "AI Adoption (%)",
}


class PolicyImpactMatrixError(ValueError):
    """Raised when impact-matrix inputs cannot be aligned deterministically."""


@dataclass(slots=True)
class PolicyImpactMatrixResult:
    """Container for policy-impact matrix artifacts."""

    baseline_kpis: list[str]
    metadata: pd.DataFrame
    matrix: pd.DataFrame
    export_paths: dict[str, Path] = field(default_factory=dict)


def build_policy_impact_artifacts(
    baseline_kpi_path: str | Path = DEFAULT_BASELINE_KPI_PATH,
    recommendation_mapping_path: str | Path = DEFAULT_IMPACT_MAPPING_PATH,
    calibration_effects_path: str | Path = DEFAULT_EFFECT_CALIBRATION_PATH,
    calibration_lags_path: str | Path = DEFAULT_LAG_CALIBRATION_PATH,
    output_dir: str | Path | None = None,
) -> PolicyImpactMatrixResult:
    """Build the long and wide impact-matrix artifacts and write them to disk."""

    baseline_kpis = load_baseline_kpis(baseline_kpi_path)
    mapping = load_recommendation_mapping(recommendation_mapping_path)
    effect_calibration = load_effect_calibration(calibration_effects_path)
    lag_calibration = load_lag_calibration(calibration_lags_path)

    metadata = build_policy_impact_metadata(
        mapping=mapping,
        baseline_kpis=baseline_kpis,
        effect_calibration=effect_calibration,
        lag_calibration=lag_calibration,
    )
    matrix = build_policy_impact_matrix(metadata=metadata, baseline_kpis=baseline_kpis)

    resolved_output_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir is not None
        else (Path.cwd() / DEFAULT_OUTPUT_DIR).resolve()
    )
    export_paths = export_policy_impact_outputs(
        metadata=metadata,
        matrix=matrix,
        output_dir=resolved_output_dir,
    )
    return PolicyImpactMatrixResult(
        baseline_kpis=baseline_kpis,
        metadata=metadata,
        matrix=matrix,
        export_paths=export_paths,
    )


def load_baseline_kpis(path: str | Path) -> list[str]:
    """Load the ordered KPI catalog from the baseline export."""

    baseline_frame = pd.read_csv(Path(path).expanduser().resolve())
    _validate_columns(baseline_frame, REQUIRED_BASELINE_COLUMNS, "baseline KPI export")
    ordered_kpis = (
        baseline_frame[["kpi_order", "kpi"]]
        .drop_duplicates()
        .sort_values("kpi_order")
    )
    if ordered_kpis["kpi"].duplicated().any():
        raise PolicyImpactMatrixError("The baseline KPI export contains duplicate KPI names.")
    return ordered_kpis["kpi"].tolist()


def load_recommendation_mapping(path: str | Path) -> pd.DataFrame:
    """Load the long-form recommendation-to-KPI mapping."""

    mapping = pd.read_csv(Path(path).expanduser().resolve())
    _validate_columns(mapping, REQUIRED_MAPPING_COLUMNS, "recommendation mapping")
    mapping = mapping.copy()
    mapping["effect_strength"] = pd.to_numeric(mapping["effect_strength"], errors="raise").astype(int)
    mapping["row_order"] = range(len(mapping))
    return mapping


def load_effect_calibration(path: str | Path) -> pd.DataFrame:
    """Load effect calibration rows keyed by calibration lever id."""

    calibration = pd.read_csv(Path(path).expanduser().resolve())
    _validate_columns(calibration, REQUIRED_EFFECT_COLUMNS, "effect calibration")
    return calibration


def load_lag_calibration(path: str | Path) -> pd.DataFrame:
    """Load lag calibration rows keyed by calibration lever id."""

    calibration = pd.read_csv(Path(path).expanduser().resolve())
    _validate_columns(calibration, REQUIRED_LAG_COLUMNS, "lag calibration")
    numeric_columns = ["lag_quarters_low", "lag_quarters_base", "lag_quarters_high"]
    for column_name in numeric_columns:
        calibration[column_name] = pd.to_numeric(calibration[column_name], errors="raise").astype(int)
    return calibration


def build_policy_impact_metadata(
    mapping: pd.DataFrame,
    baseline_kpis: list[str],
    effect_calibration: pd.DataFrame,
    lag_calibration: pd.DataFrame,
) -> pd.DataFrame:
    """Build the enriched long-form metadata table used by the simulator."""

    baseline_kpi_set = set(baseline_kpis)
    metadata_rows: list[dict[str, object]] = []

    for mapping_row in mapping.to_dict("records"):
        recommendation_name = str(mapping_row["recommendation"]).strip()
        lever_name = str(mapping_row["lever"]).strip()
        kpi_name = str(mapping_row["KPI"]).strip()
        lag_class = str(mapping_row["lag_class"]).strip().lower()
        directness = str(mapping_row["directness"]).strip()

        if kpi_name not in baseline_kpi_set:
            raise PolicyImpactMatrixError(
                f"Recommendation mapping KPI '{kpi_name}' does not exist in the baseline KPI catalog."
            )

        recommendation_id = map_recommendation_name_to_id(recommendation_name)
        lever_config = get_lever_config(lever_name)
        effect_archetype = choose_effect_archetype(
            recommendation_id=recommendation_id,
            lever_name=lever_name,
            kpi_name=kpi_name,
            lever_config=lever_config,
        )
        lag_archetype = choose_lag_archetype(
            recommendation_id=recommendation_id,
            lever_name=lever_name,
            kpi_name=kpi_name,
            lever_config=lever_config,
        )

        effect_row = get_single_calibration_row(
            calibration=effect_calibration,
            lever_id=effect_archetype,
            calibration_name="effect calibration",
        )
        lag_row = get_single_calibration_row(
            calibration=lag_calibration,
            lever_id=lag_archetype,
            calibration_name="lag calibration",
        )

        coefficient_payload = strength_to_numeric_coefficient(
            effect_strength=int(mapping_row["effect_strength"]),
            effect_row=effect_row,
        )
        lag_quarters = lag_class_to_quarters(lag_class=lag_class, lag_row=lag_row)

        metadata_rows.append(
            {
                "recommendation_id": recommendation_id,
                "recommendation_name": recommendation_name,
                "lever_id": lever_config["lever_id"],
                "lever_name": lever_name,
                "KPI": kpi_name,
                "effect_strength": int(mapping_row["effect_strength"]),
                "numeric_coefficient": coefficient_payload["numeric_coefficient"],
                "coefficient_scale": COEFFICIENT_SCALE,
                "lag_class": lag_class,
                "lag_quarters": lag_quarters,
                "ramp_type": lag_row["ramp_type"],
                "directness": directness,
                "rationale": mapping_row["rationale"],
                "calibration_effect_lever_id": effect_archetype,
                "calibration_lag_lever_id": lag_archetype,
                "calibration_anchor_scenario": coefficient_payload["anchor_scenario"],
                "calibration_anchor_value": coefficient_payload["anchor_value"],
                "calibration_effect_direction": effect_row["effect_direction"],
                "calibration_confidence": effect_row["confidence"],
                "calibration_mapping_note": lever_config["mapping_note"],
                "row_order": int(mapping_row["row_order"]),
            }
        )

    metadata = pd.DataFrame(metadata_rows).sort_values("row_order").reset_index(drop=True)
    validate_simulation_kpis(metadata=metadata, baseline_kpis=baseline_kpis)
    if metadata.duplicated(subset=["lever_name", "KPI"]).any():
        duplicates = metadata.loc[
            metadata.duplicated(subset=["lever_name", "KPI"], keep=False),
            ["lever_name", "KPI"],
        ]
        raise PolicyImpactMatrixError(
            "Duplicate lever/KPI combinations were detected:\n"
            f"{duplicates.to_string(index=False)}"
        )
    return metadata


def build_policy_impact_matrix(metadata: pd.DataFrame, baseline_kpis: list[str]) -> pd.DataFrame:
    """Pivot the long metadata into a wide lever-by-KPI impact matrix."""

    lever_order = metadata.drop_duplicates("lever_name")["lever_name"].tolist()
    matrix = (
        metadata.pivot(index="lever_name", columns="KPI", values="numeric_coefficient")
        .reindex(index=lever_order, columns=baseline_kpis, fill_value=0.0)
        .fillna(0.0)
    )
    matrix.index.name = "lever_name"
    return matrix


def validate_simulation_kpis(metadata: pd.DataFrame, baseline_kpis: list[str]) -> None:
    """Ensure every simulated KPI exists in the baseline dataset."""

    missing_kpis = sorted(set(metadata["KPI"]) - set(baseline_kpis))
    if missing_kpis:
        raise PolicyImpactMatrixError(
            f"Simulation KPIs are missing from the baseline dataset: {missing_kpis}"
        )


def export_policy_impact_outputs(
    metadata: pd.DataFrame,
    matrix: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    """Write the long metadata table and the wide impact matrix to disk."""

    output_dir.mkdir(parents=True, exist_ok=True)
    export_paths = {
        "impact_matrix": output_dir / "impact_matrix.csv",
        "impact_matrix_long": output_dir / "impact_matrix_long.csv",
    }

    matrix.to_csv(export_paths["impact_matrix"])
    metadata.drop(columns=["row_order"]).to_csv(export_paths["impact_matrix_long"], index=False)
    return export_paths


def map_recommendation_name_to_id(recommendation_name: str) -> str:
    """Convert recommendation names into stable recommendation ids."""

    recommendation_key = normalize_text(recommendation_name)
    try:
        return RECOMMENDATION_ID_BY_KEY[recommendation_key]
    except KeyError as exc:
        raise PolicyImpactMatrixError(
            f"Unknown recommendation name '{recommendation_name}'."
        ) from exc


def get_lever_config(lever_name: str) -> dict[str, str]:
    """Return the configuration for one detailed policy lever."""

    lever_key = normalize_text(lever_name)
    try:
        return LEVER_CONFIG_BY_KEY[lever_key]
    except KeyError as exc:
        raise PolicyImpactMatrixError(f"Unknown policy lever '{lever_name}'.") from exc


def choose_effect_archetype(
    recommendation_id: str,
    lever_name: str,
    kpi_name: str,
    lever_config: dict[str, str],
) -> str:
    """Choose the effect-calibration archetype for one lever/KPI row."""

    lever_key = normalize_text(lever_name)

    if lever_key == "computeutilizationsubsidyfordomesticaifirms":
        if kpi_name in RESEARCH_DEVELOPMENT_KPIS:
            return "rec2_lever2"
        return "rec2_lever1"

    if lever_key == "growthstagecoinvestmentandlaterstagescaleupcapital":
        if kpi_name in {"AI Patent Grants (per 100k)", "Tortoise Development Score"}:
            return "rec2_lever2"
        return "rec2_lever1"

    if lever_key == "3040refundablefirstcustomeraiadoptiontaxcredit":
        if kpi_name == "AI Adoption (%)":
            return "rec3_lever1"
        return "rec3_lever2"

    if lever_key == "federalprocurementchallengeandpilottocontractconversionprogram":
        return "rec3_lever2"

    if recommendation_id == "rec2" and kpi_name in RESEARCH_DEVELOPMENT_KPIS:
        return "rec2_lever2"

    return lever_config["default_effect_archetype"]


def choose_lag_archetype(
    recommendation_id: str,
    lever_name: str,
    kpi_name: str,
    lever_config: dict[str, str],
) -> str:
    """Choose the lag-calibration archetype for one lever/KPI row."""

    lever_key = normalize_text(lever_name)

    if lever_key == "computeutilizationsubsidyfordomesticaifirms":
        if kpi_name in {"Tortoise Research Score", "Tortoise Development Score", "Notable AI Models"}:
            return "rec2_lever2"
        return "rec2_lever1"

    if lever_key == "growthstagecoinvestmentandlaterstagescaleupcapital":
        if kpi_name in {"AI Patent Grants (per 100k)", "Tortoise Development Score"}:
            return "rec2_lever2"
        return "rec2_lever1"

    if lever_key == "federalprocurementchallengeandpilottocontractconversionprogram":
        return "rec3_lever2"

    if recommendation_id == "rec2" and kpi_name in {"AI Patent Grants (per 100k)", "Tortoise Development Score"}:
        return "rec2_lever2"

    return lever_config["default_lag_archetype"]


def get_single_calibration_row(
    calibration: pd.DataFrame,
    lever_id: str,
    calibration_name: str,
) -> pd.Series:
    """Fetch exactly one calibration row by lever id."""

    matches = calibration.loc[calibration["lever_id"] == lever_id]
    if len(matches) != 1:
        raise PolicyImpactMatrixError(
            f"Expected exactly one row in {calibration_name} for '{lever_id}', found {len(matches)}."
        )
    return matches.iloc[0]


def strength_to_numeric_coefficient(effect_strength: int, effect_row: pd.Series) -> dict[str, object]:
    """Convert a 0/1/2/3 strength into a bounded numeric coefficient."""

    if effect_strength not in STRENGTH_BASE_COEFFICIENTS:
        raise PolicyImpactMatrixError(f"Unsupported effect strength '{effect_strength}'.")

    if effect_strength == 0:
        return {
            "numeric_coefficient": 0.0,
            "anchor_scenario": "none",
            "anchor_value": 0.0,
        }

    anchor_text, anchor_scenario = select_effect_anchor_text(effect_row, effect_strength)
    anchor_value = parse_anchor_value(anchor_text)
    confidence_factor = confidence_to_factor(str(effect_row["confidence"]))
    direction_sign = -1.0 if str(effect_row["effect_direction"]).strip().lower() == "negative" else 1.0

    if anchor_value is None:
        anchor_multiplier = 1.0
        bounded_anchor_value = 0.5
    else:
        bounded_anchor_value = min(max(anchor_value, 0.0), 1.0)
        anchor_multiplier = 0.75 + (0.75 * bounded_anchor_value)

    numeric_coefficient = (
        STRENGTH_BASE_COEFFICIENTS[effect_strength]
        * anchor_multiplier
        * confidence_factor
        * direction_sign
    )
    return {
        "numeric_coefficient": round(float(numeric_coefficient), 6),
        "anchor_scenario": anchor_scenario,
        "anchor_value": round(float(bounded_anchor_value), 6),
    }


def select_effect_anchor_text(effect_row: pd.Series, effect_strength: int) -> tuple[str, str]:
    """Select the low/base/high calibration anchor text for a strength bucket."""

    scenario_order = {
        1: ["effect_low", "effect_base", "effect_high"],
        2: ["effect_base", "effect_low", "effect_high"],
        3: ["effect_high", "effect_base", "effect_low"],
    }[effect_strength]

    for column_name in scenario_order:
        candidate_text = str(effect_row.get(column_name, "")).strip()
        if candidate_text and candidate_text.lower() != "nan":
            return candidate_text, column_name.removeprefix("effect_")

    raise PolicyImpactMatrixError(
        f"No effect-calibration text is available for lever '{effect_row['lever_id']}'."
    )


def lag_class_to_quarters(lag_class: str, lag_row: pd.Series) -> int:
    """Convert immediate/medium/long classes into numeric quarter lags."""

    lag_lookup = {
        "immediate": "lag_quarters_low",
        "medium": "lag_quarters_base",
        "long": "lag_quarters_high",
    }
    try:
        lag_column = lag_lookup[lag_class]
    except KeyError as exc:
        raise PolicyImpactMatrixError(f"Unknown lag class '{lag_class}'.") from exc

    return int(lag_row[lag_column])


def parse_anchor_value(anchor_text: str) -> float | None:
    """Parse a calibration anchor string into a bounded 0-1 magnitude."""

    if not anchor_text:
        return None

    normalized_text = str(anchor_text).strip().lower()
    if not normalized_text or "not directly estimated" in normalized_text:
        return None

    att_matches = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*att", normalized_text)]
    if att_matches:
        return min(max(att_matches), 1.0)

    percent_matches = [float(value) / 100.0 for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", normalized_text)]
    if percent_matches:
        if "associated with" in normalized_text:
            return min(percent_matches[-1], 1.0)
        if "versus" in normalized_text or "vs" in normalized_text:
            if len(percent_matches) >= 2:
                return min(abs(percent_matches[0] - percent_matches[1]), 1.0)
        return min(max(percent_matches), 1.0)

    ratio_matches = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*x", normalized_text)]
    if ratio_matches:
        ratio_value = max(ratio_matches)
        return min(max((ratio_value - 1.0) / 2.0, 0.0), 1.0)

    decimal_matches = [
        float(value)
        for value in re.findall(r"(?<![\d,])(\d+\.\d+)(?!\d)", normalized_text)
    ]
    bounded_matches = [value for value in decimal_matches if 0.0 <= value <= 1.0]
    if bounded_matches:
        return min(max(bounded_matches), 1.0)
    return None


def confidence_to_factor(confidence: str) -> float:
    """Map textual confidence labels to conservative scaling factors."""

    normalized_confidence = str(confidence).strip().lower()
    return CONFIDENCE_FACTORS.get(normalized_confidence, 0.90)


def normalize_text(value: object) -> str:
    """Normalize free-text labels for robust dictionary lookups."""

    return "".join(character.lower() for character in str(value) if character.isalnum())


def _validate_columns(frame: pd.DataFrame, required_columns: list[str], frame_name: str) -> None:
    missing_columns = sorted(set(required_columns) - set(frame.columns))
    if missing_columns:
        raise PolicyImpactMatrixError(
            f"{frame_name} is missing required columns: {missing_columns}"
        )


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the policy impact-matrix generator."""

    parser = argparse.ArgumentParser(
        description="Build wide and long policy-impact matrices for the AI competitiveness simulation."
    )
    parser.add_argument(
        "--baseline-kpis",
        default=str(DEFAULT_BASELINE_KPI_PATH),
        help="Path to baseline_kpi_scores.csv.",
    )
    parser.add_argument(
        "--mapping",
        default=str(DEFAULT_IMPACT_MAPPING_PATH),
        help="Path to the long recommendation-to-KPI mapping CSV.",
    )
    parser.add_argument(
        "--calibration-effects",
        default=str(DEFAULT_EFFECT_CALIBRATION_PATH),
        help="Path to calibration_effects.csv.",
    )
    parser.add_argument(
        "--calibration-lags",
        default=str(DEFAULT_LAG_CALIBRATION_PATH),
        help="Path to calibration_lags.csv.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where impact_matrix.csv and impact_matrix_long.csv will be written.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for building impact-matrix artifacts."""

    parser = build_argument_parser()
    args = parser.parse_args()
    result = build_policy_impact_artifacts(
        baseline_kpi_path=args.baseline_kpis,
        recommendation_mapping_path=args.mapping,
        calibration_effects_path=args.calibration_effects,
        calibration_lags_path=args.calibration_lags,
        output_dir=args.output_dir,
    )
    for export_name, export_path in result.export_paths.items():
        print(f"{export_name}: {export_path}")


if __name__ == "__main__":
    main()
