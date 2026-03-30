"""Dashboard copy: Overview dashboard with screenshot-style chart types."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.dashboard.load_dashboard_data import load_dashboard_data
from src.visualization.dashboard_copy_components import (
    build_competitiveness_stacked_figure,
    build_success_stacked_figure,
    inject_copy_style,
    render_overview_cards,
)


def main() -> None:
    st.set_page_config(page_title="Dashboard Copy - Overview", layout="wide")
    inject_copy_style()

    bundle = load_dashboard_data(PROJECT_ROOT)
    render_overview_cards(bundle)

    section_bottom = st.columns([0.08, 0.92], gap="small")
    with section_bottom[0]:
        st.markdown("<div class='v-label'>IMPACTS</div>", unsafe_allow_html=True)
    with section_bottom[1]:
        left, right = st.columns(2, gap="small")
        with left:
            st.markdown("<div class='copy-card'>", unsafe_allow_html=True)
            st.plotly_chart(build_success_stacked_figure(bundle), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown("<div class='copy-card'>", unsafe_allow_html=True)
            st.plotly_chart(build_competitiveness_stacked_figure(bundle), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
