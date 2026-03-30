"""Screenshot-style dashboard components built on existing Phase 6 data and palette."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.dashboard_config import (
    CANADA_HIGHLIGHT,
    CARD_BACKGROUND,
    CARD_BORDER,
    COUNTRY_STYLE_MAP,
    GRIDLINE,
    MUTED_NEUTRAL,
    PROBLEM_CARDS,
    RECOMMENDATION_CARDS,
    RECOMMENDATION_STYLE,
    SCENARIO_LABELS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from src.dashboard.load_dashboard_data import DashboardDataBundle, build_timeline_frame, parse_success_metrics

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def inject_copy_style() -> None:
    """Inject screenshot-like card and layout styling."""

    st.markdown(
        f"""
        <style>
        .stApp {{ background: #F7F8FA; }}
        .copy-card {{
            background: {CARD_BACKGROUND};
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
            box-shadow: 0 6px 18px rgba(16,24,40,0.06);
            padding: 12px 14px;
        }}
        .copy-soft-card {{
            border: 1px solid {CARD_BORDER};
            border-radius: 16px;
            box-shadow: 0 6px 18px rgba(16,24,40,0.06);
            padding: 12px 14px;
        }}
        .v-label {{
            writing-mode: vertical-rl;
            transform: rotate(180deg);
            letter-spacing: 2px;
            font-size: 12px;
            font-weight: 700;
            color: #ffffff;
            text-align: center;
            background: #1F2A44;
            border-radius: 12px;
            height: 100%;
            min-height: 140px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 8px 6px;
        }}
        .chip {{
            display: inline-block;
            font-size: 12px;
            border-radius: 999px;
            border: 1px solid {CARD_BORDER};
            background: #FFFFFF;
            color: {TEXT_PRIMARY};
            padding: 3px 8px;
            margin-bottom: 8px;
        }}
        .rec-pill {{
            display: inline-block;
            border-radius: 999px;
            border: 1px solid {CARD_BORDER};
            background: #FFFFFF;
            color: {TEXT_PRIMARY};
            font-size: 12px;
            padding: 4px 8px;
            margin-right: 6px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _scenario_for_rec(rec_id: str) -> str:
    return {"R1": "rec1_only", "R2": "rec2_only", "R3": "rec3_only"}[rec_id]


def _compute_urgency(bundle: DashboardDataBundle, rec_id: str) -> int:
    gap = bundle.frames.get("kpi_gap_reduction_by_recommendation.csv", pd.DataFrame())
    if gap.empty:
        return 75
    scenario = _scenario_for_rec(rec_id)
    frame = gap.loc[(gap["scenario"] == scenario) & (gap["benchmark_type"] == "peer_best") & (gap["quarter_index"] == 16)]
    if frame.empty:
        return 75
    severity = float(frame["baseline_gap"].mean())
    return int(max(45, min(95, round(severity))))


def _recommendation_stats(bundle: DashboardDataBundle, rec_id: str) -> tuple[str, str, int]:
    timeline = build_timeline_frame(bundle)
    rec_short = rec_id.lower().replace("r", "rec")
    rec_rows = timeline.loc[timeline["recommendation_id"] == rec_short]
    if rec_rows.empty:
        return "Q1-Q4", "0 levers", 0

    q_start = int(rec_rows["start_index"].min())
    q_end = int(rec_rows["full_index"].max())
    window = f"Q{q_start}-Q{q_end}"
    lever_chip = f"{len(rec_rows)} policy levers"

    gap = bundle.frames.get("kpi_gap_reduction_by_recommendation.csv", pd.DataFrame())
    scenario = _scenario_for_rec(rec_id)
    active = gap.loc[
        (gap["scenario"] == scenario)
        & (gap["benchmark_type"] == "peer_best")
        & (gap["quarter_index"] == 16)
        & (gap["percent_gap_reduction"] > 0)
    ]
    kpi_count = int(active["kpi"].nunique())
    return window, lever_chip, kpi_count


def render_overview_cards(bundle: DashboardDataBundle) -> None:
    """Render screenshot-style top overview blocks (problems + recommendations)."""

    st.markdown("<h1 style='margin-top:0;color:#0f172a;'>Overview</h1>", unsafe_allow_html=True)

    section_top = st.columns([0.08, 0.92], gap="small")
    with section_top[0]:
        st.markdown("<div class='v-label'>CHALLENGES</div>", unsafe_allow_html=True)
    with section_top[1]:
        cards = st.columns(3, gap="small")
        for col, card in zip(cards, PROBLEM_CARDS):
            style = RECOMMENDATION_STYLE[card["id"]]
            urgency = _compute_urgency(bundle, card["id"])
            with col:
                st.markdown(
                    f"""
                    <div class='copy-soft-card' style='background:{style['tint']};min-height:132px;'>
                      <span class='chip'>{card['evidence'][0]}</span>
                      <div style='font-weight:700;color:{TEXT_PRIMARY};font-size:34px;line-height:1.2'>{card['title']}</div>
                      <div style='margin-top:4px;color:{TEXT_SECONDARY};font-size:14px'>{card['diagnosis']}</div>
                      <div style='margin-top:8px;height:6px;background:#d9dee8;border-radius:999px;overflow:hidden'>
                        <div style='width:{urgency}%;height:6px;background:{style['light']};'></div>
                      </div>
                      <div style='margin-top:6px;color:{TEXT_SECONDARY};font-size:12px'>Urgency index: {urgency}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    section_mid = st.columns([0.08, 0.92], gap="small")
    with section_mid[0]:
        st.markdown("<div class='v-label'>RECOMMENDATIONS & ACTIONS</div>", unsafe_allow_html=True)
    with section_mid[1]:
        rec_cards = st.columns(3, gap="small")
        for col, card in zip(rec_cards, RECOMMENDATION_CARDS):
            style = RECOMMENDATION_STYLE[card["id"]]
            window, lever_chip, kpi_count = _recommendation_stats(bundle, card["id"])
            bullets = "".join([f"<div style='background:#F3F5F9;border-radius:10px;padding:6px 8px;margin-top:6px;font-size:14px;color:{TEXT_PRIMARY}'>{bullet}</div>" for bullet in card["bullets"]])
            with col:
                st.markdown(
                    f"""
                    <div class='copy-soft-card' style='background:{style['tint']};min-height:190px;'>
                      <div style='font-weight:800;color:{TEXT_PRIMARY};font-size:16px;'>
                        <span style='color:{style['core']};'>■</span> {card['id'].replace('R', 'REC')}
                      </div>
                      {bullets}
                      <div style='margin-top:10px;'>
                        <span class='rec-pill'>⏱ {window}</span>
                        <span class='rec-pill'>📌 {lever_chip}</span>
                      </div>
                      <div style='margin-top:6px;color:{TEXT_SECONDARY};font-size:14px;'>Closes gaps on {kpi_count} KPIs</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def build_success_stacked_figure(bundle: DashboardDataBundle) -> go.Figure:
    """Build screenshot-like stacked success metrics chart."""

    success = parse_success_metrics(bundle)
    if success.empty:
        return go.Figure()

    success = success.copy()
    success["target_numeric"] = success["target_numeric"].fillna(success["current_numeric"])

    def progress(row: pd.Series) -> float:
        current = float(row["current_numeric"] or 0.0)
        target = float(row["target_numeric"] or 0.0)
        if target <= 0:
            return 0.0
        if row["direction"] == "lower_is_better":
            return max(0.0, min(100.0, (target / max(current, 1e-9)) * 100.0))
        return max(0.0, min(100.0, (current / target) * 100.0))

    success["current_pct"] = success.apply(progress, axis=1)

    gap = bundle.frames.get("kpi_gap_reduction_by_recommendation.csv", pd.DataFrame())
    rec_strength: dict[str, float] = {}
    for rec_id, scenario in {"R1": "rec1_only", "R2": "rec2_only", "R3": "rec3_only"}.items():
        frame = gap.loc[
            (gap["scenario"] == scenario)
            & (gap["benchmark_type"] == "peer_best")
            & (gap["quarter_index"] == 16)
            & (gap["percent_gap_reduction"] > 0)
        ]
        rec_strength[rec_id] = float(frame["percent_gap_reduction"].mean()) if not frame.empty else 0.0

    segments = {"REC1": [], "REC2": [], "REC3": [], "Current actual": []}
    labels = []
    for row in success.itertuples(index=False):
        labels.append(row.metric_name)
        current = float(row.current_pct)
        remainder = max(0.0, 100.0 - current)
        rec_key = str(row.recommendation_id)
        boost = min(remainder, rec_strength.get(rec_key, 0.0))

        segments["Current actual"].append(current)
        segments["REC1"].append(boost if rec_key == "R1" else 0.0)
        segments["REC2"].append(boost if rec_key == "R2" else 0.0)
        segments["REC3"].append(boost if rec_key == "R3" else 0.0)

    fig = go.Figure()
    fig.add_bar(name="Current actual", x=labels, y=segments["Current actual"], marker_color="#4C78A8")
    fig.add_bar(name="REC1", x=labels, y=segments["REC1"], marker_color=RECOMMENDATION_STYLE["R1"]["core"])
    fig.add_bar(name="REC2", x=labels, y=segments["REC2"], marker_color=RECOMMENDATION_STYLE["R2"]["core"])
    fig.add_bar(name="REC3", x=labels, y=segments["REC3"], marker_color=RECOMMENDATION_STYLE["R3"]["core"])

    fig.update_layout(
        barmode="stack",
        title={"text": "Success metrics", "font": {"size": 32}},
        yaxis={"title": "% toward target", "range": [0, 100], "gridcolor": GRIDLINE},
        xaxis={"tickangle": 28},
        legend={"orientation": "h", "y": -0.24},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        margin={"l": 10, "r": 10, "t": 60, "b": 80},
        height=360,
    )
    return fig


def build_competitiveness_stacked_figure(bundle: DashboardDataBundle) -> go.Figure:
    """Build screenshot-like KPI gap stack with current/rec contributions/remaining gap."""

    gap = bundle.frames.get("kpi_gap_reduction_by_recommendation.csv", pd.DataFrame())
    if gap.empty:
        return go.Figure()

    kpis = [
        "Tortoise Talent Score",
        "Net Migration Flow of AI Skills",
        "AI Hiring Rate YoY Ratio",
        "Compute Hardware Index",
        "Tortoise Commercial Score",
        "AI Adoption (%)",
        "AI Investment Activity",
    ]

    rows = gap.loc[(gap["benchmark_type"] == "peer_best") & (gap["quarter_index"] == 16) & (gap["kpi"].isin(kpis))].copy()
    if rows.empty:
        return go.Figure()

    baseline = rows.groupby("kpi", as_index=True)["baseline_canada_score"].first()
    benchmark = rows.groupby("kpi", as_index=True)["benchmark_score"].first()

    rec_scores = {}
    for scenario in ["rec1_only", "rec2_only", "rec3_only"]:
        rec_scores[scenario] = rows.loc[rows["scenario"] == scenario].set_index("kpi")["scenario_canada_score"]

    labels = [kpi for kpi in kpis if kpi in baseline.index]
    current_pct = []
    rec1_pct = []
    rec2_pct = []
    rec3_pct = []
    remain_pct = []

    for kpi in labels:
        bench = float(benchmark[kpi])
        base = float(baseline[kpi])
        r1 = max(0.0, float(rec_scores["rec1_only"].get(kpi, base)) - base)
        r2 = max(0.0, float(rec_scores["rec2_only"].get(kpi, base)) - base)
        r3 = max(0.0, float(rec_scores["rec3_only"].get(kpi, base)) - base)

        if bench <= 0:
            current_pct.append(0.0)
            rec1_pct.append(0.0)
            rec2_pct.append(0.0)
            rec3_pct.append(0.0)
            remain_pct.append(0.0)
            continue

        base_clip = max(0.0, min(base, bench))
        remaining = max(0.0, bench - base_clip)
        c1 = min(r1, remaining)
        remaining -= c1
        c2 = min(r2, remaining)
        remaining -= c2
        c3 = min(r3, remaining)
        remaining -= c3

        current_pct.append((base_clip / bench) * 100.0)
        rec1_pct.append((c1 / bench) * 100.0)
        rec2_pct.append((c2 / bench) * 100.0)
        rec3_pct.append((c3 / bench) * 100.0)
        remain_pct.append((remaining / bench) * 100.0)

    fig = go.Figure()
    fig.add_bar(name="Current actual", x=labels, y=current_pct, marker_color="#4C78A8")
    fig.add_bar(name="REC1", x=labels, y=rec1_pct, marker_color=RECOMMENDATION_STYLE["R1"]["core"])
    fig.add_bar(name="REC2", x=labels, y=rec2_pct, marker_color=RECOMMENDATION_STYLE["R2"]["core"])
    fig.add_bar(name="REC3", x=labels, y=rec3_pct, marker_color=RECOMMENDATION_STYLE["R3"]["core"])
    fig.add_bar(name="Remaining gap", x=labels, y=remain_pct, marker_color="#8C6BB1")

    fig.update_layout(
        barmode="stack",
        title={"text": "AI competitiveness KPIs", "font": {"size": 32}},
        yaxis={"title": "% toward target", "range": [0, 100], "gridcolor": GRIDLINE},
        xaxis={"tickangle": 22},
        legend={"orientation": "h", "y": -0.24},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        margin={"l": 10, "r": 10, "t": 60, "b": 80},
        height=360,
    )
    return fig


def _quarter_label_from_index(quarter_index: int) -> str:
    year = 2026 + ((quarter_index - 1) // 4)
    q = ((quarter_index - 1) % 4) + 1
    return f"{year}Q{q}"


def render_timeline_summary_cards(bundle: DashboardDataBundle) -> None:
    """Render top rec summary boxes in screenshot style."""

    timeline = build_timeline_frame(bundle)
    cols = st.columns(3, gap="small")
    for col, rec_id in zip(cols, ["R1", "R2", "R3"]):
        style = RECOMMENDATION_STYLE[rec_id]
        rec_key = rec_id.lower().replace("r", "rec")
        rows = timeline.loc[timeline["recommendation_id"] == rec_key]
        details = []
        for row in rows.itertuples(index=False):
            details.append(
                f"• {row.display_lever}: Q{int(row.start_index)}-Q{int(row.full_index)}"
            )
        body = "<br>".join(details) if details else "No schedule rows available"
        with col:
            st.markdown(
                f"""
                <div class='copy-card' style='background:{style['tint']};min-height:95px;'>
                  <div style='font-weight:700;color:{style['dark']};font-size:14px'>{rec_id} - {style['label']}</div>
                  <div style='font-size:12px;color:{TEXT_PRIMARY};line-height:1.35;margin-top:4px'>{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def build_timeline_gantt_copy(bundle: DashboardDataBundle, quarter_index: int) -> go.Figure:
    """Build screenshot-like policy timeline Gantt chart."""

    timeline = build_timeline_frame(bundle)
    if timeline.empty:
        return go.Figure()

    fig = go.Figure()
    for row in timeline.itertuples(index=False):
        rec_family = str(row.rec_family)
        core = RECOMMENDATION_STYLE.get(rec_family, {}).get("core", MUTED_NEUTRAL)
        fig.add_trace(
            go.Bar(
                x=[float(row.duration)],
                y=[row.display_lever],
                base=[float(row.start_index)],
                orientation="h",
                marker={"color": core, "line": {"color": "#ffffff", "width": 1.0}},
                showlegend=False,
                hovertemplate=(
                    f"{row.display_lever}<br>Start: Q{int(row.start_index)}<br>Full effect: Q{int(row.full_index)}"
                    f"<br>Pattern: {row.rollout_pattern}<extra></extra>"
                ),
            )
        )

    fig.add_vline(x=quarter_index, line_color="#1f2937", line_dash="dot", line_width=2)

    fig.update_layout(
        title={"text": "Federal Policy Actions Over the 1-3 Year Timeline", "font": {"size": 24}},
        barmode="overlay",
        xaxis={"title": "Quarter", "tickvals": list(range(1, 17)), "ticktext": [_quarter_label_from_index(i) for i in range(1, 17)], "gridcolor": GRIDLINE},
        yaxis={"title": "", "autorange": "reversed"},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        margin={"l": 10, "r": 10, "t": 70, "b": 50},
        height=470,
    )
    return fig


def build_selected_kpi_lines_copy(bundle: DashboardDataBundle, scenario: str, quarter_index: int) -> go.Figure:
    """Build lower-left timeline KPI line chart."""

    trajectories = bundle.frames.get("canada_kpi_trajectories.csv", pd.DataFrame())
    watch = [
        "AI Investment Activity",
        "AI Adoption (%)",
        "Tortoise Commercial Score",
        "AI Patent Grants (per 100k)",
        "Tortoise Talent Score",
    ]
    frame = trajectories.loc[(trajectories["scenario"] == scenario) & (trajectories["kpi"].isin(watch))].copy()
    if frame.empty:
        return go.Figure()

    palette = [
        RECOMMENDATION_STYLE["R2"]["dark"],
        RECOMMENDATION_STYLE["R3"]["core"],
        RECOMMENDATION_STYLE["R2"]["core"],
        "#6C8EBF",
        RECOMMENDATION_STYLE["R1"]["core"],
    ]

    fig = go.Figure()
    for idx, kpi in enumerate(watch):
        rows = frame.loc[frame["kpi"] == kpi].sort_values("quarter_index")
        if rows.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=rows["quarter_index"],
                y=rows["kpi_score_median"],
                mode="lines",
                name=kpi,
                line={"color": palette[idx % len(palette)], "width": 2.2},
            )
        )

    fig.add_vline(x=quarter_index, line_color="#1f2937", line_dash="dot", line_width=2)
    fig.update_layout(
        title={"text": "Selected KPI Improvement from Federal Actions", "font": {"size": 20}},
        xaxis={"title": "Quarter", "dtick": 1, "gridcolor": GRIDLINE},
        yaxis={"title": "Canada KPI score", "gridcolor": GRIDLINE},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        margin={"l": 10, "r": 10, "t": 50, "b": 35},
        legend={"orientation": "v", "x": 0.01, "y": 0.98},
        height=290,
    )
    return fig


def build_country_rank_bars_copy(bundle: DashboardDataBundle, scenario: str, quarter_index: int) -> go.Figure:
    """Build lower-right country ranking bars with Canada highlight."""

    scores = bundle.frames.get("country_quarter_scores.csv", pd.DataFrame())
    frame = scores.loc[(scores["scenario"] == scenario) & (scores["quarter_index"] == quarter_index)].copy()
    if frame.empty:
        return go.Figure()

    frame = frame.sort_values("composite_score", ascending=True)
    frame["label"] = frame["country"].map(
        lambda c: f"{COUNTRY_STYLE_MAP.get(c, {}).get('flag', '')} {COUNTRY_STYLE_MAP.get(c, {}).get('short', c)}".strip()
    )
    frame["color"] = frame["country"].map(lambda c: COUNTRY_STYLE_MAP.get(c, {}).get("color", MUTED_NEUTRAL))

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=frame["composite_score"],
            y=frame["label"],
            orientation="h",
            marker={
                "color": [CANADA_HIGHLIGHT if c == "Canada" else clr for c, clr in zip(frame["country"], frame["color"])],
                "line": {"color": "#ffffff", "width": 0.6},
            },
            customdata=frame[["country", "rank"]],
            hovertemplate="%{customdata[0]}<br>Rank: %{customdata[1]:.0f}<br>Composite: %{x:.2f}<extra></extra>",
            showlegend=False,
        )
    )

    canada_rank = frame.loc[frame["country"] == "Canada", "rank"]
    rank_text = f"Rank {int(canada_rank.iloc[0])}" if not canada_rank.empty else ""

    fig.update_layout(
        title={"text": f"Canada Rank vs Other Countries | {rank_text}", "font": {"size": 20}},
        xaxis={"title": "Composite score", "gridcolor": GRIDLINE},
        yaxis={"title": "", "automargin": True},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        margin={"l": 10, "r": 10, "t": 50, "b": 35},
        height=290,
    )
    return fig


def scenario_header_text(bundle: DashboardDataBundle, scenario: str, quarter_index: int) -> str:
    """Build headline text like screenshot for timeline dashboard."""

    label = SCENARIO_LABELS.get(scenario, scenario)
    ranking = bundle.frames.get("canada_rank_trajectory.csv", pd.DataFrame())
    row = ranking.loc[(ranking["scenario"] == scenario) & (ranking["quarter_index"] == quarter_index)].head(1)
    if row.empty:
        return f"Federal-Only Policy Timeline Simulation | {label}"
    score = float(row["composite_score_median"].iloc[0])
    return f"Federal-Only Policy Timeline Simulation | {label} | Canada Composite {score:.2f}"
