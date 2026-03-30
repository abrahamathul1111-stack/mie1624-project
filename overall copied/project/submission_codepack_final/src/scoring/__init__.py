"""Scoring utilities for competitiveness baselines and policy impacts."""

from .baseline_scoring import (
    compute_baseline_scores,
    compute_weighted_index,
    normalize_kpi_frame,
    prepare_weight_vector,
)
from .baseline_reproduction import (
    BaselineReproductionError,
    BaselineReproductionResult,
    reproduce_baseline,
)
from .impact_matrix import (
    build_impact_matrix,
    combine_recommendation_impacts,
    set_recommendation_impacts,
)
from .policy_impact_matrix import (
    PolicyImpactMatrixError,
    PolicyImpactMatrixResult,
    build_policy_impact_artifacts,
    strength_to_numeric_coefficient,
    validate_simulation_kpis,
)

__all__ = [
    "build_impact_matrix",
    "combine_recommendation_impacts",
    "compute_baseline_scores",
    "compute_weighted_index",
    "BaselineReproductionError",
    "BaselineReproductionResult",
    "PolicyImpactMatrixError",
    "PolicyImpactMatrixResult",
    "normalize_kpi_frame",
    "prepare_weight_vector",
    "build_policy_impact_artifacts",
    "reproduce_baseline",
    "set_recommendation_impacts",
    "strength_to_numeric_coefficient",
    "validate_simulation_kpis",
]
