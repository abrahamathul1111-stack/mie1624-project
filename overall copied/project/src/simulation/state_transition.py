"""Quarterly state-transition simulation for AI competitiveness scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import argparse
import math
import re

import numpy as np
import pandas as pd


DEFAULT_BASELINE_COUNTRY_PATH = Path("outputs") / "tables" / "baseline_country_scores.csv"
DEFAULT_BASELINE_KPI_PATH = Path("outputs") / "tables" / "baseline_kpi_scores.csv"
DEFAULT_IMPACT_MATRIX_PATH = Path("outputs") / "tables" / "impact_matrix.csv"
DEFAULT_IMPACT_METADATA_PATH = Path("outputs") / "tables" / "impact_matrix_long.csv"
DEFAULT_EFFECT_CALIBRATION_PATH = Path("data") / "calibration" / "calibration_effects.csv"
DEFAULT_LAG_CALIBRATION_PATH = Path("data") / "calibration" / "calibration_lags.csv"
DEFAULT_COMPETITOR_DRIFT_PATH = Path("data") / "calibration" / "competitor_drift.csv"
DEFAULT_IMPLEMENTATION_SCHEDULE_PATH = (
    Path("data") / "calibration" / "implementation_schedule.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs") / "tables"

EXPECTED_COUNTRY_COUNT = 13
EXPECTED_KPI_COUNT = 26
CLIP_MIN_SCORE = 0.0
CLIP_MAX_SCORE = 100.0

REQUIRED_BASELINE_COUNTRY_COLUMNS = ["country", "rank", "composite_score"]
REQUIRED_BASELINE_KPI_COLUMNS = [
    "country",
    "kpi_order",
    "pillar",
    "subpillar",
    "subpillar_weight",
    "kpi",
    "kpi_weight",
    "kpi_score",
]
REQUIRED_IMPACT_METADATA_COLUMNS = [
    "recommendation_id",
    "lever_id",
    "lever_name",
    "KPI",
    "numeric_coefficient",
    "lag_class",
    "lag_quarters",
    "ramp_type",
    "calibration_effect_lever_id",
    "calibration_lag_lever_id",
    "calibration_confidence",
]
REQUIRED_EFFECT_COLUMNS = [
    "lever_id",
    "effect_direction",
    "effect_low",
    "effect_base",
    "effect_high",
    "confidence",
]
REQUIRED_LAG_COLUMNS = [
    "lever_id",
    "lag_quarters_low",
    "lag_quarters_base",
    "lag_quarters_high",
    "ramp_type",
]
REQUIRED_SCHEDULE_COLUMNS = [
    "recommendation_id",
    "lever_id",
    "start_quarter",
    "full_effect_quarter",
    "rollout_pattern",
]
REQUIRED_DRIFT_COLUMNS = [
    "cluster",
    "kpi",
    "drift_low",
    "drift_base",
    "drift_high",
    "confidence",
]

SCENARIO_DEFINITIONS = {
    "baseline": tuple(),
    "rec1_only": ("rec1",),
    "rec2_only": ("rec2",),
    "rec3_only": ("rec3",),
    "all_recommendations": ("rec1", "rec2", "rec3"),
}

COUNTRY_CLUSTER_MAP = {
    "United States of America": "Cluster 2 USA/China",
    "China": "Cluster 2 USA/China",
    "South Korea": "Cluster 1 Asia-Pacific / high-intensity",
    "Singapore": "Cluster 1 Asia-Pacific / high-intensity",
    "India": "Cluster 1 Asia-Pacific / high-intensity",
    "Israel": "Cluster 1 Asia-Pacific / high-intensity",
    "UAE": "Cluster 1 Asia-Pacific / high-intensity",
    "Japan": "Cluster 1 Asia-Pacific / high-intensity",
    "Canada": "Cluster 3 Western policy-led peers",
    "United Kingdom": "Cluster 3 Western policy-led peers",
    "Germany": "Cluster 3 Western policy-led peers",
    "France": "Cluster 3 Western policy-led peers",
    "Spain": "Cluster 3 Western policy-led peers",
}

PILLAR_EXPORT_COLUMNS = {
    "Implementation": "implementation_score_median",
    "Innovation": "innovation_score_median",
    "Investment": "investment_score_median",
}
SUBPILLAR_EXPORT_COLUMNS = {
    "Talent": "talent_score_median",
    "Infrastructure": "infrastructure_score_median",
    "Operating Environment": "operating_environment_score_median",
    "Research": "research_score_median",
    "Development": "development_score_median",
    "Commercial Ecosystem": "commercial_ecosystem_score_median",
    "Government Strategy": "government_strategy_score_median",
}

EFFECT_CONFIDENCE_BAND_WIDTH = {
    "high": 0.10,
    "medium": 0.20,
    "weak-to-medium": 0.25,
    "medium on direction, weak on size": 0.25,
    "weak": 0.30,
}
DRIFT_CLUSTER_INTENSITY = {
    "Cluster 1 Asia-Pacific / high-intensity": 1.15,
    "Cluster 2 USA/China": 1.45,
    "Cluster 3 Western policy-led peers": 1.00,
}
DRIFT_CONFIDENCE_FACTOR = {
    "high": 1.10,
    "medium": 1.00,
    "weak-to-medium": 0.90,
    "weak": 0.85,
}
DRIFT_SCENARIO_MULTIPLIER = {
    "low": 0.80,
    "base": 1.00,
    "high": 1.25,
}
BASE_DRIFT_RATE_POINTS = 0.30
DRIFT_KPI_ALIASES = {
    "AI Patent Grants": "AI Patent Grants (per 100k)",
}
RESPONSE_WINDOW_BY_RAMP = {
    "front_loaded_then_s_curve": 4,
    "front_loaded_then_decay_if_retention_weak": 6,
    "slow_start_then_s_curve": 5,
    "back_loaded": 6,
    "pilot_to_scale_s_curve": 4,
    "lumpy_contract_driven": 6,
}


class QuarterlyStateTransitionError(ValueError):
    """Raised when simulation inputs cannot be aligned deterministically."""


@dataclass(slots=True)
class StateTransitionConfig:
    """Configuration for the quarterly scenario simulation."""

    start_quarter: str = "2026Q1"
    quarters: int = 16
    draws: int = 10000
    random_seed: int | None = 42
    canada_country: str = "Canada"


@dataclass(slots=True)
class SimulationInputs:
    """Validated inputs and derived matrices used by the simulation engine."""

    baseline_country_scores: pd.DataFrame
    baseline_kpi_scores: pd.DataFrame
    kpi_metadata: pd.DataFrame
    countries: list[str]
    kpis: list[str]
    pillars: list[str]
    subpillars: list[str]
    country_to_index: dict[str, int]
    kpi_to_index: dict[str, int]
    baseline_kpi_matrix: np.ndarray
    kpi_to_subpillar_weights: np.ndarray
    subpillar_weights: np.ndarray
    subpillar_to_pillar_shares: np.ndarray
    impact_matrix: pd.DataFrame
    impact_metadata: pd.DataFrame
    effect_calibration: pd.DataFrame
    lag_calibration: pd.DataFrame
    schedule_frame: pd.DataFrame
    schedule_profiles: dict[str, np.ndarray]
    drift_priors: pd.DataFrame
    country_clusters: dict[str, str]
    quarter_labels: list[str]


@dataclass(slots=True)
class StateTransitionResult:
    """Simulation exports for downstream notebooks and dashboards."""

    simulation_summary: pd.DataFrame
    country_quarter_scores: pd.DataFrame
    canada_kpi_trajectories: pd.DataFrame
    canada_rank_trajectory: pd.DataFrame
    scenario_comparison: pd.DataFrame
    export_paths: dict[str, Path] = field(default_factory=dict)


def run_quarterly_state_transition(
    config: StateTransitionConfig | None = None,
    baseline_country_path: str | Path = DEFAULT_BASELINE_COUNTRY_PATH,
    baseline_kpi_path: str | Path = DEFAULT_BASELINE_KPI_PATH,
    impact_matrix_path: str | Path = DEFAULT_IMPACT_MATRIX_PATH,
    impact_metadata_path: str | Path = DEFAULT_IMPACT_METADATA_PATH,
    implementation_schedule_path: str | Path = DEFAULT_IMPLEMENTATION_SCHEDULE_PATH,
    calibration_effects_path: str | Path = DEFAULT_EFFECT_CALIBRATION_PATH,
    calibration_lags_path: str | Path = DEFAULT_LAG_CALIBRATION_PATH,
    competitor_drift_path: str | Path = DEFAULT_COMPETITOR_DRIFT_PATH,
    output_dir: str | Path | None = None,
) -> StateTransitionResult:
    """Run all required scenarios and write the requested exports."""

    simulation_config = config or StateTransitionConfig()
    inputs = load_simulation_inputs(
        config=simulation_config,
        baseline_country_path=baseline_country_path,
        baseline_kpi_path=baseline_kpi_path,
        impact_matrix_path=impact_matrix_path,
        impact_metadata_path=impact_metadata_path,
        implementation_schedule_path=implementation_schedule_path,
        calibration_effects_path=calibration_effects_path,
        calibration_lags_path=calibration_lags_path,
        competitor_drift_path=competitor_drift_path,
    )

    scenario_summary_frames: list[pd.DataFrame] = []
    canada_kpi_frames: list[pd.DataFrame] = []
    canada_rank_frames: list[pd.DataFrame] = []

    for scenario_index, (scenario_name, active_recommendations) in enumerate(
        SCENARIO_DEFINITIONS.items()
    ):
        scenario_seed = None
        if simulation_config.random_seed is not None:
            scenario_seed = simulation_config.random_seed + (scenario_index * 9973)
        rng = np.random.default_rng(scenario_seed)

        scenario_summary, canada_kpis, canada_rank = simulate_scenario(
            inputs=inputs,
            config=simulation_config,
            scenario_name=scenario_name,
            active_recommendations=active_recommendations,
            rng=rng,
        )
        scenario_summary_frames.append(scenario_summary)
        canada_kpi_frames.append(canada_kpis)
        canada_rank_frames.append(canada_rank)

    simulation_summary = pd.concat(scenario_summary_frames, ignore_index=True)
    canada_kpi_trajectories = pd.concat(canada_kpi_frames, ignore_index=True)
    canada_rank_trajectory = pd.concat(canada_rank_frames, ignore_index=True)
    country_quarter_scores = build_country_quarter_scores(simulation_summary)
    scenario_comparison = build_scenario_comparison(canada_rank_trajectory)

    simulation_summary = sort_export_frame(
        simulation_summary,
        by=["scenario", "quarter_index", "country"],
    )
    country_quarter_scores = sort_export_frame(
        country_quarter_scores,
        by=["scenario", "quarter_index", "rank", "country"],
    )
    canada_kpi_trajectories = sort_export_frame(
        canada_kpi_trajectories,
        by=["scenario", "quarter_index", "kpi_order"],
    )
    canada_rank_trajectory = sort_export_frame(
        canada_rank_trajectory,
        by=["scenario", "quarter_index"],
    )
    scenario_comparison = sort_export_frame(
        scenario_comparison,
        by=["scenario"],
    )

    resolved_output_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir is not None
        else (Path.cwd() / DEFAULT_OUTPUT_DIR).resolve()
    )
    export_paths = export_simulation_outputs(
        simulation_summary=simulation_summary,
        country_quarter_scores=country_quarter_scores,
        canada_kpi_trajectories=canada_kpi_trajectories,
        canada_rank_trajectory=canada_rank_trajectory,
        scenario_comparison=scenario_comparison,
        output_dir=resolved_output_dir,
    )

    return StateTransitionResult(
        simulation_summary=simulation_summary,
        country_quarter_scores=country_quarter_scores,
        canada_kpi_trajectories=canada_kpi_trajectories,
        canada_rank_trajectory=canada_rank_trajectory,
        scenario_comparison=scenario_comparison,
        export_paths=export_paths,
    )


def load_simulation_inputs(
    config: StateTransitionConfig,
    baseline_country_path: str | Path,
    baseline_kpi_path: str | Path,
    impact_matrix_path: str | Path,
    impact_metadata_path: str | Path,
    implementation_schedule_path: str | Path,
    calibration_effects_path: str | Path,
    calibration_lags_path: str | Path,
    competitor_drift_path: str | Path,
) -> SimulationInputs:
    """Load, validate, and derive the matrices required by the simulator."""

    baseline_country_scores = pd.read_csv(Path(baseline_country_path).expanduser().resolve())
    baseline_kpi_scores = pd.read_csv(Path(baseline_kpi_path).expanduser().resolve())
    effect_calibration = pd.read_csv(Path(calibration_effects_path).expanduser().resolve())
    lag_calibration = pd.read_csv(Path(calibration_lags_path).expanduser().resolve())
    impact_metadata = pd.read_csv(Path(impact_metadata_path).expanduser().resolve())
    impact_matrix = pd.read_csv(Path(impact_matrix_path).expanduser().resolve())
    schedule_frame = pd.read_csv(Path(implementation_schedule_path).expanduser().resolve())
    competitor_drift = pd.read_csv(Path(competitor_drift_path).expanduser().resolve())

    _validate_columns(
        baseline_country_scores,
        REQUIRED_BASELINE_COUNTRY_COLUMNS,
        "baseline country scores",
    )
    _validate_columns(baseline_kpi_scores, REQUIRED_BASELINE_KPI_COLUMNS, "baseline KPI scores")
    _validate_columns(effect_calibration, REQUIRED_EFFECT_COLUMNS, "effect calibration")
    _validate_columns(lag_calibration, REQUIRED_LAG_COLUMNS, "lag calibration")
    _validate_columns(impact_metadata, REQUIRED_IMPACT_METADATA_COLUMNS, "impact metadata")
    _validate_columns(schedule_frame, REQUIRED_SCHEDULE_COLUMNS, "implementation schedule")
    _validate_columns(competitor_drift, REQUIRED_DRIFT_COLUMNS, "competitor drift")

    countries = (
        baseline_country_scores.sort_values(["rank", "country"])["country"].tolist()
    )
    if len(countries) != EXPECTED_COUNTRY_COUNT:
        raise QuarterlyStateTransitionError(
            f"Expected {EXPECTED_COUNTRY_COUNT} countries, found {len(countries)}."
        )
    if config.canada_country not in countries:
        raise QuarterlyStateTransitionError(
            f"Canada country key '{config.canada_country}' was not found in the baseline export."
        )

    kpi_metadata = (
        baseline_kpi_scores[
            ["kpi_order", "pillar", "subpillar", "subpillar_weight", "kpi", "kpi_weight"]
        ]
        .drop_duplicates()
        .sort_values("kpi_order")
        .reset_index(drop=True)
    )
    if len(kpi_metadata) != EXPECTED_KPI_COUNT:
        raise QuarterlyStateTransitionError(
            f"Expected {EXPECTED_KPI_COUNT} unique KPIs, found {len(kpi_metadata)}."
        )
    if kpi_metadata["kpi"].duplicated().any():
        duplicates = kpi_metadata.loc[kpi_metadata["kpi"].duplicated(), "kpi"].tolist()
        raise QuarterlyStateTransitionError(f"Duplicate KPI names detected: {duplicates}")

    kpis = kpi_metadata["kpi"].tolist()
    pillars = (
        kpi_metadata.groupby("pillar", as_index=False)["kpi_order"]
        .min()
        .sort_values("kpi_order")["pillar"]
        .tolist()
    )
    subpillars = (
        kpi_metadata.groupby("subpillar", as_index=False)["kpi_order"]
        .min()
        .sort_values("kpi_order")["subpillar"]
        .tolist()
    )

    baseline_matrix = (
        baseline_kpi_scores.pivot(index="country", columns="kpi", values="kpi_score")
        .reindex(index=countries, columns=kpis)
        .astype(float)
        .to_numpy()
    )
    if np.isnan(baseline_matrix).any():
        raise QuarterlyStateTransitionError("The baseline KPI matrix contains missing values.")

    country_to_index = {country: index for index, country in enumerate(countries)}
    kpi_to_index = {kpi_name: index for index, kpi_name in enumerate(kpis)}
    pillar_to_index = {pillar_name: index for index, pillar_name in enumerate(pillars)}
    subpillar_to_index = {
        subpillar_name: index for index, subpillar_name in enumerate(subpillars)
    }

    kpi_to_subpillar_weights = np.zeros((len(kpis), len(subpillars)), dtype="float64")
    subpillar_weights = np.zeros(len(subpillars), dtype="float64")
    pillar_weights = np.zeros(len(pillars), dtype="float64")
    subpillar_to_pillar_shares = np.zeros((len(subpillars), len(pillars)), dtype="float64")

    subpillar_frame = (
        kpi_metadata[["pillar", "subpillar", "subpillar_weight"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    for row in kpi_metadata.to_dict("records"):
        kpi_index = kpi_to_index[str(row["kpi"])]
        subpillar_index = subpillar_to_index[str(row["subpillar"])]
        kpi_to_subpillar_weights[kpi_index, subpillar_index] = float(row["kpi_weight"])

    for row in subpillar_frame.to_dict("records"):
        pillar_name = str(row["pillar"])
        subpillar_name = str(row["subpillar"])
        subpillar_weight = float(row["subpillar_weight"])
        subpillar_index = subpillar_to_index[subpillar_name]
        pillar_index = pillar_to_index[pillar_name]
        subpillar_weights[subpillar_index] = subpillar_weight
        pillar_weights[pillar_index] += subpillar_weight

    for row in subpillar_frame.to_dict("records"):
        pillar_name = str(row["pillar"])
        subpillar_name = str(row["subpillar"])
        subpillar_weight = float(row["subpillar_weight"])
        subpillar_index = subpillar_to_index[subpillar_name]
        pillar_index = pillar_to_index[pillar_name]
        subpillar_to_pillar_shares[subpillar_index, pillar_index] = (
            subpillar_weight / pillar_weights[pillar_index]
        )

    validate_baseline_alignment(
        baseline_country_scores=baseline_country_scores,
        countries=countries,
        baseline_kpi_matrix=baseline_matrix,
        kpi_to_subpillar_weights=kpi_to_subpillar_weights,
        subpillar_weights=subpillar_weights,
    )

    impact_matrix = normalize_impact_matrix(impact_matrix=impact_matrix, baseline_kpis=kpis)
    validate_impact_metadata(
        impact_metadata=impact_metadata,
        impact_matrix=impact_matrix,
        baseline_kpis=kpis,
        kpi_to_index=kpi_to_index,
    )

    effect_calibration = effect_calibration.drop_duplicates("lever_id").reset_index(drop=True)
    lag_calibration = lag_calibration.drop_duplicates("lever_id").reset_index(drop=True)
    if effect_calibration["lever_id"].duplicated().any():
        raise QuarterlyStateTransitionError("Effect calibration contains duplicate lever ids.")
    if lag_calibration["lever_id"].duplicated().any():
        raise QuarterlyStateTransitionError("Lag calibration contains duplicate lever ids.")

    missing_effect_ids = sorted(
        set(impact_metadata["calibration_effect_lever_id"]) - set(effect_calibration["lever_id"])
    )
    if missing_effect_ids:
        raise QuarterlyStateTransitionError(
            "Impact metadata references missing effect-calibration ids: "
            f"{missing_effect_ids}"
        )

    missing_lag_ids = sorted(
        set(impact_metadata["calibration_lag_lever_id"]) - set(lag_calibration["lever_id"])
    )
    if missing_lag_ids:
        raise QuarterlyStateTransitionError(
            "Impact metadata references missing lag-calibration ids: "
            f"{missing_lag_ids}"
        )

    schedule_frame = schedule_frame.drop_duplicates("lever_id").reset_index(drop=True)
    required_schedule_ids = sorted(set(impact_metadata["calibration_lag_lever_id"]))
    missing_schedule_ids = sorted(set(required_schedule_ids) - set(schedule_frame["lever_id"]))
    if missing_schedule_ids:
        raise QuarterlyStateTransitionError(
            "Implementation schedule is missing lever ids used by the impact metadata: "
            f"{missing_schedule_ids}"
        )

    schedule_profiles = {}
    for schedule_row in schedule_frame.to_dict("records"):
        schedule_profiles[str(schedule_row["lever_id"])] = build_rollout_profile(
            start_quarter=str(schedule_row["start_quarter"]),
            full_effect_quarter=str(schedule_row["full_effect_quarter"]),
            rollout_pattern=str(schedule_row["rollout_pattern"]),
            quarters=config.quarters,
        )

    drift_priors = build_competitor_drift_priors(competitor_drift, baseline_kpis=kpis)
    country_clusters = map_countries_to_clusters(countries)
    available_clusters = set(drift_priors["cluster"])
    missing_cluster_priors = sorted(set(country_clusters.values()) - available_clusters)
    if missing_cluster_priors:
        raise QuarterlyStateTransitionError(
            "Competitor drift priors are missing clusters used by the baseline country set: "
            f"{missing_cluster_priors}"
        )

    impact_metadata = impact_metadata.copy()
    impact_metadata["kpi_index"] = impact_metadata["KPI"].map(kpi_to_index)
    if impact_metadata["kpi_index"].isna().any():
        raise QuarterlyStateTransitionError("Impact metadata could not be mapped to KPI indexes.")
    impact_metadata["kpi_index"] = impact_metadata["kpi_index"].astype(int)

    lever_names = impact_matrix["lever_name"].tolist()
    lever_to_index = {lever_name: index for index, lever_name in enumerate(lever_names)}
    impact_metadata["lever_index"] = impact_metadata["lever_name"].map(lever_to_index)
    if impact_metadata["lever_index"].isna().any():
        raise QuarterlyStateTransitionError("Impact metadata could not be mapped to lever indexes.")
    impact_metadata["lever_index"] = impact_metadata["lever_index"].astype(int)

    return SimulationInputs(
        baseline_country_scores=baseline_country_scores,
        baseline_kpi_scores=baseline_kpi_scores,
        kpi_metadata=kpi_metadata,
        countries=countries,
        kpis=kpis,
        pillars=pillars,
        subpillars=subpillars,
        country_to_index=country_to_index,
        kpi_to_index=kpi_to_index,
        baseline_kpi_matrix=baseline_matrix,
        kpi_to_subpillar_weights=kpi_to_subpillar_weights,
        subpillar_weights=subpillar_weights,
        subpillar_to_pillar_shares=subpillar_to_pillar_shares,
        impact_matrix=impact_matrix,
        impact_metadata=impact_metadata,
        effect_calibration=effect_calibration,
        lag_calibration=lag_calibration,
        schedule_frame=schedule_frame,
        schedule_profiles=schedule_profiles,
        drift_priors=drift_priors,
        country_clusters=country_clusters,
        quarter_labels=build_quarter_labels(config.start_quarter, config.quarters),
    )


def simulate_scenario(
    inputs: SimulationInputs,
    config: StateTransitionConfig,
    scenario_name: str,
    active_recommendations: tuple[str, ...],
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Simulate one scenario and aggregate medians and uncertainty bands."""

    draws = int(config.draws)
    if draws <= 0:
        raise QuarterlyStateTransitionError("Monte Carlo draw count must be positive.")

    quarter_count = int(config.quarters)
    country_count = len(inputs.countries)
    kpi_count = len(inputs.kpis)
    canada_index = inputs.country_to_index[config.canada_country]

    current_state = np.broadcast_to(
        inputs.baseline_kpi_matrix[np.newaxis, :, :],
        (draws, country_count, kpi_count),
    ).copy()
    baseline_canada_vector = inputs.baseline_kpi_matrix[canada_index]
    drift_rates = sample_country_drift_rates(
        inputs=inputs,
        canada_country=config.canada_country,
        draws=draws,
        rng=rng,
    )
    canada_policy_shift = build_canada_policy_shift(
        inputs=inputs,
        active_recommendations=active_recommendations,
        draws=draws,
        quarters=quarter_count,
        rng=rng,
    )

    summary_frames: list[pd.DataFrame] = []
    canada_kpi_frames: list[pd.DataFrame] = []
    canada_rank_records: list[dict[str, object]] = []

    for quarter_zero_index, quarter_label in enumerate(inputs.quarter_labels):
        if quarter_zero_index > 0:
            current_state += drift_rates * ((CLIP_MAX_SCORE - current_state) / CLIP_MAX_SCORE)
            current_state = np.clip(current_state, CLIP_MIN_SCORE, CLIP_MAX_SCORE)

        current_state[:, canada_index, :] = np.clip(
            baseline_canada_vector[np.newaxis, :] + canada_policy_shift[:, quarter_zero_index, :],
            CLIP_MIN_SCORE,
            CLIP_MAX_SCORE,
        )

        subpillar_scores = np.tensordot(
            current_state,
            inputs.kpi_to_subpillar_weights,
            axes=([2], [0]),
        )
        pillar_scores = np.tensordot(
            subpillar_scores,
            inputs.subpillar_to_pillar_shares,
            axes=([2], [0]),
        )
        composite_scores = np.tensordot(
            subpillar_scores,
            inputs.subpillar_weights,
            axes=([2], [0]),
        )
        ranks = compute_country_ranks(composite_scores, countries=inputs.countries)

        quarter_index = quarter_zero_index + 1
        summary_frames.append(
            build_country_summary_frame(
                scenario_name=scenario_name,
                quarter_index=quarter_index,
                quarter_label=quarter_label,
                countries=inputs.countries,
                pillars=inputs.pillars,
                subpillars=inputs.subpillars,
                composite_scores=composite_scores,
                ranks=ranks,
                pillar_scores=pillar_scores,
                subpillar_scores=subpillar_scores,
            )
        )
        canada_kpi_frames.append(
            build_canada_kpi_frame(
                scenario_name=scenario_name,
                quarter_index=quarter_index,
                quarter_label=quarter_label,
                kpi_metadata=inputs.kpi_metadata,
                canada_kpi_scores=current_state[:, canada_index, :],
            )
        )

        canada_composite_q = np.percentile(composite_scores[:, canada_index], [10, 50, 90])
        canada_rank_q = np.percentile(ranks[:, canada_index], [10, 50, 90])
        canada_rank_records.append(
            {
                "scenario": scenario_name,
                "quarter_index": quarter_index,
                "quarter": quarter_label,
                "country": config.canada_country,
                "composite_score_p10": float(canada_composite_q[0]),
                "composite_score_median": float(canada_composite_q[1]),
                "composite_score_p90": float(canada_composite_q[2]),
                "rank_p10": float(canada_rank_q[0]),
                "rank_median": float(canada_rank_q[1]),
                "rank_p90": float(canada_rank_q[2]),
            }
        )

    return (
        pd.concat(summary_frames, ignore_index=True),
        pd.concat(canada_kpi_frames, ignore_index=True),
        pd.DataFrame(canada_rank_records),
    )


