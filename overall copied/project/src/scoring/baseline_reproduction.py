"""Baseline reproduction pipeline for the AI competitiveness workbook."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import math

import pandas as pd

from src.io import (
    load_tabular_data,
    load_xlsx_sheets,
    map_required_sheet_names,
    normalize_sheet_name,
    validate_required_columns,
)


EXPECTED_WORKBOOK_SHEETS = [
    "KPI Scores and Weights",
    "Final Rankings",
]
EXPECTED_COUNTRY_COUNT = 13
EXPECTED_KPI_COUNT = 26
DEFAULT_OUTPUT_DIR = Path("outputs") / "tables"

SUBPILLAR_NAME_MAP = {
    "Commercial": "Commercial Ecosystem",
    "Gov. Strategy": "Government Strategy",
    "Operating Env": "Operating Environment",
}
PILLAR_NAME_MAP = {
    "Implementation": "Implementation",
    "Innovation": "Innovation",
    "Investment": "Investment",
}
SUBPILLAR_ORDER = [
    "Talent",
    "Infrastructure",
    "Operating Environment",
    "Research",
    "Development",
    "Commercial Ecosystem",
    "Government Strategy",
]
PILLAR_ORDER = ["Implementation", "Innovation", "Investment"]
EXPECTED_L1_WEIGHTS = {
    "Talent": 0.2456,
    "Infrastructure": 0.0870,
    "Operating Environment": 0.0424,
    "Research": 0.2136,
    "Development": 0.1655,
    "Commercial Ecosystem": 0.1930,
    "Government Strategy": 0.0529,
}
EXPECTED_PILLAR_WEIGHTS = {
    "Implementation": 0.3751,
    "Innovation": 0.3790,
    "Investment": 0.2459,
}
EXPECTED_L2_WEIGHTS = {
    "Talent": {
        "Tortoise Talent Score": 0.3110,
        "Relative AI Skill Penetration": 0.1439,
        "AI Hiring Rate YoY Ratio": 0.1749,
        "AI Talent Concentration": 0.1023,
        "AI Job Postings (% of Total)": 0.1430,
        "Net Migration Flow of AI Skills": 0.1249,
    },
    "Infrastructure": {
        "Tortoise Infrastructure Score": 0.3888,
        "Compute Hardware Index": 0.2964,
        "Parts Semiconductor Devices Exports": 0.1237,
        "Internet Speed": 0.0841,
        "Energy Resilience Score": 0.1070,
    },
    "Operating Environment": {
        "Tortoise Operating Environment Score": 0.5168,
        "AI Social Media Sentiment": 0.1283,
        "Conference Submissions on RAI Topics": 0.1618,
        "Open Data Score": 0.1931,
    },
    "Research": {
        "Tortoise Research Score": 0.4033,
        "AI Publications (Total)": 0.1956,
        "AI Citations (% of World Total)": 0.1956,
        "Notable AI Models": 0.1331,
        "Academia-Industry Concentration": 0.0723,
    },
    "Development": {
        "Tortoise Development Score": 0.6000,
        "AI Patent Grants (per 100k)": 0.4000,
    },
    "Commercial Ecosystem": {
        "Tortoise Commercial Score": 0.5390,
        "AI Investment Activity": 0.2973,
        "AI Adoption (%)": 0.1638,
    },
    "Government Strategy": {
        "Tortoise Government Strategy Score": 1.0000,
    },
}
CANADA_SUBPILLAR_TARGETS = {
    "Talent": 41.94,
    "Infrastructure": 40.92,
    "Operating Environment": 69.82,
    "Research": 28.82,
    "Development": 15.80,
    "Commercial Ecosystem": 10.27,
    "Government Strategy": 100.00,
}
CANADA_PILLAR_TARGETS = {
    "Implementation": 44.8557,
    "Innovation": 23.1360,
    "Investment": 29.5734,
}
CANADA_KPI_SPOT_CHECKS = {
    "Tortoise Talent Score": 31.28,
    "AI Hiring Rate YoY Ratio": 73.73,
    "Net Migration Flow of AI Skills": 48.96,
    "Tortoise Infrastructure Score": 77.05,
    "Compute Hardware Index": 3.61,
    "Energy Resilience Score": 86.16,
    "Tortoise Operating Environment Score": 93.94,
    "Open Data Score": 92.86,
    "Tortoise Research Score": 30.67,
    "AI Publications (Total)": 34.73,
    "AI Citations (% of World Total)": 10.72,
    "Notable AI Models": 2.50,
    "Tortoise Development Score": 25.78,
    "AI Patent Grants (per 100k)": 0.83,
    "Tortoise Commercial Score": 14.88,
    "AI Investment Activity": 3.16,
    "AI Adoption (%)": 8.00,
    "Tortoise Government Strategy Score": 100.00,
}
FINAL_RANKING_COLUMNS = [
    "Rank",
    "Country",
    "Composite Score",
    "Talent Score",
    "Infrastructure Score",
    "Operating Env Score",
    "Research Score",
    "Development Score",
    "Commercial Score",
    "Gov Strategy Score",
    "Talent Weight",
    "Infrastructure Weight",
    "OpEnv Weight",
    "Research Weight",
    "Development Weight",
    "Commercial Weight",
    "GovStrategy Weight",
    "Implementation Weight",
    "Innovation Weight",
    "Investment Weight",
]


class BaselineReproductionError(ValueError):
    """Raised when baseline inputs cannot be reproduced deterministically."""


@dataclass(slots=True)
class BaselineReproductionResult:
    """Full baseline reproduction payload for notebook and script use."""

    workbook_path: Path
    canada_gap_path: Path
    workbook_sheet_map: dict[str, str]
    kpi_metadata: pd.DataFrame
    kpi_scores: pd.DataFrame
    subpillar_scores: pd.DataFrame
    country_scores: pd.DataFrame
    final_rankings: pd.DataFrame
    canada_gap: pd.DataFrame
    validation_checks: pd.DataFrame
    export_paths: dict[str, Path] = field(default_factory=dict)


def reproduce_baseline(
    workbook_path: str | Path,
    canada_gap_csv_path: str | Path,
    output_dir: str | Path | None = None,
) -> BaselineReproductionResult:
    """Load, recompute, validate, and export the current baseline."""

    resolved_workbook_path = Path(workbook_path).expanduser().resolve()
    resolved_canada_gap_path = Path(canada_gap_csv_path).expanduser().resolve()
    resolved_output_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir is not None
        else (Path.cwd() / DEFAULT_OUTPUT_DIR).resolve()
    )

    workbook_sheets = load_xlsx_sheets(resolved_workbook_path)
    workbook_sheet_map = map_required_sheet_names(
        available_sheet_names=list(workbook_sheets.keys()),
        required_sheet_names=EXPECTED_WORKBOOK_SHEETS,
    )

    kpi_sheet = workbook_sheets[workbook_sheet_map["KPI Scores and Weights"]].frame
    final_sheet = workbook_sheets[workbook_sheet_map["Final Rankings"]].frame

    kpi_metadata, kpi_scores = parse_kpi_sheet(kpi_sheet)
    final_rankings = parse_final_rankings_sheet(final_sheet)
    canada_gap = load_canada_gap_csv(resolved_canada_gap_path)

    validate_canada_gap_alignment(kpi_metadata, canada_gap)

    subpillar_scores = compute_subpillar_scores(kpi_scores)
    country_scores = compute_country_scores(subpillar_scores, final_rankings)
    validation_checks = build_validation_checks(
        workbook_sheet_map=workbook_sheet_map,
        kpi_metadata=kpi_metadata,
        kpi_scores=kpi_scores,
        subpillar_scores=subpillar_scores,
        country_scores=country_scores,
        final_rankings=final_rankings,
        canada_gap=canada_gap,
    )

    if not validation_checks["passed"].all():
        failed_checks = validation_checks.loc[~validation_checks["passed"], "check"].tolist()
        raise BaselineReproductionError(
            "Baseline reproduction validation failed for: "
            f"{', '.join(failed_checks)}"
        )

    report_text = render_validation_report(
        workbook_path=resolved_workbook_path,
        canada_gap_path=resolved_canada_gap_path,
        workbook_sheet_map=workbook_sheet_map,
        kpi_metadata=kpi_metadata,
        country_scores=country_scores,
        canada_gap=canada_gap,
        validation_checks=validation_checks,
    )

    export_paths = export_baseline_outputs(
        country_scores=country_scores,
        kpi_scores=kpi_scores,
        report_text=report_text,
        output_dir=resolved_output_dir,
    )

    return BaselineReproductionResult(
        workbook_path=resolved_workbook_path,
        canada_gap_path=resolved_canada_gap_path,
        workbook_sheet_map=workbook_sheet_map,
        kpi_metadata=kpi_metadata,
        kpi_scores=kpi_scores,
        subpillar_scores=subpillar_scores,
        country_scores=country_scores,
        final_rankings=final_rankings,
        canada_gap=canada_gap,
        validation_checks=validation_checks,
        export_paths=export_paths,
    )


def parse_kpi_sheet(sheet_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse the workbook's wide KPI sheet into metadata and a long score table."""

    if sheet_frame.empty:
        raise BaselineReproductionError("The KPI Scores and Weights sheet is empty.")
    if sheet_frame.shape[0] < 8 or sheet_frame.shape[1] < 2:
        raise BaselineReproductionError(
            "The KPI Scores and Weights sheet is too small to contain metadata rows."
        )

    _validate_kpi_sheet_row_labels(sheet_frame)

    kpi_columns = [
        column_index
        for column_index in range(1, sheet_frame.shape[1])
        if _as_text(sheet_frame.iat[4, column_index])
    ]
    if len(kpi_columns) != EXPECTED_KPI_COUNT:
        raise BaselineReproductionError(
            f"Expected {EXPECTED_KPI_COUNT} KPI columns, found {len(kpi_columns)}."
        )

    country_row_indexes = [
        row_index
        for row_index in range(7, sheet_frame.shape[0])
        if _as_text(sheet_frame.iat[row_index, 0])
    ]
    if len(country_row_indexes) != EXPECTED_COUNTRY_COUNT:
        raise BaselineReproductionError(
            f"Expected {EXPECTED_COUNTRY_COUNT} countries, found "
            f"{len(country_row_indexes)} in the KPI sheet."
        )

    metadata_records: list[dict[str, object]] = []
    current_pillar = ""
    current_subpillar = ""
    current_subpillar_weight: float | None = None

    for kpi_order, column_index in enumerate(kpi_columns, start=1):
        pillar_cell = _as_text(sheet_frame.iat[0, column_index])
        if pillar_cell:
            current_pillar = canonicalize_pillar_name(pillar_cell)

        subpillar_cell = _as_text(sheet_frame.iat[1, column_index])
        if subpillar_cell:
            current_subpillar = canonicalize_subpillar_name(subpillar_cell)

        subpillar_weight_cell = sheet_frame.iat[2, column_index]
        if _as_text(subpillar_weight_cell):
            current_subpillar_weight = parse_percent(subpillar_weight_cell)

        if not current_pillar or not current_subpillar or current_subpillar_weight is None:
            raise BaselineReproductionError(
                "Unable to map pillar, sub-pillar, and weight metadata to KPI column "
                f"{column_index + 1}."
            )

        kpi_name = _as_text(sheet_frame.iat[4, column_index])
        source_name = _as_text(sheet_frame.iat[3, column_index])
        scale_label = _as_text(sheet_frame.iat[6, column_index])
        kpi_weight = parse_percent(sheet_frame.iat[5, column_index])

        if not source_name or not scale_label:
            raise BaselineReproductionError(
                f"KPI column '{kpi_name}' is missing source or scale metadata."
            )

        metadata_records.append(
            {
                "kpi_order": kpi_order,
                "column_index": column_index,
                "pillar": current_pillar,
                "subpillar": current_subpillar,
                "subpillar_weight": current_subpillar_weight,
                "source": source_name,
                "kpi": kpi_name,
                "kpi_weight": kpi_weight,
                "scale": scale_label,
                "final_weight_display": current_subpillar_weight * kpi_weight,
            }
        )

    kpi_metadata = pd.DataFrame(metadata_records).sort_values("kpi_order").reset_index(drop=True)
    validate_kpi_weight_structure(kpi_metadata)

    kpi_score_records: list[dict[str, object]] = []
    for country_row_index in country_row_indexes:
        country_name = _as_text(sheet_frame.iat[country_row_index, 0])
        for metadata_row in kpi_metadata.to_dict("records"):
            score_value = sheet_frame.iat[country_row_index, int(metadata_row["column_index"])]
            if score_value is None or _as_text(score_value) == "":
                raise BaselineReproductionError(
                    f"Country '{country_name}' is missing a score for KPI "
                    f"'{metadata_row['kpi']}'."
                )

            kpi_score = parse_float(score_value)
            kpi_score_records.append(
                {
                    "country": country_name,
                    "kpi_order": int(metadata_row["kpi_order"]),
                    "pillar": metadata_row["pillar"],
                    "subpillar": metadata_row["subpillar"],
                    "subpillar_weight": float(metadata_row["subpillar_weight"]),
                    "source": metadata_row["source"],
                    "kpi": metadata_row["kpi"],
                    "kpi_weight": float(metadata_row["kpi_weight"]),
                    "final_weight_display": float(metadata_row["final_weight_display"]),
                    "scale": metadata_row["scale"],
                    "kpi_score": kpi_score,
                    "weighted_kpi_score": kpi_score * float(metadata_row["kpi_weight"]),
                }
            )

    kpi_scores = pd.DataFrame(kpi_score_records)
    return kpi_metadata, kpi_scores


