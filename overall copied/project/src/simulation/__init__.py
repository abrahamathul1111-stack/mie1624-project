"""Simulation engines for deterministic and stochastic policy scenarios."""

from .monte_carlo import MonteCarloConfig, run_monte_carlo, summarize_monte_carlo_runs
from .quarterly_simulation import (
    QuarterlySimulationSpec,
    build_quarter_index,
    expand_adoption_plan,
    simulate_quarterly_path,
)

__all__ = [
    "MonteCarloConfig",
    "QuarterlyStateTransitionError",
    "QuarterlySimulationSpec",
    "RecommendationAttributionError",
    "SCENARIO_DEFINITIONS",
    "SimulationInputs",
    "StateTransitionConfig",
    "StateTransitionResult",
    "build_quarter_index",
    "build_kpi_benchmarks",
    "expand_adoption_plan",
    "export_recommendation_attribution",
    "load_simulation_inputs",
    "run_monte_carlo",
    "run_quarterly_state_transition",
    "simulate_quarterly_path",
    "summarize_monte_carlo_runs",
]


def __getattr__(name: str):
    if name in {
        "QuarterlyStateTransitionError",
        "SCENARIO_DEFINITIONS",
        "SimulationInputs",
        "StateTransitionConfig",
        "StateTransitionResult",
        "load_simulation_inputs",
        "run_quarterly_state_transition",
    }:
        from . import state_transition as state_transition_module

        return getattr(state_transition_module, name)
    if name in {
        "RecommendationAttributionError",
        "build_kpi_benchmarks",
        "export_recommendation_attribution",
    }:
        from . import recommendation_attribution as recommendation_attribution_module

        return getattr(recommendation_attribution_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
