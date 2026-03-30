"""Helpers for exporting simulation outputs into dashboard-friendly artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _frame_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame into JSON-serializable records."""

    if frame.empty:
        return []

    serializable = frame.copy()
    for column_name in serializable.columns:
        if pd.api.types.is_period_dtype(serializable[column_name]):
            serializable[column_name] = serializable[column_name].astype(str)

    return json.loads(serializable.to_json(orient="records", date_format="iso"))


def _flatten_impact_matrix(impact_matrix: pd.DataFrame) -> pd.DataFrame:
    """Return a record-friendly version of an impact matrix."""

    flattened = impact_matrix.copy().reset_index()
    if "index" in flattened.columns:
        flattened = flattened.rename(
            columns={"index": impact_matrix.index.name or "recommendation"}
        )
    return flattened


def build_dashboard_payload(
    simulation_results: pd.DataFrame,
    impact_matrix: pd.DataFrame,
    monte_carlo_summary: pd.DataFrame | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-ready payload for dashboard applications."""

    flattened_impact_matrix = _flatten_impact_matrix(impact_matrix)
    payload = {
        "metadata": metadata or {},
        "simulation_results": _frame_to_records(simulation_results),
        "impact_matrix": _frame_to_records(flattened_impact_matrix),
        "monte_carlo_summary": _frame_to_records(
            monte_carlo_summary if monte_carlo_summary is not None else pd.DataFrame()
        ),
    }
    return payload


def export_dashboard_bundle(
    simulation_results: pd.DataFrame,
    impact_matrix: pd.DataFrame,
    output_dir: str | Path,
    monte_carlo_summary: pd.DataFrame | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Export CSV and JSON artifacts that a dashboard can read directly."""

    export_path = Path(output_dir).expanduser().resolve()
    export_path.mkdir(parents=True, exist_ok=True)
    flattened_impact_matrix = _flatten_impact_matrix(impact_matrix)
    payload = build_dashboard_payload(
        simulation_results=simulation_results,
        impact_matrix=impact_matrix,
        monte_carlo_summary=monte_carlo_summary,
        metadata=metadata,
    )

    payload_path = export_path / "dashboard_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    simulation_path = export_path / "simulation_results.csv"
    simulation_results.to_csv(simulation_path, index=False)

    impact_path = export_path / "impact_matrix.csv"
    flattened_impact_matrix.to_csv(impact_path, index=False)

    exported_paths = {
        "payload": payload_path,
        "simulation_results": simulation_path,
        "impact_matrix": impact_path,
    }

    if monte_carlo_summary is not None and not monte_carlo_summary.empty:
        monte_carlo_path = export_path / "monte_carlo_summary.csv"
        monte_carlo_summary.to_csv(monte_carlo_path, index=False)
        exported_paths["monte_carlo_summary"] = monte_carlo_path

    return exported_paths


def load_dashboard_payload(payload_path: str | Path) -> dict[str, Any]:
    """Load a dashboard JSON payload from disk."""

    path = Path(payload_path).expanduser().resolve()
    return json.loads(path.read_text(encoding="utf-8"))
