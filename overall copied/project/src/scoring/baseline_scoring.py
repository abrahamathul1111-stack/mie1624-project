"""Baseline scoring helpers for AI competitiveness KPI tables.

The functions in this module are intentionally small so they can be called
directly from notebooks, scripts, or dashboard data pipelines.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd


def normalize_min_max(series: pd.Series) -> pd.Series:
    """Scale a numeric series to the ``0-1`` range.

    Constant columns return all zeros because they do not differentiate entities.
    """

    numeric_series = pd.to_numeric(series, errors="coerce").fillna(0.0)
    min_value = numeric_series.min()
    max_value = numeric_series.max()

    if min_value == max_value:
        return pd.Series(0.0, index=series.index, dtype="float64")

    return (numeric_series - min_value) / (max_value - min_value)


def normalize_kpi_frame(kpi_frame: pd.DataFrame) -> pd.DataFrame:
    """Min-max normalize each KPI column independently."""

    return kpi_frame.apply(normalize_min_max, axis=0)


def prepare_weight_vector(weights: pd.Series | Mapping[str, float]) -> pd.Series:
    """Convert raw weights into a normalized pandas ``Series`` that sums to one."""

    weight_vector = pd.Series(weights, dtype="float64")
    if weight_vector.empty:
        raise ValueError("At least one KPI weight is required.")

    weight_total = weight_vector.sum()
    if weight_total == 0:
        raise ValueError("KPI weights must sum to a non-zero value.")

    return weight_vector / weight_total


def compute_weighted_index(
    kpi_frame: pd.DataFrame, weights: pd.Series | Mapping[str, float]
) -> pd.Series:
    """Compute a weighted index from already aligned KPI columns.

    This is useful when KPIs are already normalized and you only need the final
    competitiveness score.
    """

    weight_vector = prepare_weight_vector(weights)
    aligned_kpis = kpi_frame.reindex(columns=weight_vector.index).fillna(0.0)
    return aligned_kpis.mul(weight_vector, axis=1).sum(axis=1)


def compute_baseline_scores(
    kpi_frame: pd.DataFrame, weights: pd.Series | Mapping[str, float]
) -> pd.DataFrame:
    """Normalize KPI columns, compute weighted scores, and return a ranked table.

    The input DataFrame should use rows for entities and columns for KPI values.
    The DataFrame index is preserved and treated as the entity label.
    """

    normalized_kpis = normalize_kpi_frame(kpi_frame)
    baseline_score = compute_weighted_index(normalized_kpis, weights)

    results = normalized_kpis.copy()
    results.insert(0, "baseline_score", baseline_score)
    results.insert(
        1,
        "rank",
        results["baseline_score"].rank(method="dense", ascending=False).astype(int),
    )

    return results.sort_values("baseline_score", ascending=False)
