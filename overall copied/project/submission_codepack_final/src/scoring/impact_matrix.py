"""Helpers for building and combining recommendation impact matrices."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


def build_impact_matrix(
    recommendations: Sequence[str], kpis: Sequence[str], default_impact: float = 0.0
) -> pd.DataFrame:
    """Create a zero-filled recommendation-to-KPI matrix.

    Each row represents a policy recommendation and each column represents the
    additive effect on a KPI when the recommendation is fully adopted.
    """

    matrix = pd.DataFrame(
        default_impact,
        index=pd.Index(recommendations, name="recommendation"),
        columns=list(kpis),
        dtype="float64",
    )
    return matrix


def set_recommendation_impacts(
    impact_matrix: pd.DataFrame, recommendation: str, impacts: Mapping[str, float]
) -> pd.DataFrame:
    """Return a copy of an impact matrix with one recommendation row updated."""

    updated_matrix = impact_matrix.copy()
    if recommendation not in updated_matrix.index:
        updated_matrix.loc[recommendation] = 0.0

    for kpi_name, effect_size in impacts.items():
        if kpi_name not in updated_matrix.columns:
            raise KeyError(f"Unknown KPI column: {kpi_name}")
        updated_matrix.loc[recommendation, kpi_name] = float(effect_size)

    return updated_matrix


def combine_recommendation_impacts(
    impact_matrix: pd.DataFrame, adoption_levels: Mapping[str, float]
) -> pd.Series:
    """Aggregate adoption-weighted recommendation impacts into a KPI delta vector."""

    if not adoption_levels:
        return pd.Series(0.0, index=impact_matrix.columns, dtype="float64")

    adoption_series = pd.Series(adoption_levels, dtype="float64")
    missing_recommendations = adoption_series.index.difference(impact_matrix.index)
    if not missing_recommendations.empty:
        raise KeyError(
            f"Missing recommendation rows in impact matrix: {missing_recommendations.tolist()}"
        )

    return impact_matrix.loc[adoption_series.index].mul(adoption_series, axis=0).sum(axis=0)