def build_country_quarter_scores(simulation_summary: pd.DataFrame) -> pd.DataFrame:
    """Keep the median path columns used for displayed scenario trajectories."""

    median_columns = [
        "scenario",
        "quarter_index",
        "quarter",
        "country",
        "rank_median",
        "composite_score_median",
        *PILLAR_EXPORT_COLUMNS.values(),
        *SUBPILLAR_EXPORT_COLUMNS.values(),
    ]
    return simulation_summary[median_columns].rename(
        columns={
            "rank_median": "rank",
            "composite_score_median": "composite_score",
            "implementation_score_median": "implementation_score",
            "innovation_score_median": "innovation_score",
            "investment_score_median": "investment_score",
            "talent_score_median": "talent_score",
            "infrastructure_score_median": "infrastructure_score",
            "operating_environment_score_median": "operating_environment_score",
            "research_score_median": "research_score",
            "development_score_median": "development_score",
            "commercial_ecosystem_score_median": "commercial_ecosystem_score",
            "government_strategy_score_median": "government_strategy_score",
        }
    )


def build_scenario_comparison(canada_rank_trajectory: pd.DataFrame) -> pd.DataFrame:
    """Summarize the final-quarter Canada outcome across scenarios."""

    final_quarter_index = int(canada_rank_trajectory["quarter_index"].max())
    final_rows = canada_rank_trajectory.loc[
        canada_rank_trajectory["quarter_index"] == final_quarter_index
    ].copy()
    start_rows = canada_rank_trajectory.loc[
        canada_rank_trajectory["quarter_index"] == 1,
        ["scenario", "composite_score_median", "rank_median"],
    ].rename(
        columns={
            "composite_score_median": "start_composite_score_median",
            "rank_median": "start_rank_median",
        }
    )
    baseline_row = final_rows.loc[final_rows["scenario"] == "baseline"]
    if len(baseline_row) != 1:
        raise QuarterlyStateTransitionError(
            "Expected exactly one baseline row in the Canada rank trajectory."
        )
    baseline_composite = float(baseline_row["composite_score_median"].iloc[0])
    baseline_rank = float(baseline_row["rank_median"].iloc[0])

    final_rows = final_rows.merge(start_rows, on="scenario", how="left")
    final_rows["composite_score_delta_vs_baseline"] = (
        final_rows["composite_score_median"] - baseline_composite
    )
    final_rows["rank_delta_vs_baseline"] = final_rows["rank_median"] - baseline_rank
    final_rows["composite_score_delta_vs_start"] = (
        final_rows["composite_score_median"] - final_rows["start_composite_score_median"]
    )
    final_rows["rank_delta_vs_start"] = (
        final_rows["rank_median"] - final_rows["start_rank_median"]
    )
    return final_rows.drop(columns=["start_composite_score_median", "start_rank_median"])