def parse_final_rankings_sheet(sheet_frame: pd.DataFrame) -> pd.DataFrame:
    """Parse the workbook's final rankings sheet into typed columns."""

    if sheet_frame.empty:
        raise BaselineReproductionError("The Final Rankings sheet is empty.")

    headers = [_as_text(value) for value in sheet_frame.iloc[0].tolist()]
    if headers[: len(FINAL_RANKING_COLUMNS)] != FINAL_RANKING_COLUMNS:
        raise BaselineReproductionError(
            "The Final Rankings sheet header does not match the expected schema."
        )

    row_records: list[dict[str, object]] = []
    for row_index in range(1, sheet_frame.shape[0]):
        country_name = _as_text(sheet_frame.iat[row_index, 1])
        if not country_name:
            continue

        row_data = {
            header: sheet_frame.iat[row_index, column_index]
            for column_index, header in enumerate(headers)
            if header
        }
        row_records.append(row_data)

    final_rankings = pd.DataFrame(row_records)
    validate_required_columns(final_rankings, FINAL_RANKING_COLUMNS, "Final Rankings sheet")

    rename_map = {
        "Rank": "workbook_rank",
        "Country": "country",
        "Composite Score": "workbook_composite_score",
        "Talent Score": "talent_score_workbook",
        "Infrastructure Score": "infrastructure_score_workbook",
        "Operating Env Score": "operating_environment_score_workbook",
        "Research Score": "research_score_workbook",
        "Development Score": "development_score_workbook",
        "Commercial Score": "commercial_ecosystem_score_workbook",
        "Gov Strategy Score": "government_strategy_score_workbook",
        "Talent Weight": "talent_weight_display",
        "Infrastructure Weight": "infrastructure_weight_display",
        "OpEnv Weight": "operating_environment_weight_display",
        "Research Weight": "research_weight_display",
        "Development Weight": "development_weight_display",
        "Commercial Weight": "commercial_ecosystem_weight_display",
        "GovStrategy Weight": "government_strategy_weight_display",
        "Implementation Weight": "implementation_weight_display",
        "Innovation Weight": "innovation_weight_display",
        "Investment Weight": "investment_weight_display",
    }
    final_rankings = final_rankings.rename(columns=rename_map)

    numeric_columns = [
        "workbook_rank",
        "workbook_composite_score",
        "talent_score_workbook",
        "infrastructure_score_workbook",
        "operating_environment_score_workbook",
        "research_score_workbook",
        "development_score_workbook",
        "commercial_ecosystem_score_workbook",
        "government_strategy_score_workbook",
    ]
    for numeric_column in numeric_columns:
        final_rankings[numeric_column] = pd.to_numeric(
            final_rankings[numeric_column],
            errors="raise",
        )

    percent_columns = [
        "talent_weight_display",
        "infrastructure_weight_display",
        "operating_environment_weight_display",
        "research_weight_display",
        "development_weight_display",
        "commercial_ecosystem_weight_display",
        "government_strategy_weight_display",
        "implementation_weight_display",
        "innovation_weight_display",
        "investment_weight_display",
    ]
    for percent_column in percent_columns:
        final_rankings[percent_column] = final_rankings[percent_column].map(parse_percent)

    if len(final_rankings) != EXPECTED_COUNTRY_COUNT:
        raise BaselineReproductionError(
            f"Expected {EXPECTED_COUNTRY_COUNT} rows in Final Rankings, found "
            f"{len(final_rankings)}."
        )

    return final_rankings.sort_values("workbook_rank").reset_index(drop=True)


