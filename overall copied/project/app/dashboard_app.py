"""Phase 6 final dashboard package: executive and simulation dashboards."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.dashboard.dashboard_config import (
    CARD_BACKGROUND,
    CARD_BORDER,
    DASHBOARD_A_TEXT,
    DASHBOARD_B_TEXT,
    DashboardExportPaths,
    PAGE_BACKGROUND,
    SCENARIO_LABELS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from src.dashboard.load_dashboard_data import ensure_report_files, load_dashboard_data
from src.visualization.build_dashboard_a import (
    build_dashboard_a_html,
    build_gap_closure_figure,
    build_success_metrics_figure,
)
from src.visualization.build_dashboard_b import (
    build_country_ranking_figure,
    build_dashboard_b_header_html,
    build_kpi_trajectory_figure,
    build_selected_quarter_chips,
    build_timeline_gantt,
)


def _inject_page_style() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {PAGE_BACKGROUND};
        }}
        .phase-card {{
            background: {CARD_BACKGROUND};
            border: 1px solid {CARD_BORDER};
            border-radius: 22px;
            box-shadow: 0 8px 20px rgba(16,24,40,0.06);
            padding: 16px 18px;
        }}
        .chip-wrap {{
            background: {CARD_BACKGROUND};
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
            padding: 10px 12px;
        }}
        .chip-title {{
            font-size: 12px;
            color: {TEXT_SECONDARY};
        }}
        .chip-value {{
            font-size: 24px;
            color: {TEXT_PRIMARY};
            font-weight: 700;
            line-height: 1.2;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_chip(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="chip-wrap">
          <div class="chip-title">{label}</div>
          <div class="chip-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_a(bundle, benchmark_mode: str) -> tuple[object, object]:
    """Render Dashboard A and return figures for static exports."""

    st.markdown('<div class="phase-card">', unsafe_allow_html=True)
    st.markdown(build_dashboard_a_html(bundle), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1.08, 1.62], gap="large")
    success_fig = build_success_metrics_figure(bundle)
    gap_fig = build_gap_closure_figure(bundle, benchmark_type=benchmark_mode)

    with left_col:
        st.plotly_chart(success_fig, use_container_width=True)
    with right_col:
        st.plotly_chart(gap_fig, use_container_width=True)

    return success_fig, gap_fig


def render_dashboard_b(bundle, scenario: str, quarter_index: int, show_uncertainty: bool) -> tuple[object, object, object]:
    """Render Dashboard B and return key figures for static exports."""

    st.markdown('<div class="phase-card">', unsafe_allow_html=True)
    st.markdown(build_dashboard_b_header_html(), unsafe_allow_html=True)

    chips = build_selected_quarter_chips(bundle, scenario=scenario, quarter_index=quarter_index)
    chip_col1, chip_col2, chip_col3, chip_col4, chip_col5 = st.columns(5)
    with chip_col1:
        _render_chip("Scenario", chips["scenario"])
    with chip_col2:
        _render_chip("Composite (median)", chips["composite"])
    with chip_col3:
        _render_chip("Rank (median)", chips["rank"])
    with chip_col4:
        _render_chip("Delta vs baseline", chips["delta_baseline"])
    with chip_col5:
        _render_chip("Delta vs start", chips["delta_start"])

    st.markdown("</div>", unsafe_allow_html=True)

    timeline_fig = build_timeline_gantt(bundle)
    st.plotly_chart(timeline_fig, use_container_width=True)

    bottom_left, bottom_right = st.columns([1.25, 1.0], gap="large")
    kpi_fig = build_kpi_trajectory_figure(
        bundle,
        scenario=scenario,
        show_uncertainty=show_uncertainty,
    )
    ranking_fig = build_country_ranking_figure(
        bundle,
        scenario=scenario,
        quarter_index=quarter_index,
    )

    with bottom_left:
        st.plotly_chart(kpi_fig, use_container_width=True)
    with bottom_right:
        st.plotly_chart(ranking_fig, use_container_width=True)

    return timeline_fig, kpi_fig, ranking_fig


def _render_final_html(
    bundle,
    success_fig,
    gap_fig,
    timeline_fig,
    kpi_fig,
    ranking_fig,
    benchmark_mode: str,
    scenario: str,
    quarter_index: int,
) -> str:
    """Build a standalone HTML report containing both dashboards."""

    summary = bundle.frames.get("scenario_comparison.csv", pd.DataFrame())
    summary_rows = summary[["scenario", "composite_score_median", "rank_median"]].copy() if not summary.empty else pd.DataFrame()
    summary_rows["scenario"] = summary_rows["scenario"].map(lambda value: SCENARIO_LABELS.get(value, value))

    summary_table = ""
    if not summary_rows.empty:
        summary_table = "<table style='width:100%;border-collapse:collapse;font-size:13px;'>"
        summary_table += "<tr><th style='text-align:left;border-bottom:1px solid #D9E0EA;padding:8px;'>Scenario</th><th style='text-align:right;border-bottom:1px solid #D9E0EA;padding:8px;'>Composite</th><th style='text-align:right;border-bottom:1px solid #D9E0EA;padding:8px;'>Rank</th></tr>"
        for row in summary_rows.itertuples(index=False):
            summary_table += (
                f"<tr><td style='padding:8px;border-bottom:1px solid #EEF1F5;'>{row.scenario}</td>"
                f"<td style='padding:8px;text-align:right;border-bottom:1px solid #EEF1F5;'>{float(row.composite_score_median):.2f}</td>"
                f"<td style='padding:8px;text-align:right;border-bottom:1px solid #EEF1F5;'>#{int(round(float(row.rank_median)))}</td></tr>"
            )
        summary_table += "</table>"

    return f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Phase 6 Final Dashboard</title>
        <style>
          body {{ background:#F7F8FA; font-family: 'Segoe UI', sans-serif; color:#1F2937; margin:0; padding:24px; }}
          .card {{ background:#FFFFFF; border:1px solid #D9E0EA; border-radius:22px; box-shadow:0 8px 20px rgba(16,24,40,0.06); padding:18px; margin-bottom:16px; }}
          .grid-two {{ display:grid; grid-template-columns: 1fr 1fr; gap:16px; }}
          .meta {{ color:#667085; font-size:14px; }}
        </style>
      </head>
      <body>
        <div class="card">
          <h1 style="margin:0;">{DASHBOARD_A_TEXT['title']}</h1>
          <div class="meta" style="margin-top:8px;">{DASHBOARD_A_TEXT['subtitle']}</div>
        </div>
        <div class="card">{build_dashboard_a_html(bundle)}</div>
        <div class="grid-two">
          <div class="card">{success_fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>
          <div class="card">{gap_fig.to_html(full_html=False, include_plotlyjs=False)}</div>
        </div>
        <div class="card" style="margin-top:18px;">
          <h1 style="margin:0;">{DASHBOARD_B_TEXT['title']}</h1>
          <div class="meta" style="margin-top:8px;">{DASHBOARD_B_TEXT['subtitle']}</div>
          <div class="meta" style="margin-top:8px;">Scenario: {SCENARIO_LABELS.get(scenario, scenario)} | Quarter index: {quarter_index} | Benchmark mode: {benchmark_mode}</div>
        </div>
        <div class="card">{timeline_fig.to_html(full_html=False, include_plotlyjs=False)}</div>
        <div class="grid-two">
          <div class="card">{kpi_fig.to_html(full_html=False, include_plotlyjs=False)}</div>
          <div class="card">{ranking_fig.to_html(full_html=False, include_plotlyjs=False)}</div>
        </div>
        <div class="card">
          <h3 style="margin-top:0;">Scenario Summary (2029Q4)</h3>
          {summary_table}
        </div>
      </body>
    </html>
    """


