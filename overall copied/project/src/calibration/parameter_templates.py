"""Starter parameter tables and assumptions for calibrating simulation inputs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(slots=True)
class SimulationAssumptions:
    """Centralized assumptions that can later be tuned during calibration."""

    start_quarter: str = "2026Q1"
    periods: int = 12
    baseline_noise_scale: float = 0.02
    impact_noise_scale: float = 0.05
    default_ramp_quarters: int = 4
    default_max_adoption: float = 1.0
    default_implementation_lag: int = 0

    def to_dict(self) -> dict[str, float | int | str]:
        """Return assumptions as a plain dictionary for config exports or notebooks."""

        return asdict(self)


def default_weight_table(kpis: Sequence[str]) -> pd.DataFrame:
    """Create an equal-weight starter table that can be edited during calibration."""

    if len(kpis) == 0:
        raise ValueError("At least one KPI name is required to build a weight table.")

    equal_weight = 1.0 / len(kpis)
    return pd.DataFrame({"kpi": list(kpis), "weight": [equal_weight] * len(kpis)})


def default_adoption_plan(
    recommendations: Sequence[str],
    assumptions: SimulationAssumptions | None = None,
) -> pd.DataFrame:
    """Create a simple adoption-plan template for scenario design."""

    scenario_assumptions = assumptions or SimulationAssumptions()
    return pd.DataFrame(
        {
            "recommendation": list(recommendations),
            "start_quarter": [scenario_assumptions.start_quarter] * len(recommendations),
            "ramp_quarters": [scenario_assumptions.default_ramp_quarters]
            * len(recommendations),
            "max_adoption": [scenario_assumptions.default_max_adoption] * len(recommendations),
            "implementation_lag": [
                scenario_assumptions.default_implementation_lag
            ]
            * len(recommendations),
        }
    )
