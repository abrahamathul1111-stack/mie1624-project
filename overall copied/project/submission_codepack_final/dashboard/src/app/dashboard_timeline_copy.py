"""Dashboard copy: Timeline dashboard with screenshot-style interactions."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.dashboard.dashboard_config import SCENARIO_LABELS
from src.dashboard.load_dashboard_data import load_dashboard_data
from src.visualization.dashboard_copy_components import (
    build_country_rank_bars_copy,
    build_selected_kpi_lines_copy,
    build_timeline_gantt_copy,
    inject_copy_style,
    render_timeline_summary_cards,
    scenario_header_text,
)


def main() -> None:
    st.set_page_config(page_title="Dashboard Copy - Timeline", layout="wide")
    inject_copy_style()
    bundle = load_dashboard_data(PROJECT_ROOT)

    render_timeline_summary_cards(bundle)

    top_controls = st.columns([0.12, 0.38, 0.28, 0.22], gap="small")
    if "copy_play" not in st.session_state:
        st.session_state.copy_play = False
    if "copy_quarter" not in st.session_state:
        st.session_state.copy_quarter = 1

    with top_controls[0]:
        if st.button("Play"):
            st.session_state.copy_play = not st.session_state.copy_play

    with top_controls[1]:
        quarter = st.slider("Timeline", min_value=1, max_value=16, value=st.session_state.copy_quarter)
        st.session_state.copy_quarter = quarter

    with top_controls[2]:
        scenario = st.selectbox(
            "Scenario",
            options=["baseline", "rec1_only", "rec2_only", "rec3_only", "all_recommendations"],
            index=0,
            format_func=lambda val: SCENARIO_LABELS.get(val, val),
        )

    with top_controls[3]:
        st.markdown(
            "<div style='padding-top:28px;font-weight:700;color:#344054;'>"
            f"{SCENARIO_LABELS.get(scenario, scenario)}"
            "</div>",
            unsafe_allow_html=True,
        )

    if st.session_state.copy_play:
        st.session_state.copy_quarter = 1 if st.session_state.copy_quarter >= 16 else st.session_state.copy_quarter + 1
        st.rerun()

    st.markdown(
        """
        <div class='copy-card' style='margin-top:8px;'>
        <b>Updated action set (matched to project recommendation labels):</b><br>
        • Rec 1 – Build Career Moats for Talent: Elite equity tax exemption; 1:1 salary matching credits; AI Elite fast-track visa.<br>
        • Rec 2 – Build Conditions to Scale AI: Compute subsidies for domestic firms; procurement matching; later-stage capital access.<br>
        • Rec 3 – Stimulate B2B Demand via Credits: Refundable adoption credit; startup registry; conversion mandate with clawback.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<h2 style='text-align:center;color:#1f2937;margin-top:10px'>{scenario_header_text(bundle, scenario, st.session_state.copy_quarter)}</h2>",
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        build_timeline_gantt_copy(bundle, quarter_index=st.session_state.copy_quarter),
        use_container_width=True,
    )

    bottom = st.columns(2, gap="small")
    with bottom[0]:
        st.plotly_chart(
            build_selected_kpi_lines_copy(bundle, scenario=scenario, quarter_index=st.session_state.copy_quarter),
            use_container_width=True,
        )
    with bottom[1]:
        st.plotly_chart(
            build_country_rank_bars_copy(bundle, scenario=scenario, quarter_index=st.session_state.copy_quarter),
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