def export_dashboard_assets(
    bundle,
    success_fig,
    gap_fig,
    timeline_fig,
    kpi_fig,
    ranking_fig,
    benchmark_mode: str,
    scenario: str,
    quarter_index: int,
) -> dict[str, Path]:
    """Export HTML and snapshots for final deliverables."""

    outputs_dashboard_dir = bundle.project_root / "outputs" / "dashboard"
    outputs_dashboard_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = outputs_dashboard_dir / "dashboard_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir = outputs_dashboard_dir / "dashboard_data_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    report_paths = ensure_report_files(bundle)

    html = _render_final_html(
        bundle=bundle,
        success_fig=success_fig,
        gap_fig=gap_fig,
        timeline_fig=timeline_fig,
        kpi_fig=kpi_fig,
        ranking_fig=ranking_fig,
        benchmark_mode=benchmark_mode,
        scenario=scenario,
        quarter_index=quarter_index,
    )

    export_paths = DashboardExportPaths()
    html_path = bundle.project_root / export_paths.html
    html_path.write_text(html, encoding="utf-8")

    dashboard_a_png = bundle.project_root / export_paths.dashboard_a_png
    dashboard_b_png = bundle.project_root / export_paths.dashboard_b_png

    snapshot_errors: list[str] = []
    try:
        gap_fig.write_image(dashboard_a_png, width=1920, height=1080, scale=1)
    except Exception as exc:  # pragma: no cover
        snapshot_errors.append(f"dashboard_a_snapshot.png export failed: {exc}")

    try:
        timeline_fig.write_image(dashboard_b_png, width=1920, height=1080, scale=1)
    except Exception as exc:  # pragma: no cover
        snapshot_errors.append(f"dashboard_b_snapshot.png export failed: {exc}")

    # Save reusable bundle tables used by this dashboard package.
    bundle_tables = {
        "baseline_country_scores.csv",
        "scenario_comparison.csv",
        "country_quarter_scores.csv",
        "canada_rank_trajectory.csv",
        "canada_kpi_trajectories.csv",
        "kpi_gap_reduction_by_recommendation.csv",
        "implementation_schedule.csv",
        "calibration_effects.csv",
        "calibration_lags.csv",
        "success_metrics_tracking.csv",
    }
    for file_name in sorted(bundle_tables):
        frame = bundle.frames.get(file_name)
        if frame is not None and not frame.empty:
            frame.to_csv(bundle_dir / file_name, index=False)

    if snapshot_errors:
        unresolved_path = report_paths["unresolved"]
        unresolved_text = unresolved_path.read_text(encoding="utf-8")
        unresolved_text += "\n\n## Static Snapshot Export Notes\n"
        for error in snapshot_errors:
            unresolved_text += f"\n- {error}\n"
        unresolved_text += "\nInstall kaleido to enable Plotly PNG export if needed.\n"
        unresolved_path.write_text(unresolved_text, encoding="utf-8")

    return {
        "html": html_path,
        "dashboard_a_png": dashboard_a_png,
        "dashboard_b_png": dashboard_b_png,
        "inventory": report_paths["inventory"],
        "unresolved": report_paths["unresolved"],
        "notes": report_paths["notes"],
    }


