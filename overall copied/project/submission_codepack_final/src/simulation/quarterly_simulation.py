"""Quarterly simulation utilities for AI competitiveness policy scenarios."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.scoring.baseline_scoring import compute_weighted_index, prepare_weight_vector
from src.scoring.impact_matrix import combine_recommendation_impacts


@dataclass(slots=True)
class QuarterlySimulationSpec:
    """Configuration for a quarter-by-quarter policy rollout simulation."""

    start_quarter: str = "2026Q1"
    periods: int = 12
    impact_floor: float = 0.0
    impact_ceiling: float = 1.0


def build_quarter_index(start_quarter: str, periods: int) -> pd.PeriodIndex:
    """Create a contiguous quarterly index for scenario modeling."""

    return pd.period_range(start=start_quarter, periods=periods, freq="Q")


def expand_adoption_plan(
    adoption_plan: pd.DataFrame, quarter_index: pd.PeriodIndex
) -> pd.DataFrame:
    """Expand a recommendation rollout plan into quarter-level adoption shares.

    Expected columns are:
    - ``recommendation``
    - ``start_quarter``
    - ``ramp_quarters``
    - ``max_adoption``
    - optional ``implementation_lag``
    """

    if adoption_plan is None or adoption_plan.empty:
        return pd.DataFrame(columns=["quarter", "recommendation", "adoption_share"])

    expanded_rows: list[dict[str, object]] = []

    for plan_row in adoption_plan.to_dict(orient="records"):
        start_quarter = pd.Period(str(plan_row["start_quarter"]), freq="Q")
        ramp_quarters = max(1, int(plan_row.get("ramp_quarters", 1)))
        implementation_lag = max(0, int(plan_row.get("implementation_lag", 0)))
        max_adoption = float(plan_row.get("max_adoption", 1.0))

        for quarter in quarter_index:
            elapsed_quarters = quarter.ordinal - start_quarter.ordinal - implementation_lag + 1
            if elapsed_quarters <= 0:
                adoption_share = 0.0
            else:
                adoption_share = min(max_adoption, max_adoption * elapsed_quarters / ramp_quarters)

            expanded_rows.append(
                {
                    "quarter": str(quarter),
                    "recommendation": plan_row["recommendation"],
                    "adoption_share": float(adoption_share),
                }
            )

    return pd.DataFrame(expanded_rows)


def simulate_quarterly_path(
    baseline_kpis: pd.DataFrame,
    weights: pd.Series | dict[str, float],
    impact_matrix: pd.DataFrame,
    adoption_plan: pd.DataFrame,
    spec: QuarterlySimulationSpec | None = None,
) -> pd.DataFrame:
    """Project KPI and competitiveness-score trajectories over multiple quarters.

    ``baseline_kpis`` should contain one row per entity and normalized KPI columns.
    Recommendation impacts are treated as additive shifts in the same normalized space.
    """

    simulation_spec = spec or QuarterlySimulationSpec()
    weight_vector = prepare_weight_vector(weights)
    baseline_frame = baseline_kpis.reindex(columns=weight_vector.index).fillna(0.0).astype(float)
    baseline_score = compute_weighted_index(baseline_frame, weight_vector)
    quarter_index = build_quarter_index(simulation_spec.start_quarter, simulation_spec.periods)
    expanded_plan = expand_adoption_plan(adoption_plan, quarter_index)
    entity_column = baseline_frame.index.name or "entity"
    baseline_frame.index = baseline_frame.index.rename(entity_column)

    quarterly_results: list[pd.DataFrame] = []
    zero_delta = pd.Series(0.0, index=weight_vector.index, dtype="float64")

    for quarter in quarter_index:
        quarter_plan = expanded_plan.loc[expanded_plan["quarter"] == str(quarter)]
        adoption_levels = (
            quarter_plan.set_index("recommendation")["adoption_share"].to_dict()
            if not quarter_plan.empty
            else {}
        )
        impact_delta = (
            combine_recommendation_impacts(impact_matrix, adoption_levels).reindex(
                weight_vector.index, fill_value=0.0
            )
            if adoption_levels
            else zero_delta
        )

        simulated_kpis = baseline_frame.add(impact_delta, axis=1).clip(
            lower=simulation_spec.impact_floor,
            upper=simulation_spec.impact_ceiling,
        )
        simulated_score = compute_weighted_index(simulated_kpis, weight_vector)

        quarter_frame = simulated_kpis.copy()
        quarter_frame.insert(0, "baseline_score", baseline_score)
        quarter_frame.insert(1, "simulated_score", simulated_score)
        quarter_frame.insert(2, "score_change", simulated_score - baseline_score)
        quarter_frame = quarter_frame.reset_index().rename(
            columns={entity_column: "entity", "index": "entity"}
        )
        quarter_frame.insert(1, "quarter", str(quarter))
        quarterly_results.append(quarter_frame)

    return pd.concat(quarterly_results, ignore_index=True)