def load_canada_gap_csv(path: str | Path) -> pd.DataFrame:
    """Load and type the Canada gap CSV used for precision cross-checks."""

    canada_gap = load_tabular_data(path)
    validate_required_columns(
        canada_gap,
        [
            "Country",
            "Canada_Overall_Rank",
            "Canada_Composite_Score",
            "Pillar",
            "Pillar_Weightage",
            "Pillar_Canada_Score",
            "Subpillar",
            "Subpillar_Weightage",
            "Subpillar_Share_of_Pillar",
            "Subpillar_Canada_Score",
            "KPI_Order",
            "KPI",
            "Source",
            "KPI_Weight_Within_Subpillar",
            "Final_KPI_Weightage",
            "Scale",
            "Canada_KPI_Score",
        ],
        "Canada gap CSV",
    )

    canada_gap = canada_gap.rename(
        columns={
            "Country": "country",
            "Canada_Overall_Rank": "canada_overall_rank",
            "Canada_Composite_Score": "canada_composite_score",
            "Pillar": "pillar",
            "Pillar_Weightage": "pillar_weight",
            "Pillar_Canada_Score": "pillar_canada_score",
            "Subpillar": "subpillar",
            "Subpillar_Weightage": "subpillar_weight",
            "Subpillar_Share_of_Pillar": "subpillar_share_of_pillar",
            "Subpillar_Canada_Score": "subpillar_canada_score",
            "KPI_Order": "kpi_order",
            "KPI": "kpi",
            "Source": "source",
            "KPI_Weight_Within_Subpillar": "kpi_weight",
            "Final_KPI_Weightage": "final_kpi_weightage",
            "Scale": "scale",
            "Canada_KPI_Score": "canada_kpi_score",
        }
    )

    canada_gap["pillar"] = canada_gap["pillar"].map(canonicalize_pillar_name)
    canada_gap["subpillar"] = canada_gap["subpillar"].map(canonicalize_subpillar_name)

    numeric_columns = [
        "canada_overall_rank",
        "canada_composite_score",
        "pillar_weight",
        "pillar_canada_score",
        "subpillar_weight",
        "subpillar_share_of_pillar",
        "subpillar_canada_score",
        "kpi_order",
        "kpi_weight",
        "final_kpi_weightage",
        "canada_kpi_score",
    ]
    for numeric_column in numeric_columns:
        canada_gap[numeric_column] = pd.to_numeric(canada_gap[numeric_column], errors="raise")

    canada_gap = canada_gap.sort_values(["kpi_order", "kpi"]).reset_index(drop=True)
    if canada_gap["country"].nunique() != 1 or canada_gap["country"].iloc[0] != "Canada":
        raise BaselineReproductionError(
            "The Canada gap CSV is expected to contain exactly one country: Canada."
        )

    return canada_gap


