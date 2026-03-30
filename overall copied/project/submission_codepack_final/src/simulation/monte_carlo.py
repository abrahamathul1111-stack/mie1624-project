"""Monte Carlo simulation helpers for uncertainty-aware policy analysis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.simulation.quarterly_simulation import QuarterlySimulationSpec, simulate_quarterly_path


@dataclass(slots=True)
class MonteCarloConfig:
    """Configuration for repeated stochastic simulation runs."""

    draws: int = 250
    baseline_noise_scale: float = 0.02
    impact_noise_scale: float = 0.05
    random_seed: int | None = 42


def summarize_monte_carlo_runs(simulation_runs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw Monte Carlo draws into summary statistics by entity and quarter."""

    return (
        simulation_runs.groupby(["entity", "quarter"], as_index=False)
        .agg(
            mean_score=("simulated_score", "mean"),
            median_score=("simulated_score", "median"),
            p10_score=("simulated_score", lambda values: values.quantile(0.10)),
            p90_score=("simulated_score", lambda values: values.quantile(0.90)),
            mean_change=("score_change", "mean"),
        )
        .sort_values(["entity", "quarter"])
        .reset_index(drop=True)
    )


def run_monte_carlo(
    baseline_kpis: pd.DataFrame,
    weights: pd.Series | dict[str, float],
    impact_matrix: pd.DataFrame,
    adoption_plan: pd.DataFrame,
    simulation_spec: QuarterlySimulationSpec | None = None,
    config: MonteCarloConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run repeated scenario draws and return both summary and raw simulation outputs.

    Gaussian noise is applied in normalized KPI space, which keeps the starter
    implementation easy to reason about and extend.
    """

    monte_carlo_config = config or MonteCarloConfig()
    rng = np.random.default_rng(monte_carlo_config.random_seed)
    baseline_frame = baseline_kpis.astype(float)
    impact_frame = impact_matrix.astype(float)

    run_frames: list[pd.DataFrame] = []

    for draw in range(monte_carlo_config.draws):
        baseline_noise = pd.DataFrame(
            rng.normal(
                loc=0.0,
                scale=monte_carlo_config.baseline_noise_scale,
                size=baseline_frame.shape,
            ),
            index=baseline_frame.index,
            columns=baseline_frame.columns,
        )
        impact_noise = pd.DataFrame(
            rng.normal(
                loc=0.0,
                scale=monte_carlo_config.impact_noise_scale,
                size=impact_frame.shape,
            ),
            index=impact_frame.index,
            columns=impact_frame.columns,
        )

        sampled_baseline = baseline_frame.add(baseline_noise).clip(lower=0.0, upper=1.0)
        sampled_impacts = impact_frame.add(impact_noise)

        simulation_run = simulate_quarterly_path(
            baseline_kpis=sampled_baseline,
            weights=weights,
            impact_matrix=sampled_impacts,
            adoption_plan=adoption_plan,
            spec=simulation_spec,
        )
        simulation_run.insert(0, "draw", draw)
        run_frames.append(simulation_run)

    raw_runs = pd.concat(run_frames, ignore_index=True)
    summary = summarize_monte_carlo_runs(raw_runs)
    return summary, raw_runs