def export_simulation_outputs(
    simulation_summary: pd.DataFrame,
    country_quarter_scores: pd.DataFrame,
    canada_kpi_trajectories: pd.DataFrame,
    canada_rank_trajectory: pd.DataFrame,
    scenario_comparison: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    """Write the requested simulation exports to disk."""

    output_dir.mkdir(parents=True, exist_ok=True)
    export_paths = {
        "simulation_summary": output_dir / "simulation_summary.csv",
        "country_quarter_scores": output_dir / "country_quarter_scores.csv",
        "canada_kpi_trajectories": output_dir / "canada_kpi_trajectories.csv",
        "canada_rank_trajectory": output_dir / "canada_rank_trajectory.csv",
        "scenario_comparison": output_dir / "scenario_comparison.csv",
    }

    simulation_summary.to_csv(export_paths["simulation_summary"], index=False)
    country_quarter_scores.to_csv(export_paths["country_quarter_scores"], index=False)
    canada_kpi_trajectories.to_csv(export_paths["canada_kpi_trajectories"], index=False)
    canada_rank_trajectory.to_csv(export_paths["canada_rank_trajectory"], index=False)
    scenario_comparison.to_csv(export_paths["scenario_comparison"], index=False)
    return export_paths


def normalize_impact_matrix(impact_matrix: pd.DataFrame, baseline_kpis: list[str]) -> pd.DataFrame:
    """Normalize the exported impact matrix into a lever-name keyed frame."""

    normalized_matrix = impact_matrix.copy()
    first_column = str(normalized_matrix.columns[0])
    if first_column != "lever_name":
        normalized_matrix = normalized_matrix.rename(columns={first_column: "lever_name"})

    required_columns = ["lever_name", *baseline_kpis]
    _validate_columns(normalized_matrix, required_columns, "impact matrix")
    normalized_matrix = normalized_matrix[required_columns].copy()
    for kpi_name in baseline_kpis:
        normalized_matrix[kpi_name] = pd.to_numeric(
            normalized_matrix[kpi_name],
            errors="raise",
        )
    return normalized_matrix


def validate_impact_metadata(
    impact_metadata: pd.DataFrame,
    impact_matrix: pd.DataFrame,
    baseline_kpis: list[str],
    kpi_to_index: dict[str, int],
) -> None:
    """Validate that long-form impact metadata lines up with the wide matrix."""

    unknown_kpis = sorted(set(impact_metadata["KPI"]) - set(baseline_kpis))
    if unknown_kpis:
        raise QuarterlyStateTransitionError(
            f"Impact metadata references unknown KPIs: {unknown_kpis}"
        )

    unknown_levers = sorted(
        set(impact_metadata["lever_name"]) - set(impact_matrix["lever_name"])
    )
    if unknown_levers:
        raise QuarterlyStateTransitionError(
            f"Impact metadata references unknown lever names: {unknown_levers}"
        )

    impact_lookup = impact_matrix.set_index("lever_name")
    mismatched_rows: list[str] = []
    for row in impact_metadata.to_dict("records"):
        matrix_value = float(impact_lookup.loc[str(row["lever_name"]), str(row["KPI"])])
        metadata_value = float(row["numeric_coefficient"])
        if not math.isclose(matrix_value, metadata_value, rel_tol=0.0, abs_tol=1e-9):
            mismatched_rows.append(
                f"{row['lever_name']} -> {row['KPI']} (matrix={matrix_value}, metadata={metadata_value})"
            )
    if mismatched_rows:
        raise QuarterlyStateTransitionError(
            "Impact matrix and long metadata disagree on numeric coefficients:\n"
            + "\n".join(mismatched_rows)
        )

    if impact_metadata["KPI"].map(kpi_to_index).isna().any():
        raise QuarterlyStateTransitionError("Impact metadata contains unmapped KPIs.")


def validate_baseline_alignment(
    baseline_country_scores: pd.DataFrame,
    countries: list[str],
    baseline_kpi_matrix: np.ndarray,
    kpi_to_subpillar_weights: np.ndarray,
    subpillar_weights: np.ndarray,
) -> None:
    """Recompute the baseline composite from KPI scores as a defensive check."""

    subpillar_scores = np.tensordot(
        baseline_kpi_matrix,
        kpi_to_subpillar_weights,
        axes=([1], [0]),
    )
    composite_scores = np.tensordot(subpillar_scores, subpillar_weights, axes=([1], [0]))
    expected = (
        baseline_country_scores.set_index("country").reindex(countries)["composite_score"].to_numpy()
    )
    if not np.allclose(composite_scores, expected, rtol=0.0, atol=1e-6):
        raise QuarterlyStateTransitionError(
            "The baseline composite scores do not recompute cleanly from the KPI export."
        )


def build_rollout_profile(
    start_quarter: str,
    full_effect_quarter: str,
    rollout_pattern: str,
    quarters: int,
) -> np.ndarray:
    """Build a 0-1 implementation profile for one schedule archetype."""

    start_index = parse_relative_quarter(start_quarter)
    full_index = parse_relative_quarter(full_effect_quarter)
    if full_index < start_index:
        raise QuarterlyStateTransitionError(
            "Implementation schedule has full_effect_quarter before start_quarter: "
            f"{start_quarter} -> {full_effect_quarter}"
        )

    quarter_positions = np.arange(quarters, dtype="float64")
    if start_index >= quarters:
        return np.zeros(quarters, dtype="float64")

    ramp_span = max(full_index - start_index + 1, 1)
    progress = np.clip((quarter_positions - start_index + 1) / ramp_span, 0.0, 1.0)
    return shape_rollout_progress(progress, rollout_pattern)


def parse_relative_quarter(relative_quarter: str) -> int:
    """Convert Y1_Q1 style labels into zero-based quarter indexes."""

    match = re.fullmatch(r"Y(\d+)_Q([1-4])", str(relative_quarter).strip())
    if match is None:
        raise QuarterlyStateTransitionError(
            f"Unsupported relative quarter label '{relative_quarter}'."
        )
    year_number = int(match.group(1))
    quarter_number = int(match.group(2))
    return ((year_number - 1) * 4) + (quarter_number - 1)


def shape_rollout_progress(progress: np.ndarray, rollout_pattern: str) -> np.ndarray:
    """Apply a rollout shape to a normalized 0-1 implementation progress vector."""

    smooth = smoothstep(progress)

    if rollout_pattern == "front_loaded_then_s_curve":
        shaped = np.sqrt(progress)
    elif rollout_pattern == "front_loaded_then_decay_if_retention_weak":
        shaped = progress ** 0.55
    elif rollout_pattern == "slow_start_then_s_curve":
        shaped = smooth
    elif rollout_pattern == "back_loaded":
        shaped = progress**2.0
    elif rollout_pattern == "pilot_to_scale_s_curve":
        shaped = (0.15 * progress) + (0.85 * smooth)
    elif rollout_pattern == "lumpy_contract_driven":
        shaped = (
            0.25 * (progress > 0.0).astype(float)
            + 0.35 * (progress >= 0.40).astype(float)
            + 0.25 * (progress >= 0.75).astype(float)
            + 0.15 * (progress >= 1.00).astype(float)
        )
    else:
        raise QuarterlyStateTransitionError(
            f"Unknown rollout pattern '{rollout_pattern}'."
        )
    return np.clip(shaped, 0.0, 1.0)


def build_effect_profile(
    adoption_profile: np.ndarray,
    lag_quarters: int,
    ramp_type: str,
    quarters: int,
) -> np.ndarray:
    """Combine implementation rollout with KPI-response lag into one level path."""

    adoption_increments = np.diff(np.concatenate(([0.0], adoption_profile)))
    effect_profile = np.zeros(quarters, dtype="float64")

    for quarter_index, increment in enumerate(adoption_increments):
        if increment <= 0.0:
            continue
        offsets = np.arange(quarters - quarter_index, dtype="float64")
        response_curve = build_response_curve(
            offsets=offsets,
            lag_quarters=lag_quarters,
            ramp_type=ramp_type,
        )
        effect_profile[quarter_index:] += increment * response_curve

    return np.clip(effect_profile, 0.0, 1.0)


def build_response_curve(offsets: np.ndarray, lag_quarters: int, ramp_type: str) -> np.ndarray:
    """Build the cumulative KPI response after one unit of implementation arrives."""

    if ramp_type not in RESPONSE_WINDOW_BY_RAMP:
        raise QuarterlyStateTransitionError(f"Unknown ramp type '{ramp_type}'.")

    window = RESPONSE_WINDOW_BY_RAMP[ramp_type]
    progress = np.clip((offsets - lag_quarters + 1.0) / window, 0.0, 1.0)
    smooth = smoothstep(progress)

    if ramp_type == "front_loaded_then_s_curve":
        response = progress ** 0.65
    elif ramp_type == "front_loaded_then_decay_if_retention_weak":
        response = np.where(progress < 1.0, progress ** 0.60, 0.95)
    elif ramp_type == "slow_start_then_s_curve":
        response = smooth
    elif ramp_type == "back_loaded":
        response = progress**2.0
    elif ramp_type == "pilot_to_scale_s_curve":
        response = (0.10 * progress) + (0.90 * smooth)
    elif ramp_type == "lumpy_contract_driven":
        response = (
            0.35 * (progress > 0.0).astype(float)
            + 0.35 * (progress >= 0.45).astype(float)
            + 0.20 * (progress >= 0.75).astype(float)
            + 0.10 * (progress >= 1.00).astype(float)
        )
    else:
        raise QuarterlyStateTransitionError(f"Unknown ramp type '{ramp_type}'.")

    return np.clip(response, 0.0, 1.0)


def smoothstep(progress: np.ndarray) -> np.ndarray:
    """Smooth cubic interpolation on a clipped 0-1 input."""

    clipped_progress = np.clip(progress, 0.0, 1.0)
    return clipped_progress * clipped_progress * (3.0 - (2.0 * clipped_progress))


def build_competitor_drift_priors(
    competitor_drift: pd.DataFrame,
    baseline_kpis: list[str],
) -> pd.DataFrame:
    """Explode cluster KPI lists and convert priors into quarterly drift bands."""

    baseline_kpi_set = set(baseline_kpis)
    drift_records: list[dict[str, object]] = []

    for row in competitor_drift.to_dict("records"):
        cluster_name = str(row["cluster"]).strip()
        if cluster_name not in DRIFT_CLUSTER_INTENSITY:
            raise QuarterlyStateTransitionError(
                f"Unknown competitor drift cluster '{cluster_name}'."
            )

        kpi_names = [
            DRIFT_KPI_ALIASES.get(kpi_name.strip(), kpi_name.strip())
            for kpi_name in str(row["kpi"]).split(";")
            if kpi_name.strip()
        ]
        missing_kpis = sorted(set(kpi_names) - baseline_kpi_set)
        if missing_kpis:
            raise QuarterlyStateTransitionError(
                f"Competitor drift prior references KPIs outside the baseline set: {missing_kpis}"
            )

        low_rate = drift_anchor_to_quarterly_rate(
            anchor_text=str(row["drift_low"]),
            cluster_name=cluster_name,
            confidence=str(row["confidence"]),
            scenario_level="low",
        )
        base_rate = drift_anchor_to_quarterly_rate(
            anchor_text=str(row["drift_base"]),
            cluster_name=cluster_name,
            confidence=str(row["confidence"]),
            scenario_level="base",
        )
        high_rate = drift_anchor_to_quarterly_rate(
            anchor_text=str(row["drift_high"]),
            cluster_name=cluster_name,
            confidence=str(row["confidence"]),
            scenario_level="high",
        )
        low_rate, base_rate, high_rate = sorted([low_rate, base_rate, high_rate])

        for kpi_name in kpi_names:
            drift_records.append(
                {
                    "cluster": cluster_name,
                    "kpi": kpi_name,
                    "low_rate": low_rate,
                    "base_rate": base_rate,
                    "high_rate": high_rate,
                }
            )

    return pd.DataFrame(drift_records)


def drift_anchor_to_quarterly_rate(
    anchor_text: str,
    cluster_name: str,
    confidence: str,
    scenario_level: str,
) -> float:
    """Convert textual cluster drift priors into small quarterly KPI-point rates."""

    anchor_magnitude = parse_drift_anchor(anchor_text)
    confidence_factor = DRIFT_CONFIDENCE_FACTOR.get(
        str(confidence).strip().lower(),
        0.90,
    )
    cluster_intensity = DRIFT_CLUSTER_INTENSITY[cluster_name]
    scenario_multiplier = DRIFT_SCENARIO_MULTIPLIER[scenario_level]
    anchor_adjustment = 0.85 + (0.35 * anchor_magnitude)
    return float(
        BASE_DRIFT_RATE_POINTS
        * cluster_intensity
        * confidence_factor
        * scenario_multiplier
        * anchor_adjustment
    )


def parse_drift_anchor(anchor_text: str) -> float:
    """Parse a free-text drift prior into a bounded 0-1 magnitude proxy."""

    normalized_text = str(anchor_text).strip().lower()
    if not normalized_text or normalized_text == "nan":
        return 0.50

    percent_values = [
        float(value) / 100.0
        for value in re.findall(r"(\d+(?:\.\d+)?)\s*%", normalized_text)
    ]
    if len(percent_values) >= 2 and (
        (" from " in normalized_text and " to " in normalized_text)
        or " versus " in normalized_text
        or " vs " in normalized_text
    ):
        return min(abs(percent_values[-1] - percent_values[0]), 1.0)
    if percent_values:
        return min(max(percent_values[-1], 0.0), 1.0)

    ratio_values = [
        float(value)
        for value in re.findall(r"(\d+(?:\.\d+)?)\s*x", normalized_text)
    ]
    if ratio_values:
        ratio_value = max(ratio_values)
        return min(max((ratio_value - 1.0) / 2.0, 0.0), 1.0)

    number_values = [
        float(value)
        for value in re.findall(r"(?<![A-Za-z])(\d+(?:\.\d+)?)", normalized_text)
    ]
    if len(number_values) >= 2 and (
        (" from " in normalized_text and " to " in normalized_text)
        or " versus " in normalized_text
        or " vs " in normalized_text
    ):
        first_value = number_values[0]
        last_value = number_values[-1]
        denominator = max(abs(first_value), abs(last_value), 1.0)
        return min(abs(last_value - first_value) / denominator, 1.0)
    if number_values:
        return min(math.log10(max(number_values) + 1.0) / 6.0, 1.0)

    return 0.50


def map_countries_to_clusters(countries: list[str]) -> dict[str, str]:
    """Map the baseline countries onto the explicit competitor-drift clusters."""

    missing_countries = sorted(set(countries) - set(COUNTRY_CLUSTER_MAP))
    if missing_countries:
        raise QuarterlyStateTransitionError(
            "No cluster mapping was defined for these countries: "
            f"{missing_countries}"
        )
    return {country: COUNTRY_CLUSTER_MAP[country] for country in countries}


def sample_country_drift_rates(
    inputs: SimulationInputs,
    canada_country: str,
    draws: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample quarterly drift rates for competitor countries by cluster and KPI."""

    drift_rates = np.zeros(
        (draws, len(inputs.countries), len(inputs.kpis)),
        dtype="float64",
    )

    for prior in inputs.drift_priors.to_dict("records"):
        sampled_rates = rng.triangular(
            float(prior["low_rate"]),
            float(prior["base_rate"]),
            float(prior["high_rate"]),
            size=draws,
        )
        kpi_index = inputs.kpi_to_index[str(prior["kpi"])]
        for country_index, country_name in enumerate(inputs.countries):
            if country_name == canada_country:
                continue
            if inputs.country_clusters[country_name] == str(prior["cluster"]):
                drift_rates[:, country_index, kpi_index] = sampled_rates

    return drift_rates


def build_canada_policy_shift(
    inputs: SimulationInputs,
    active_recommendations: tuple[str, ...],
    draws: int,
    quarters: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Build the Canada-only policy shift tensor for one scenario."""

    active_metadata = inputs.impact_metadata.loc[
        inputs.impact_metadata["recommendation_id"].isin(active_recommendations)
    ].reset_index(drop=True)
    policy_shift = np.zeros((draws, quarters, len(inputs.kpis)), dtype="float64")
    if active_metadata.empty:
        return policy_shift

    effect_multiplier_samples = sample_effect_multipliers(
        active_metadata=active_metadata,
        effect_calibration=inputs.effect_calibration,
        draws=draws,
        rng=rng,
    )
    lag_samples = sample_lag_quarters(
        active_metadata=active_metadata,
        lag_calibration=inputs.lag_calibration,
        draws=draws,
        rng=rng,
    )

    for metadata_index, row in enumerate(active_metadata.to_dict("records")):
        schedule_profile = inputs.schedule_profiles[str(row["calibration_lag_lever_id"])]
        base_shift_points = float(row["numeric_coefficient"]) * CLIP_MAX_SCORE
        shift_draws = base_shift_points * effect_multiplier_samples[metadata_index]
        sampled_lags = lag_samples[metadata_index]
        kpi_index = int(row["kpi_index"])
        ramp_type = str(row["ramp_type"])

        for lag_value in np.unique(sampled_lags):
            lag_mask = sampled_lags == lag_value
            effect_profile = build_effect_profile(
                adoption_profile=schedule_profile,
                lag_quarters=int(lag_value),
                ramp_type=ramp_type,
                quarters=quarters,
            )
            policy_shift[lag_mask, :, kpi_index] += (
                shift_draws[lag_mask, np.newaxis] * effect_profile[np.newaxis, :]
            )

    return policy_shift


def sample_effect_multipliers(
    active_metadata: pd.DataFrame,
    effect_calibration: pd.DataFrame,
    draws: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample multiplicative effect-size uncertainty around the calibrated base."""

    effect_lookup = effect_calibration.set_index("lever_id")
    multiplier_samples = np.ones((len(active_metadata), draws), dtype="float64")

    for metadata_index, row in enumerate(active_metadata.to_dict("records")):
        effect_row = effect_lookup.loc[str(row["calibration_effect_lever_id"])]
        confidence_label = str(effect_row["confidence"]).strip().lower()
        band_width = EFFECT_CONFIDENCE_BAND_WIDTH.get(confidence_label, 0.25)
        multiplier_samples[metadata_index, :] = rng.triangular(
            1.0 - band_width,
            1.0,
            1.0 + band_width,
            size=draws,
        )

    return multiplier_samples


def sample_lag_quarters(
    active_metadata: pd.DataFrame,
    lag_calibration: pd.DataFrame,
    draws: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample integer lag draws using the low/base/high lag calibration ranges."""

    lag_lookup = lag_calibration.set_index("lever_id")
    lag_samples = np.zeros((len(active_metadata), draws), dtype="int64")

    for metadata_index, row in enumerate(active_metadata.to_dict("records")):
        lag_row = lag_lookup.loc[str(row["calibration_lag_lever_id"])]
        left, mode, right = lag_sampling_bounds(
            lag_class=str(row["lag_class"]),
            selected_lag=int(row["lag_quarters"]),
            lag_row=lag_row,
        )
        if left == right:
            lag_samples[metadata_index, :] = int(left)
            continue
        lag_samples[metadata_index, :] = np.rint(
            rng.triangular(left, mode, right, size=draws)
        ).astype("int64")

    return lag_samples


def lag_sampling_bounds(
    lag_class: str,
    selected_lag: int,
    lag_row: pd.Series,
) -> tuple[int, int, int]:
    """Respect the lag class while still sampling inside the calibrated ranges."""

    low_lag = int(lag_row["lag_quarters_low"])
    base_lag = int(lag_row["lag_quarters_base"])
    high_lag = int(lag_row["lag_quarters_high"])
    normalized_lag_class = str(lag_class).strip().lower()

    if normalized_lag_class == "immediate":
        left, mode, right = low_lag, selected_lag, max(base_lag, selected_lag)
    elif normalized_lag_class == "medium":
        left, mode, right = low_lag, selected_lag, high_lag
    elif normalized_lag_class == "long":
        left, mode, right = min(base_lag, selected_lag), selected_lag, high_lag
    else:
        raise QuarterlyStateTransitionError(f"Unknown lag class '{lag_class}'.")

    left = min(left, mode)
    right = max(right, mode)
    return int(left), int(mode), int(right)


def compute_country_ranks(composite_scores: np.ndarray, countries: list[str]) -> np.ndarray:
    """Rank countries within each draw using composite score descending."""

    alphabetical_order = {
        country_name: index for index, country_name in enumerate(sorted(countries))
    }
    tie_break = np.array(
        [alphabetical_order[country_name] for country_name in countries],
        dtype="float64",
    )
    sort_key = composite_scores - (tie_break[np.newaxis, :] * 1e-12)
    order = np.argsort(-sort_key, axis=1, kind="mergesort")
    ranks = np.empty_like(order, dtype="int64")
    row_indexes = np.arange(composite_scores.shape[0])[:, np.newaxis]
    ranks[row_indexes, order] = np.arange(1, composite_scores.shape[1] + 1)
    return ranks.astype("float64")


def build_country_summary_frame(
    scenario_name: str,
    quarter_index: int,
    quarter_label: str,
    countries: list[str],
    pillars: list[str],
    subpillars: list[str],
    composite_scores: np.ndarray,
    ranks: np.ndarray,
    pillar_scores: np.ndarray,
    subpillar_scores: np.ndarray,
) -> pd.DataFrame:
    """Aggregate one quarter of country metrics into median and uncertainty rows."""

    composite_quantiles = np.percentile(composite_scores, [10, 50, 90], axis=0)
    rank_quantiles = np.percentile(ranks, [10, 50, 90], axis=0)
    pillar_medians = np.percentile(pillar_scores, 50, axis=0)
    subpillar_medians = np.percentile(subpillar_scores, 50, axis=0)

    summary_frame = pd.DataFrame(
        {
            "scenario": scenario_name,
            "quarter_index": quarter_index,
            "quarter": quarter_label,
            "country": countries,
            "composite_score_p10": composite_quantiles[0],
            "composite_score_median": composite_quantiles[1],
            "composite_score_p90": composite_quantiles[2],
            "rank_p10": rank_quantiles[0],
            "rank_median": rank_quantiles[1],
            "rank_p90": rank_quantiles[2],
        }
    )

    for pillar_index, pillar_name in enumerate(pillars):
        export_name = PILLAR_EXPORT_COLUMNS[pillar_name]
        summary_frame[export_name] = pillar_medians[:, pillar_index]

    for subpillar_index, subpillar_name in enumerate(subpillars):
        export_name = SUBPILLAR_EXPORT_COLUMNS[subpillar_name]
        summary_frame[export_name] = subpillar_medians[:, subpillar_index]

    return summary_frame


def build_canada_kpi_frame(
    scenario_name: str,
    quarter_index: int,
    quarter_label: str,
    kpi_metadata: pd.DataFrame,
    canada_kpi_scores: np.ndarray,
) -> pd.DataFrame:
    """Aggregate one quarter of Canada KPI trajectories."""

    canada_quantiles = np.percentile(canada_kpi_scores, [10, 50, 90], axis=0)
    metadata = kpi_metadata[["kpi_order", "pillar", "subpillar", "kpi"]].copy()
    metadata.insert(0, "quarter", quarter_label)
    metadata.insert(0, "quarter_index", quarter_index)
    metadata.insert(0, "scenario", scenario_name)
    metadata["kpi_score_p10"] = canada_quantiles[0]
    metadata["kpi_score_median"] = canada_quantiles[1]
    metadata["kpi_score_p90"] = canada_quantiles[2]
    return metadata


def build_quarter_labels(start_quarter: str, quarters: int) -> list[str]:
    """Create contiguous quarterly labels like 2026Q1."""

    return [str(period) for period in pd.period_range(start=start_quarter, periods=quarters, freq="Q")]


def sort_export_frame(frame: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Sort one export using the declared scenario order where present."""

    sortable_frame = frame.copy()
    if "scenario" in sortable_frame.columns:
        scenario_order = {scenario_name: index for index, scenario_name in enumerate(SCENARIO_DEFINITIONS)}
        sortable_frame["scenario_sort_key"] = sortable_frame["scenario"].map(scenario_order)
        by = ["scenario_sort_key", *[column_name for column_name in by if column_name != "scenario"]]
    sortable_frame = sortable_frame.sort_values(by).reset_index(drop=True)
    return sortable_frame.drop(columns=["scenario_sort_key"], errors="ignore")


def _validate_columns(frame: pd.DataFrame, required_columns: list[str], frame_name: str) -> None:
    missing_columns = sorted(set(required_columns) - set(frame.columns))
    if missing_columns:
        raise QuarterlyStateTransitionError(
            f"{frame_name} is missing required columns: {missing_columns}"
        )


def build_argument_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for quarterly scenario simulation."""

    parser = argparse.ArgumentParser(
        description="Run the quarterly AI competitiveness simulation across all scenarios."
    )
    parser.add_argument(
        "--baseline-country",
        default=str(DEFAULT_BASELINE_COUNTRY_PATH),
        help="Path to baseline_country_scores.csv.",
    )
    parser.add_argument(
        "--baseline-kpis",
        default=str(DEFAULT_BASELINE_KPI_PATH),
        help="Path to baseline_kpi_scores.csv.",
    )
    parser.add_argument(
        "--impact-matrix",
        default=str(DEFAULT_IMPACT_MATRIX_PATH),
        help="Path to impact_matrix.csv.",
    )
    parser.add_argument(
        "--impact-metadata",
        default=str(DEFAULT_IMPACT_METADATA_PATH),
        help="Path to impact_matrix_long.csv.",
    )
    parser.add_argument(
        "--implementation-schedule",
        default=str(DEFAULT_IMPLEMENTATION_SCHEDULE_PATH),
        help="Path to implementation_schedule.csv.",
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
        "--competitor-drift",
        default=str(DEFAULT_COMPETITOR_DRIFT_PATH),
        help="Path to competitor_drift.csv.",
    )
    parser.add_argument(
        "--start-quarter",
        default="2026Q1",
        help="Quarter label used for the first simulated quarter.",
    )
    parser.add_argument(
        "--quarters",
        type=int,
        default=16,
        help="Number of quarters to simulate.",
    )
    parser.add_argument(
        "--draws",
        type=int,
        default=10000,
        help="Monte Carlo draws per scenario.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Base random seed used for reproducible scenario draws.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where the scenario CSV exports will be written.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for the quarterly simulation."""

    parser = build_argument_parser()
    args = parser.parse_args()
    result = run_quarterly_state_transition(
        config=StateTransitionConfig(
            start_quarter=args.start_quarter,
            quarters=args.quarters,
            draws=args.draws,
            random_seed=args.random_seed,
        ),
        baseline_country_path=args.baseline_country,
        baseline_kpi_path=args.baseline_kpis,
        impact_matrix_path=args.impact_matrix,
        impact_metadata_path=args.impact_metadata,
        implementation_schedule_path=args.implementation_schedule,
        calibration_effects_path=args.calibration_effects,
        calibration_lags_path=args.calibration_lags,
        competitor_drift_path=args.competitor_drift,
        output_dir=args.output_dir,
    )
    for export_name, export_path in result.export_paths.items():
        print(f"{export_name}: {export_path}")


if __name__ == "__main__":
    main()