def run_streamlit_app() -> None:
    """Interactive Streamlit entrypoint."""

    st.set_page_config(page_title="Phase 6 Final Dashboards", layout="wide")
    _inject_page_style()

    bundle = load_dashboard_data(PROJECT_ROOT)
    ensure_report_files(bundle)

    st.sidebar.header("Dashboard controls")
    view_mode = st.sidebar.radio("Dashboard", options=["Dashboard A", "Dashboard B"], horizontal=True)
    benchmark_mode = st.sidebar.selectbox(
        "Benchmark mode (Dashboard A)",
        options=["peer_best", "global_best"],
        index=0,
    )

    scenario_values = ["baseline", "rec1_only", "rec2_only", "rec3_only", "all_recommendations"]
    scenario = st.sidebar.selectbox(
        "Scenario (Dashboard B)",
        options=scenario_values,
        index=scenario_values.index("all_recommendations"),
        format_func=lambda value: SCENARIO_LABELS.get(value, value),
    )

    if "quarter_index" not in st.session_state:
        st.session_state.quarter_index = 16
    if "is_playing" not in st.session_state:
        st.session_state.is_playing = False

    play_col, pause_col = st.sidebar.columns(2)
    with play_col:
        if st.button("Play"):
            st.session_state.is_playing = True
    with pause_col:
        if st.button("Pause"):
            st.session_state.is_playing = False

    quarter_index = st.sidebar.slider("Quarter", min_value=1, max_value=16, value=st.session_state.quarter_index)
    st.session_state.quarter_index = quarter_index

    if st.session_state.is_playing:
        st.session_state.quarter_index = 1 if quarter_index >= 16 else quarter_index + 1
        st.rerun()

    show_uncertainty = st.sidebar.toggle("Show p10-p90 uncertainty", value=True)

    if bundle.unresolved:
        with st.expander("Dependency notes", expanded=False):
            for issue in bundle.unresolved:
                st.write(f"- {issue}")

    if view_mode == "Dashboard A":
        render_dashboard_a(bundle, benchmark_mode=benchmark_mode)
    else:
        render_dashboard_b(
            bundle,
            scenario=scenario,
            quarter_index=st.session_state.quarter_index,
            show_uncertainty=show_uncertainty,
        )

    st.sidebar.markdown("---")
    if st.sidebar.button("Export final dashboard package"):
        success_fig, gap_fig = render_dashboard_a(bundle, benchmark_mode=benchmark_mode)
        timeline_fig, kpi_fig, ranking_fig = render_dashboard_b(
            bundle,
            scenario=scenario,
            quarter_index=st.session_state.quarter_index,
            show_uncertainty=show_uncertainty,
        )
        paths = export_dashboard_assets(
            bundle,
            success_fig=success_fig,
            gap_fig=gap_fig,
            timeline_fig=timeline_fig,
            kpi_fig=kpi_fig,
            ranking_fig=ranking_fig,
            benchmark_mode=benchmark_mode,
            scenario=scenario,
            quarter_index=st.session_state.quarter_index,
        )
        st.sidebar.success("Dashboard package exported.")
        for name, path in paths.items():
            st.sidebar.caption(f"{name}: {path.relative_to(PROJECT_ROOT)}")