def validate_canada_gap_alignment(
    kpi_metadata: pd.DataFrame,
    canada_gap: pd.DataFrame,
) -> None:
    """Ensure the Canada gap CSV aligns with the workbook KPI metadata."""

    canada_gap_kpis = (
        canada_gap[
            [
                "kpi_order",
                "pillar",
                "subpillar",
                "subpillar_weight",
                "kpi",
                "source",
                "kpi_weight",
                "final_kpi_weightage",
                "scale",
            ]
        ]
        .drop_duplicates()
        .sort_values("kpi_order")
        .reset_index(drop=True)
    )

    if len(canada_gap_kpis) != EXPECTED_KPI_COUNT:
        raise BaselineReproductionError(
            "The Canada gap CSV does not contain the expected 26 unique KPI rows."
        )

    workbook_kpis = (
        kpi_metadata[
            [
                "kpi_order",
                "pillar",
                "subpillar",
                "subpillar_weight",
                "kpi",
                "source",
                "kpi_weight",
                "final_weight_display",
                "scale",
            ]
        ]
        .rename(columns={"final_weight_display": "final_kpi_weightage"})
        .reset_index(drop=True)
    )

    text_columns = ["pillar", "subpillar", "kpi", "source", "scale"]
    for text_column in text_columns:
        if workbook_kpis[text_column].tolist() != canada_gap_kpis[text_column].tolist():
            raise BaselineReproductionError(
                f"Workbook metadata does not align with the Canada gap CSV for column "
                f"'{text_column}'."
            )

    numeric_columns = [
        "kpi_order",
        "subpillar_weight",
        "kpi_weight",
        "final_kpi_weightage",
    ]
    for numeric_column in numeric_columns:
        for workbook_value, canada_gap_value in zip(
            workbook_kpis[numeric_column],
            canada_gap_kpis[numeric_column],
        ):
            if not math.isclose(
                float(workbook_value),
                float(canada_gap_value),
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                raise BaselineReproductionError(
                    f"Workbook metadata does not align with the Canada gap CSV for "
                    f"'{numeric_column}'."
                )


def validate_kpi_weight_structure(kpi_metadata: pd.DataFrame) -> None:
    """Validate KPI counts and weight totals before scoring."""

    if len(kpi_metadata) != EXPECTED_KPI_COUNT:
        raise BaselineReproductionError(
            f"Expected {EXPECTED_KPI_COUNT} KPI definitions, found {len(kpi_metadata)}."
        )

    l1_weights = (
        kpi_metadata[["subpillar", "subpillar_weight"]]
        .drop_duplicates()
        .set_index("subpillar")["subpillar_weight"]
        .to_dict()
    )
    if set(l1_weights) != set(SUBPILLAR_ORDER):
        raise BaselineReproductionError(
            f"Detected sub-pillars {sorted(l1_weights)} do not match the expected set "
            f"{SUBPILLAR_ORDER}."
        )

    for subpillar_name, expected_weight in EXPECTED_L1_WEIGHTS.items():
        actual_weight = l1_weights[subpillar_name]
        if not math.isclose(actual_weight, expected_weight, rel_tol=0.0, abs_tol=1e-9):
            raise BaselineReproductionError(
                f"Unexpected L1 weight for sub-pillar '{subpillar_name}': "
                f"{actual_weight}."
            )

    if not math.isclose(sum(l1_weights.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise BaselineReproductionError("The Level 1 weights do not sum to 1.0.")

    for subpillar_name, expected_block in EXPECTED_L2_WEIGHTS.items():
        subpillar_block = (
            kpi_metadata.loc[kpi_metadata["subpillar"] == subpillar_name]
            .sort_values("kpi_order")
            .set_index("kpi")["kpi_weight"]
            .to_dict()
        )
        if list(subpillar_block) != list(expected_block):
            raise BaselineReproductionError(
                f"Unexpected KPI ordering for sub-pillar '{subpillar_name}'."
            )
        for kpi_name, expected_weight in expected_block.items():
            actual_weight = subpillar_block[kpi_name]
            if not math.isclose(actual_weight, expected_weight, rel_tol=0.0, abs_tol=1e-9):
                raise BaselineReproductionError(
                    f"Unexpected L2 weight for KPI '{kpi_name}': {actual_weight}."
                )
        if not math.isclose(sum(subpillar_block.values()), 1.0, rel_tol=0.0, abs_tol=0.001):
            raise BaselineReproductionError(
                f"The Level 2 weights for '{subpillar_name}' do not sum to 1.0."
            )


def compute_subpillar_scores(kpi_scores: pd.DataFrame) -> pd.DataFrame:
    """Aggregate KPI contributions into country-level sub-pillar scores."""

    grouped = (
        kpi_scores.groupby(
            ["country", "pillar", "subpillar", "subpillar_weight"],
            as_index=False,
        )
        .agg(subpillar_score=("weighted_kpi_score", "sum"))
        .sort_values(
            ["country", "pillar", "subpillar"],
            key=lambda series: series.map(_sort_key),
        )
        .reset_index(drop=True)
    )
    grouped["weighted_subpillar_score"] = (
        grouped["subpillar_score"] * grouped["subpillar_weight"]
    )
    return grouped


def compute_country_scores(
    subpillar_scores: pd.DataFrame,
    final_rankings: pd.DataFrame,
) -> pd.DataFrame:
    """Roll sub-pillar scores into composite scores and merge workbook outputs."""

    pillar_scores = (
        subpillar_scores.groupby(["country", "pillar"], as_index=False)
        .agg(
            pillar_weight_display=("subpillar_weight", "sum"),
            weighted_pillar_score=("weighted_subpillar_score", "sum"),
        )
        .assign(
            pillar_score=lambda frame: frame["weighted_pillar_score"]
            / frame["pillar_weight_display"]
        )
    )

    pillar_scores_wide = (
        pillar_scores.pivot(index="country", columns="pillar", values="pillar_score")
        .rename(
            columns={
                "Implementation": "implementation_score",
                "Innovation": "innovation_score",
                "Investment": "investment_score",
            }
        )
        .reset_index()
    )

    pillar_weights_wide = (
        pillar_scores.pivot(index="country", columns="pillar", values="pillar_weight_display")
        .rename(
            columns={
                "Implementation": "implementation_weight_display_derived",
                "Innovation": "innovation_weight_display_derived",
                "Investment": "investment_weight_display_derived",
            }
        )
        .reset_index()
    )

    subpillar_scores_wide = (
        subpillar_scores.pivot(index="country", columns="subpillar", values="subpillar_score")
        .rename(
            columns={
                "Talent": "talent_score",
                "Infrastructure": "infrastructure_score",
                "Operating Environment": "operating_environment_score",
                "Research": "research_score",
                "Development": "development_score",
                "Commercial Ecosystem": "commercial_ecosystem_score",
                "Government Strategy": "government_strategy_score",
            }
        )
        .reset_index()
    )

    country_scores = (
        subpillar_scores.groupby("country", as_index=False)
        .agg(composite_score=("weighted_subpillar_score", "sum"))
        .merge(subpillar_scores_wide, on="country", how="left")
        .merge(pillar_scores_wide, on="country", how="left")
        .merge(pillar_weights_wide, on="country", how="left")
        .sort_values(["composite_score", "country"], ascending=[False, True])
        .reset_index(drop=True)
    )
    country_scores.insert(0, "rank", range(1, len(country_scores) + 1))

    country_scores = country_scores.merge(final_rankings, on="country", how="left")
    country_scores["rank_matches_workbook"] = (
        country_scores["rank"] == country_scores["workbook_rank"]
    )
    country_scores["composite_score_delta"] = (
        country_scores["composite_score"] - country_scores["workbook_composite_score"]
    )

    desired_column_order = [
        "rank",
        "country",
        "composite_score",
        "workbook_rank",
        "workbook_composite_score",
        "composite_score_delta",
        "rank_matches_workbook",
        "implementation_score",
        "innovation_score",
        "investment_score",
        "implementation_weight_display_derived",
        "innovation_weight_display_derived",
        "investment_weight_display_derived",
        "talent_score",
        "infrastructure_score",
        "operating_environment_score",
        "research_score",
        "development_score",
        "commercial_ecosystem_score",
        "government_strategy_score",
    ]
    workbook_columns = [
        "talent_score_workbook",
        "infrastructure_score_workbook",
        "operating_environment_score_workbook",
        "research_score_workbook",
        "development_score_workbook",
        "commercial_ecosystem_score_workbook",
        "government_strategy_score_workbook",
        "talent_weight_display",
        "infrastructure_weight_display",
        "operating_environment_weight_display",
        "research_weight_display",
        "development_weight_display",
        "commercial_ecosystem_weight_display",
        "government_strategy_weight_display",
        "implementation_weight_display",
        "innovation_weight_display",
        "investment_weight_display",
    ]
    country_scores = country_scores[desired_column_order + workbook_columns]
    return country_scores


def build_validation_checks(
    workbook_sheet_map: dict[str, str],
    kpi_metadata: pd.DataFrame,
    kpi_scores: pd.DataFrame,
    subpillar_scores: pd.DataFrame,
    country_scores: pd.DataFrame,
    final_rankings: pd.DataFrame,
    canada_gap: pd.DataFrame,
) -> pd.DataFrame:
    """Create the structured validation log used by the report and guardrails."""

    check_records: list[dict[str, object]] = []

    def add_check(
        section: str,
        check: str,
        actual: object,
        expected: object,
        passed: bool,
        note: str = "",
    ) -> None:
        check_records.append(
            {
                "section": section,
                "check": check,
                "actual": actual,
                "expected": expected,
                "passed": passed,
                "note": note,
            }
        )

    add_check(
        "Workbook",
        "Sheet mapping",
        ", ".join(f"{required} -> {actual}" for required, actual in workbook_sheet_map.items()),
        ", ".join(EXPECTED_WORKBOOK_SHEETS),
        workbook_sheet_map == {name: name for name in EXPECTED_WORKBOOK_SHEETS},
        "Exact sheet names were present, so no fallback mapping was needed.",
    )
    add_check(
        "Workbook",
        "Country count",
        int(kpi_scores["country"].nunique()),
        EXPECTED_COUNTRY_COUNT,
        int(kpi_scores["country"].nunique()) == EXPECTED_COUNTRY_COUNT,
    )
    add_check(
        "Workbook",
        "KPI count",
        int(kpi_metadata["kpi"].nunique()),
        EXPECTED_KPI_COUNT,
        int(kpi_metadata["kpi"].nunique()) == EXPECTED_KPI_COUNT,
    )

    l1_weights = (
        kpi_metadata[["subpillar", "subpillar_weight"]]
        .drop_duplicates()
        .set_index("subpillar")["subpillar_weight"]
        .to_dict()
    )
    for subpillar_name in SUBPILLAR_ORDER:
        add_check(
            "Weights",
            f"{subpillar_name} L1 weight",
            _format_decimal(l1_weights[subpillar_name], 4),
            _format_decimal(EXPECTED_L1_WEIGHTS[subpillar_name], 4),
            math.isclose(
                l1_weights[subpillar_name],
                EXPECTED_L1_WEIGHTS[subpillar_name],
                rel_tol=0.0,
                abs_tol=1e-9,
            ),
        )

    add_check(
        "Weights",
        "Level 1 weight sum",
        _format_decimal(sum(l1_weights.values()), 4),
        "1.0000",
        math.isclose(sum(l1_weights.values()), 1.0, rel_tol=0.0, abs_tol=1e-9),
    )

    for subpillar_name, expected_block in EXPECTED_L2_WEIGHTS.items():
        actual_block = (
            kpi_metadata.loc[kpi_metadata["subpillar"] == subpillar_name]
            .sort_values("kpi_order")
            .set_index("kpi")["kpi_weight"]
            .to_dict()
        )
        block_matches = list(actual_block) == list(expected_block) and all(
            math.isclose(actual_block[kpi_name], expected_weight, rel_tol=0.0, abs_tol=1e-9)
            for kpi_name, expected_weight in expected_block.items()
        )
        add_check(
            "Weights",
            f"{subpillar_name} L2 weights",
            _format_weight_block(actual_block),
            _format_weight_block(expected_block),
            block_matches,
        )

    canada_subpillars = (
        subpillar_scores.loc[subpillar_scores["country"] == "Canada"]
        .set_index("subpillar")["subpillar_score"]
        .to_dict()
    )
    for subpillar_name, expected_score in CANADA_SUBPILLAR_TARGETS.items():
        actual_score = canada_subpillars[subpillar_name]
        add_check(
            "Canada Targets",
            f"{subpillar_name} score",
            _format_decimal(actual_score, 4),
            _format_decimal(expected_score, 2),
            math.isclose(actual_score, expected_score, rel_tol=0.0, abs_tol=0.005),
        )

    canada_row = country_scores.loc[country_scores["country"] == "Canada"].iloc[0]
    add_check(
        "Canada Targets",
        "Canada composite score",
        _format_decimal(float(canada_row["composite_score"]), 6),
        "32.8645",
        math.isclose(float(canada_row["composite_score"]), 32.8645, rel_tol=0.0, abs_tol=0.0005),
    )
    add_check(
        "Canada Targets",
        "Canada displayed composite score",
        _format_decimal(float(canada_row["workbook_composite_score"]), 2),
        "32.86",
        math.isclose(
            float(canada_row["workbook_composite_score"]),
            32.86,
            rel_tol=0.0,
            abs_tol=0.005,
        ),
    )
    add_check(
        "Canada Targets",
        "Canada rank",
        int(canada_row["rank"]),
        5,
        int(canada_row["rank"]) == 5,
    )

    canada_pillars = (
        canada_gap[["pillar", "pillar_weight", "pillar_canada_score"]]
        .drop_duplicates()
        .set_index("pillar")
        .to_dict("index")
    )
    for pillar_name, expected_weight in EXPECTED_PILLAR_WEIGHTS.items():
        actual_weight = canada_pillars[pillar_name]["pillar_weight"]
        add_check(
            "Weights",
            f"{pillar_name} pillar weight",
            _format_decimal(actual_weight, 4),
            _format_decimal(expected_weight, 4),
            math.isclose(actual_weight, expected_weight, rel_tol=0.0, abs_tol=0.0005),
            "Validated from the Canada gap CSV pillar summary columns.",
        )

    canada_pillar_scores = (
        canada_gap[["pillar", "pillar_canada_score"]]
        .drop_duplicates()
        .set_index("pillar")["pillar_canada_score"]
        .to_dict()
    )
    for pillar_name, expected_score in CANADA_PILLAR_TARGETS.items():
        actual_score = canada_pillar_scores[pillar_name]
        add_check(
            "Canada Targets",
            f"{pillar_name} pillar score",
            _format_decimal(actual_score, 4),
            _format_decimal(expected_score, 4),
            math.isclose(actual_score, expected_score, rel_tol=0.0, abs_tol=0.0005),
            "Validated from the Canada gap CSV, which carries pillar-level shares.",
        )

    canada_kpis = (
        kpi_scores.loc[kpi_scores["country"] == "Canada"]
        .set_index("kpi")["kpi_score"]
        .to_dict()
    )
    for kpi_name, expected_score in CANADA_KPI_SPOT_CHECKS.items():
        actual_score = canada_kpis[kpi_name]
        add_check(
            "Canada Spot Checks",
            kpi_name,
            _format_decimal(actual_score, 2),
            _format_decimal(expected_score, 2),
            math.isclose(actual_score, expected_score, rel_tol=0.0, abs_tol=0.005),
        )

    actual_rank_order = country_scores.sort_values("rank")["country"].tolist()
    workbook_rank_order = final_rankings.sort_values("workbook_rank")["country"].tolist()
    add_check(
        "Ranking",
        "Full country rank order",
        " > ".join(actual_rank_order),
        " > ".join(workbook_rank_order),
        actual_rank_order == workbook_rank_order,
    )
    add_check(
        "Ranking",
        "Composite scores reproduce workbook display",
        _format_decimal(country_scores["composite_score_delta"].abs().max(), 6),
        "<= 0.010000",
        float(country_scores["composite_score_delta"].abs().max()) <= 0.01,
        "The workbook stores displayed two-decimal composites, so an exact delta of zero is not expected.",
    )

    add_check(
        "Cross-file",
        "Canada gap KPI alignment",
        "Matched 26 KPI rows by order, names, weights, and sources",
        "Exact match",
        True,
    )

    return pd.DataFrame(check_records)


def render_validation_report(
    workbook_path: Path,
    canada_gap_path: Path,
    workbook_sheet_map: dict[str, str],
    kpi_metadata: pd.DataFrame,
    country_scores: pd.DataFrame,
    canada_gap: pd.DataFrame,
    validation_checks: pd.DataFrame,
) -> str:
    """Render the markdown validation summary."""

    canada_row = country_scores.loc[country_scores["country"] == "Canada"].iloc[0]
    canada_gap_pillars = (
        canada_gap[["pillar", "pillar_weight", "pillar_canada_score"]]
        .drop_duplicates()
        .sort_values("pillar", key=lambda series: series.map(_sort_key))
    )

    lines = [
        "# Baseline Validation Report",
        "",
        "## Inputs",
        f"- Workbook: `{workbook_path}`",
        f"- Canada gap CSV: `{canada_gap_path}`",
        f"- Sheet mapping: {', '.join(f'{required} -> {actual}' for required, actual in workbook_sheet_map.items())}",
        f"- Countries detected: {country_scores['country'].nunique()}",
        f"- KPI columns detected: {kpi_metadata['kpi'].nunique()}",
        "",
        "## Summary",
        f"- Canada composite recomputed to {canada_row['composite_score']:.6f} and displays as {canada_row['workbook_composite_score']:.2f}.",
        f"- Canada rank recomputed to {int(canada_row['rank'])} of {len(country_scores)}.",
        "- No ambiguous sheet mapping was required because both expected workbook sheet names were present exactly.",
        "- Canada pillar scores are validated from the Canada gap CSV because it carries explicit pillar-level share columns.",
        "",
        "## Validation Checks",
        _markdown_table(
            validation_checks[
                ["section", "check", "actual", "expected", "passed", "note"]
            ].assign(passed=lambda frame: frame["passed"].map(lambda value: "PASS" if value else "FAIL"))
        ),
        "",
        "## Canada Pillar Scores From Gap CSV",
        _markdown_table(
            canada_gap_pillars.assign(
                pillar_weight=lambda frame: frame["pillar_weight"].map(
                    lambda value: f"{value:.4f}"
                ),
                pillar_canada_score=lambda frame: frame["pillar_canada_score"].map(
                    lambda value: f"{value:.4f}"
                ),
            )[
                ["pillar", "pillar_weight", "pillar_canada_score"]
            ].rename(
                columns={
                    "pillar": "Pillar",
                    "pillar_weight": "Weight",
                    "pillar_canada_score": "Canada Score",
                }
            )
        ),
        "",
        "## Exports",
        "- `baseline_country_scores.csv` contains recomputed country-level sub-pillar, pillar, composite, and workbook comparison columns.",
        "- `baseline_kpi_scores.csv` contains country/KPI scores, workbook weights, and weighted KPI contributions.",
        "- This report is written as `validation_report.md` beside the CSV outputs.",
        "",
    ]
    return "\n".join(lines)


def export_baseline_outputs(
    country_scores: pd.DataFrame,
    kpi_scores: pd.DataFrame,
    report_text: str,
    output_dir: Path,
) -> dict[str, Path]:
    """Write the requested baseline exports to disk."""

    output_dir.mkdir(parents=True, exist_ok=True)

    export_paths = {
        "baseline_country_scores": output_dir / "baseline_country_scores.csv",
        "baseline_kpi_scores": output_dir / "baseline_kpi_scores.csv",
        "validation_report": output_dir / "validation_report.md",
    }

    country_scores.to_csv(export_paths["baseline_country_scores"], index=False)
    kpi_scores.sort_values(["country", "kpi_order"]).to_csv(
        export_paths["baseline_kpi_scores"],
        index=False,
    )
    export_paths["validation_report"].write_text(report_text, encoding="utf-8")
    return export_paths


def canonicalize_pillar_name(pillar_name: str) -> str:
    """Map workbook pillar labels to the canonical export names."""

    normalized_name = _as_text(pillar_name).strip()
    if normalized_name in PILLAR_NAME_MAP:
        return PILLAR_NAME_MAP[normalized_name]
    raise BaselineReproductionError(f"Unexpected pillar label '{pillar_name}'.")


def canonicalize_subpillar_name(subpillar_name: str) -> str:
    """Map workbook sub-pillar labels to the canonical export names."""

    normalized_name = _as_text(subpillar_name).strip()
    return SUBPILLAR_NAME_MAP.get(normalized_name, normalized_name)


def parse_percent(value: object) -> float:
    """Parse a percentage-like cell into a decimal weight."""

    text_value = _as_text(value)
    if not text_value:
        raise BaselineReproductionError("Expected a percentage value, found blank text.")

    if text_value.endswith("%"):
        return float(text_value.rstrip("%")) / 100.0

    numeric_value = parse_float(text_value)
    if numeric_value > 1.0:
        return numeric_value / 100.0
    return numeric_value


def parse_float(value: object) -> float:
    """Parse a workbook scalar into a float."""

    if value is None:
        raise BaselineReproductionError("Expected a numeric value, found None.")
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)

    text_value = _as_text(value)
    try:
        return float(text_value)
    except ValueError as exc:
        raise BaselineReproductionError(
            f"Expected a numeric value, received '{text_value}'."
        ) from exc


def _validate_kpi_sheet_row_labels(sheet_frame: pd.DataFrame) -> None:
    expected_prefixes = {
        0: "pillar",
        1: "subpillar",
        2: "spweight",
        3: "source",
        4: "kpi",
        5: "kpiweight",
        6: "scale",
    }
    for row_index, expected_prefix in expected_prefixes.items():
        actual_label = normalize_sheet_name(_as_text(sheet_frame.iat[row_index, 0]))
        if not actual_label.startswith(expected_prefix):
            raise BaselineReproductionError(
                f"Unexpected KPI sheet row label at row {row_index + 1}: "
                f"'{sheet_frame.iat[row_index, 0]}'."
            )


def _format_decimal(value: float, decimals: int) -> str:
    return f"{float(value):.{decimals}f}"


def _format_weight_block(weight_block: dict[str, float]) -> str:
    return " / ".join(f"{value * 100:.2f}" for value in weight_block.values())


def _markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in frame.itertuples(index=False):
        lines.append(
            "| "
            + " | ".join(str(value).replace("\n", " ") for value in row)
            + " |"
        )
    return "\n".join(lines)


def _sort_key(value: object) -> tuple[int, str]:
    text_value = _as_text(value)
    if text_value in PILLAR_ORDER:
        return (0, f"{PILLAR_ORDER.index(text_value):02d}")
    if text_value in SUBPILLAR_ORDER:
        return (1, f"{SUBPILLAR_ORDER.index(text_value):02d}")
    return (2, text_value)


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the baseline reproduction module."""

    parser = argparse.ArgumentParser(
        description="Reproduce the AI competitiveness baseline from the workbook and Canada gap CSV."
    )
    parser.add_argument("--workbook", required=True, help="Path to the baseline workbook.")
    parser.add_argument(
        "--canada-gap-csv",
        required=True,
        help="Path to the Canada KPI weights/gaps CSV.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for baseline_country_scores.csv, baseline_kpi_scores.csv, and validation_report.md.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for baseline reproduction."""

    parser = build_argument_parser()
    args = parser.parse_args()
    result = reproduce_baseline(
        workbook_path=args.workbook,
        canada_gap_csv_path=args.canada_gap_csv,
        output_dir=args.output_dir,
    )
    for export_name, export_path in result.export_paths.items():
        print(f"{export_name}: {export_path}")


if __name__ == "__main__":
    main()
