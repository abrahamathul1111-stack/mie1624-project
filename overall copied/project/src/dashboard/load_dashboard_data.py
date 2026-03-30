"""Data loading, validation, and reporting for Phase 6 dashboards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd

from src.dashboard.dashboard_config import A4_DEFAULT_KPIS


EXPECTED_FILES = {
    "dashboard_spec_v1.md": [Path("DOCS") / "DECISIONS" / "dashboard_spec_v1.md"],
    "model_scope_v1.md": [Path("DOCS") / "DECISIONS" / "model_scope_v1.md"],
    "recommendation_kpi_mapping.md": [Path("DOCS") / "DECISIONS" / "recommendation_kpi_mapping.md"],
    "PROBLEM AND RECOMMENDATION 1&2.pptx": [Path("data") / "raw" / "PROBLEM AND RECOMMENDATION 1&2.pptx"],
    "PROBLEM AND RECOMMENDATION 3.pdf": [Path("data") / "raw" / "PROBLEM AND RECOMMENDATION 3.pdf"],
    "MIE1624_Final_Project.pptx": [Path("data") / "raw" / "MIE1624_Final_Project.pptx"],
    "Methodology_Report.docx": [Path("data") / "raw" / "Methodology_Report.docx"],
    "canada_combined_kpi_weights_gaps.csv": [Path("data") / "raw" / "canada_combined_kpi_weights_gaps.csv"],
    "baseline_country_scores.csv": [Path("outputs") / "tables" / "baseline_country_scores.csv"],
    "baseline_kpi_scores.csv": [Path("outputs") / "tables" / "baseline_kpi_scores.csv"],
    "simulation_summary.csv": [Path("outputs") / "tables" / "simulation_summary.csv"],
    "scenario_comparison.csv": [Path("outputs") / "tables" / "scenario_comparison.csv"],
    "country_quarter_scores.csv": [Path("outputs") / "tables" / "country_quarter_scores.csv"],
    "canada_rank_trajectory.csv": [Path("outputs") / "tables" / "canada_rank_trajectory.csv"],
    "canada_kpi_trajectories.csv": [Path("outputs") / "tables" / "canada_kpi_trajectories.csv"],
    "kpi_gap_reduction_by_recommendation.csv": [Path("outputs") / "tables" / "kpi_gap_reduction_by_recommendation.csv"],
    "impact_matrix_long.csv": [Path("outputs") / "tables" / "impact_matrix_long.csv", Path("data") / "processed" / "impact_matrix_long.csv"],
    "impact_matrix_long_validated.csv": [Path("outputs") / "tables" / "impact_matrix_long_validated.csv"],
    "implementation_schedule.csv": [Path("data") / "calibration" / "implementation_schedule.csv"],
    "calibration_effects.csv": [Path("data") / "calibration" / "calibration_effects.csv"],
    "calibration_lags.csv": [Path("data") / "calibration" / "calibration_lags.csv"],
    "success_metrics_tracking.csv": [Path("data") / "processed" / "success_metrics_tracking.csv"],
}

CSV_REQUIRED_COLUMNS = {
    "baseline_country_scores.csv": ["country", "rank", "composite_score", "talent_score", "commercial_ecosystem_score"],
    "baseline_kpi_scores.csv": ["country", "kpi_order", "kpi", "kpi_score"],
    "simulation_summary.csv": ["scenario", "quarter_index", "country", "composite_score_median", "rank_median"],
    "scenario_comparison.csv": ["scenario", "quarter_index", "composite_score_median", "rank_median"],
    "country_quarter_scores.csv": ["scenario", "quarter_index", "country", "rank", "composite_score"],
    "canada_rank_trajectory.csv": ["scenario", "quarter_index", "quarter", "rank_median", "composite_score_median"],
    "canada_kpi_trajectories.csv": ["scenario", "quarter_index", "kpi", "kpi_score_p10", "kpi_score_median", "kpi_score_p90"],
    "kpi_gap_reduction_by_recommendation.csv": [
        "scenario",
        "quarter_index",
        "kpi",
        "benchmark_type",
        "benchmark_score",
        "baseline_canada_score",
        "scenario_canada_score",
        "percent_gap_reduction",
    ],
    "impact_matrix_long.csv": ["recommendation_id", "lever_id", "lever_name", "KPI"],
    "implementation_schedule.csv": ["recommendation_id", "lever_id", "start_quarter", "full_effect_quarter", "rollout_pattern"],
    "calibration_effects.csv": ["recommendation_id", "lever_id", "lever_name", "confidence"],
    "calibration_lags.csv": ["recommendation_id", "lever_id", "ramp_type"],
    "success_metrics_tracking.csv": ["metric_name", "recommendation_id", "current_value", "target_value", "notes"],
}


@dataclass(slots=True)
class DashboardDataBundle:
    """Loaded dashboard data plus availability metadata."""

    project_root: Path
    files: dict[str, Path]
    frames: dict[str, pd.DataFrame]
    unresolved: list[str]
    inventory_rows: list[dict[str, str]]


def _resolve_file(project_root: Path, candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        full_path = (project_root / candidate).resolve()
        if full_path.exists():
            return full_path
    return None


def _parse_numeric_text(value: str | float | int) -> float | None:
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if match is None:
        return None
    return float(match.group(0))


def _parse_target_value(value: str | float | int) -> float | None:
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    if "-" in text:
        parts = [part.strip() for part in text.split("-") if part.strip()]
        nums = [_parse_numeric_text(part) for part in parts]
        nums = [num for num in nums if num is not None]
        if nums:
            return float(sum(nums) / len(nums))
    return _parse_numeric_text(text)


def _validate_columns(frame: pd.DataFrame, required_columns: list[str], file_name: str) -> list[str]:
    missing = sorted(set(required_columns) - set(frame.columns))
    if not missing:
        return []
    return [f"{file_name}: missing column(s): {', '.join(missing)}"]


def load_dashboard_data(project_root: str | Path) -> DashboardDataBundle:
    """Load expected dashboard source files and validate required columns."""

    root = Path(project_root).expanduser().resolve()
    files: dict[str, Path] = {}
    unresolved: list[str] = []
    inventory_rows: list[dict[str, str]] = []
    frames: dict[str, pd.DataFrame] = {}

    for file_name, candidates in EXPECTED_FILES.items():
        resolved = _resolve_file(root, candidates)
        if resolved is None:
            unresolved.append(
                f"Missing required file: {file_name}. Tried: {', '.join(str(path) for path in candidates)}"
            )
            inventory_rows.append(
                {
                    "file": file_name,
                    "status": "missing",
                    "resolved_path": "",
                    "notes": "Not found in expected locations.",
                }
            )
            continue

        files[file_name] = resolved
        if resolved.suffix.lower() == ".csv":
            frame = pd.read_csv(resolved)
            frames[file_name] = frame
            validation_issues = _validate_columns(
                frame,
                CSV_REQUIRED_COLUMNS.get(file_name, []),
                file_name,
            )
            unresolved.extend(validation_issues)
            inventory_rows.append(
                {
                    "file": file_name,
                    "status": "available",
                    "resolved_path": str(resolved.relative_to(root)),
                    "notes": "CSV loaded" if not validation_issues else "; ".join(validation_issues),
                }
            )
        else:
            inventory_rows.append(
                {
                    "file": file_name,
                    "status": "available",
                    "resolved_path": str(resolved.relative_to(root)),
                    "notes": "Narrative/source document available",
                }
            )

    if "impact_matrix_long_validated.csv" not in files:
        unresolved.append(
            "Optional validated impact matrix is unavailable: impact_matrix_long_validated.csv. Using impact_matrix_long.csv instead."
        )

    return DashboardDataBundle(
        project_root=root,
        files=files,
        frames=frames,
        unresolved=unresolved,
        inventory_rows=inventory_rows,
    )


def build_timeline_frame(bundle: DashboardDataBundle) -> pd.DataFrame:
    """Build a timeline frame by joining implementation, effect, and lag references."""

    schedule = bundle.frames.get("implementation_schedule.csv", pd.DataFrame()).copy()
    effects = bundle.frames.get("calibration_effects.csv", pd.DataFrame()).copy()
    lags = bundle.frames.get("calibration_lags.csv", pd.DataFrame()).copy()
    if schedule.empty:
        return schedule

    merged = schedule.merge(
        effects[["recommendation_id", "lever_id", "lever_name"]].drop_duplicates(),
        on=["recommendation_id", "lever_id"],
        how="left",
    )
    merged = merged.merge(
        lags[["recommendation_id", "lever_id", "ramp_type"]].drop_duplicates(),
        on=["recommendation_id", "lever_id"],
        how="left",
    )

    recommendation_label_map = {
        "rec1": "R1",
        "rec2": "R2",
        "rec3": "R3",
    }
    merged["rec_family"] = merged["recommendation_id"].map(recommendation_label_map)
    merged["start_index"] = merged["start_quarter"].map(parse_relative_quarter)
    merged["full_index"] = merged["full_effect_quarter"].map(parse_relative_quarter)
    merged["duration"] = merged["full_index"] - merged["start_index"] + 1
    merged["display_lever"] = merged["lever_name"].fillna(merged["lever_id"])
    return merged.sort_values(["recommendation_id", "lever_id"]).reset_index(drop=True)


def parse_relative_quarter(relative_quarter: str) -> int:
    """Convert Y1_Q1 style labels into quarter index 1..16 for display."""

    match = re.fullmatch(r"Y(\d+)_Q([1-4])", str(relative_quarter).strip())
    if match is None:
        return 1
    year_number = int(match.group(1))
    quarter_number = int(match.group(2))
    return ((year_number - 1) * 4) + quarter_number


def parse_success_metrics(bundle: DashboardDataBundle) -> pd.DataFrame:
    """Parse primary success metric rows and derive numeric fields for bullet cards."""

    success = bundle.frames.get("success_metrics_tracking.csv", pd.DataFrame()).copy()
    if success.empty:
        return success

    success["current_numeric"] = success["current_value"].map(_parse_numeric_text)
    success["target_numeric"] = success["target_value"].map(_parse_target_value)
    success["direction"] = success["recommendation_id"].map(
        {
            "R1": "lower_is_better",
            "R2": "higher_is_better",
            "R3": "higher_is_better",
        }
    )
    success["is_primary_metric"] = success["metric_name"].isin(
        {
            "Core AI team attrition among supported firms",
            "% of subsidized pilots converting to paid commercial contracts",
            "% of credit-subsidized deployments converting to multi-year commercial contracts",
        }
    )
    return success


def select_gap_panel_rows(bundle: DashboardDataBundle, benchmark_type: str = "peer_best") -> pd.DataFrame:
    """Select three recommendation-relevant KPI rows for each recommendation scenario."""

    gap = bundle.frames.get("kpi_gap_reduction_by_recommendation.csv", pd.DataFrame()).copy()
    if gap.empty:
        return gap

    gap = gap.loc[(gap["benchmark_type"] == benchmark_type) & (gap["quarter_index"] == 16)].copy()
    keep_rows: list[pd.DataFrame] = []

    for scenario, kpi_list in A4_DEFAULT_KPIS.items():
        slice_frame = gap.loc[(gap["scenario"] == scenario) & (gap["kpi"].isin(kpi_list))].copy()
        slice_frame["kpi_rank"] = slice_frame["kpi"].map({kpi: index for index, kpi in enumerate(kpi_list)})
        slice_frame = slice_frame.sort_values(["kpi_rank", "percent_gap_reduction"], ascending=[True, False]).head(3)
        keep_rows.append(slice_frame)

    if not keep_rows:
        return pd.DataFrame()
    selected = pd.concat(keep_rows, ignore_index=True)
    return selected.sort_values(["scenario", "kpi_rank"]).drop(columns=["kpi_rank"], errors="ignore")


def build_inventory_markdown(bundle: DashboardDataBundle) -> str:
    """Render a markdown table summarizing discovered dashboard dependencies."""

    lines = [
        "# Dashboard Data Inventory",
        "",
        "| file | status | resolved_path | notes |",
        "|---|---|---|---|",
    ]
    for row in bundle.inventory_rows:
        lines.append(
            f"| {row['file']} | {row['status']} | {row['resolved_path']} | {row['notes']} |"
        )

    lines.extend(
        [
            "",
            "## Validation Summary",
            "",
            f"- Available files: {sum(1 for row in bundle.inventory_rows if row['status'] == 'available')}",
            f"- Missing files: {sum(1 for row in bundle.inventory_rows if row['status'] == 'missing')}",
            f"- Issues logged: {len(bundle.unresolved)}",
        ]
    )
    return "\n".join(lines)


def build_unresolved_markdown(bundle: DashboardDataBundle) -> str:
    """Render unresolved dependency notes with no fabricated values."""

    lines = ["# Dashboard Unresolved Dependencies", ""]
    if not bundle.unresolved:
        lines.append("No unresolved dependencies were detected.")
        return "\n".join(lines)

    lines.append("The following dependencies were missing or partially unavailable during the dashboard build:")
    lines.append("")
    for issue in bundle.unresolved:
        lines.append(f"- {issue}")

    lines.extend(
        [
            "",
            "Notes:",
            "- No modeled values were invented to fill missing dependencies.",
            "- Sections with complete source coverage were still built from available files.",
        ]
    )
    return "\n".join(lines)


def build_notes_markdown(bundle: DashboardDataBundle) -> str:
    """Render implementation notes for the Phase 6 dashboard package."""

    lines = [
        "# Dashboard Build Notes",
        "",
        "## Scope",
        "",
        "- Built Dashboard A (Executive Overview) and Dashboard B (Policy Timeline Simulation) using existing Phase 1-5 outputs only.",
        "- Applied dashboard_spec_v1 as source-of-truth for layout, benchmark defaults, caveats, and chart logic.",
        "- Implemented Streamlit + Plotly package with static export helpers.",
        "",
        "## Data Caveats",
        "",
        "- Success metrics for R2 and R3 are proxy operational analogs and are explicitly footnoted in Dashboard A.",
        "- KPI gap-closure panel uses stand-alone recommendation scenarios and is explicitly labeled non-additive.",
    ]

    if bundle.unresolved:
        lines.extend(["", "## Unresolved Inputs", ""])
        for issue in bundle.unresolved:
            lines.append(f"- {issue}")

    return "\n".join(lines)


def ensure_report_files(bundle: DashboardDataBundle) -> dict[str, Path]:
    """Write inventory, unresolved, and build-note reports to outputs/reports."""

    reports_dir = bundle.project_root / "outputs" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    inventory_path = reports_dir / "dashboard_data_inventory.md"
    unresolved_path = reports_dir / "dashboard_unresolved_dependencies.md"
    notes_path = reports_dir / "dashboard_build_notes.md"

    inventory_path.write_text(build_inventory_markdown(bundle), encoding="utf-8")
    unresolved_path.write_text(build_unresolved_markdown(bundle), encoding="utf-8")
    notes_path.write_text(build_notes_markdown(bundle), encoding="utf-8")

    return {
        "inventory": inventory_path,
        "unresolved": unresolved_path,
        "notes": notes_path,
    }