def run_static_export(benchmark_mode: str = "peer_best", scenario: str = "all_recommendations", quarter_index: int = 16) -> dict[str, Path]:
    """CLI-friendly static export entrypoint."""

    bundle = load_dashboard_data(PROJECT_ROOT)
    ensure_report_files(bundle)
    success_fig = build_success_metrics_figure(bundle)
    gap_fig = build_gap_closure_figure(bundle, benchmark_type=benchmark_mode)
    timeline_fig = build_timeline_gantt(bundle)
    kpi_fig = build_kpi_trajectory_figure(bundle, scenario=scenario, show_uncertainty=True)
    ranking_fig = build_country_ranking_figure(bundle, scenario=scenario, quarter_index=quarter_index)
    return export_dashboard_assets(
        bundle,
        success_fig=success_fig,
        gap_fig=gap_fig,
        timeline_fig=timeline_fig,
        kpi_fig=kpi_fig,
        ranking_fig=ranking_fig,
        benchmark_mode=benchmark_mode,
        scenario=scenario,
        quarter_index=quarter_index,
    )


def main() -> None:
    """CLI entrypoint used for static package exports."""

    parser = argparse.ArgumentParser(description="Phase 6 dashboard static export runner")
    parser.add_argument("--export-static", action="store_true", help="Export HTML/PNG/reports without launching Streamlit.")
    parser.add_argument("--benchmark-mode", default="peer_best", choices=["peer_best", "global_best"])
    parser.add_argument(
        "--scenario",
        default="all_recommendations",
        choices=["baseline", "rec1_only", "rec2_only", "rec3_only", "all_recommendations"],
    )
    parser.add_argument("--quarter-index", type=int, default=16)
    args = parser.parse_args()

    if args.export_static:
        paths = run_static_export(
            benchmark_mode=args.benchmark_mode,
            scenario=args.scenario,
            quarter_index=args.quarter_index,
        )
        for key, value in paths.items():
            print(f"{key}: {value}")
    else:
        run_streamlit_app()


if __name__ == "__main__":
    main()
