"""Dashboard B (Policy Timeline Simulation) figure builders."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.dashboard_config import (
    CANADA_HIGHLIGHT,
    CARD_BACKGROUND,
    DASHBOARD_B_TEXT,
    DARK_NEUTRAL,
    DEFAULT_KPI_WATCHLIST,
    GRIDLINE,
    MUTED_NEUTRAL,
    RECOMMENDATION_STYLE,
    SCENARIO_LABELS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    COUNTRY_STYLE_MAP,
)
from src.dashboard.load_dashboard_data import DashboardDataBundle, build_timeline_frame


def build_timeline_gantt(bundle: DashboardDataBundle) -> go.Figure:
    """Build policy-action timeline Gantt chart."""

    timeline = build_timeline_frame(bundle)
    if timeline.empty:
        return go.Figure()

    timeline = timeline.copy()
    timeline["task"] = timeline["rec_family"] + " | " + timeline["lever_id"] + " | " + timeline["display_lever"]
    timeline["start_q"] = timeline["start_index"]
    timeline["end_q"] = timeline["full_index"]

    color_map = {
        "R1": RECOMMENDATION_STYLE["R1"]["core"],
        "R2": RECOMMENDATION_STYLE["R2"]["core"],
        "R3": RECOMMENDATION_STYLE["R3"]["core"],
    }

    fig = go.Figure()
    for row in timeline.itertuples(index=False):
        fig.add_trace(
            go.Bar(
                x=[row.duration],
                y=[row.task],
                base=[row.start_q],
                orientation="h",
                marker={"color": color_map.get(row.rec_family, MUTED_NEUTRAL), "line": {"color": DARK_NEUTRAL, "width": 0.5}},
                hovertemplate=(
                    f"{row.display_lever}<br>Start: Q{row.start_index}<br>Full effect: Q{row.full_index}"
                    f"<br>Rollout: {row.rollout_pattern}<extra></extra>"
                ),
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[row.full_index],
                y=[row.task],
                mode="markers",
                marker={"color": DARK_NEUTRAL, "size": 8, "symbol": "line-ns-open"},
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.update_layout(
        title={"text": DASHBOARD_B_TEXT["timeline_title"], "font": {"size": 18, "color": TEXT_PRIMARY}},
        barmode="overlay",
        height=410,
        margin={"l": 10, "r": 10, "t": 60, "b": 30},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        xaxis={
            "title": "Quarter index (1-16)",
            "tickmode": "array",
            "tickvals": list(range(1, 17)),
            "gridcolor": GRIDLINE,
            "range": [0.7, 16.3],
        },
        yaxis={"title": "Policy lever", "autorange": "reversed"},
        font={"color": TEXT_PRIMARY},
    )
    return fig


def build_kpi_trajectory_figure(
    bundle: DashboardDataBundle,
    scenario: str,
    show_uncertainty: bool,
    watchlist: list[str] | None = None,
) -> go.Figure:
    """Build selected KPI trajectories for Canada under one scenario."""

    watch = watchlist or DEFAULT_KPI_WATCHLIST
    trajectories = bundle.frames.get("canada_kpi_trajectories.csv", pd.DataFrame()).copy()
    trajectories = trajectories.loc[(trajectories["scenario"] == scenario) & (trajectories["kpi"].isin(watch))]
    trajectories = trajectories.sort_values(["kpi", "quarter_index"]) 

    if trajectories.empty:
        return go.Figure()

    if scenario == "all_recommendations":
        palette = ["#264653", "#287271", "#2A9D8F", "#8AB17D", "#E9C46A"]
    elif scenario == "rec1_only":
        palette = [RECOMMENDATION_STYLE["R1"]["dark"], RECOMMENDATION_STYLE["R1"]["core"], "#5B728A", "#7C8FA4", "#9BAABB"]
    elif scenario == "rec2_only":
        palette = [RECOMMENDATION_STYLE["R2"]["dark"], RECOMMENDATION_STYLE["R2"]["core"], "#5B728A", "#7C8FA4", "#9BAABB"]
    else:
        palette = [RECOMMENDATION_STYLE["R3"]["dark"], RECOMMENDATION_STYLE["R3"]["core"], "#5B728A", "#7C8FA4", "#9BAABB"]

    fig = px.line(
        trajectories,
        x="quarter_index",
        y="kpi_score_median",
        color="kpi",
        color_discrete_sequence=palette,
        markers=False,
    )

    if show_uncertainty:
        for kpi_name in watch:
            slice_frame = trajectories.loc[trajectories["kpi"] == kpi_name]
            if slice_frame.empty:
                continue
            color = fig.data[[trace.name for trace in fig.data].index(kpi_name)].line.color
            fig.add_trace(
                go.Scatter(
                    x=pd.concat([slice_frame["quarter_index"], slice_frame["quarter_index"].iloc[::-1]]),
                    y=pd.concat([slice_frame["kpi_score_p90"], slice_frame["kpi_score_p10"].iloc[::-1]]),
                    fill="toself",
                    fillcolor=_hex_to_rgba(color, 0.10),
                    line={"color": "rgba(255,255,255,0)"},
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    latest = trajectories.sort_values("quarter_index").groupby("kpi", as_index=False).tail(1)
    for row in latest.itertuples(index=False):
        fig.add_annotation(
            x=row.quarter_index + 0.2,
            y=row.kpi_score_median,
            text=row.kpi,
            showarrow=False,
            font={"size": 10, "color": TEXT_PRIMARY},
            xanchor="left",
        )

    fig.update_layout(
        title={
            "text": f"{DASHBOARD_B_TEXT['kpi_title']}<br><sup>{DASHBOARD_B_TEXT['kpi_subtitle']}</sup>",
            "font": {"size": 18, "color": TEXT_PRIMARY},
        },
        height=460,
        margin={"l": 12, "r": 120, "t": 65, "b": 35},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        xaxis={"title": "Quarter index", "gridcolor": GRIDLINE, "dtick": 1},
        yaxis={"title": "KPI score", "gridcolor": GRIDLINE},
        legend={"orientation": "h", "y": -0.22},
        font={"color": TEXT_PRIMARY},
    )
    return fig


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"rgba(100,100,100,{alpha})"
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    return f"rgba({red},{green},{blue},{alpha})"


def build_country_ranking_figure(bundle: DashboardDataBundle, scenario: str, quarter_index: int) -> go.Figure:
    """Build country ranking bar chart for selected scenario-quarter."""

    scores = bundle.frames.get("country_quarter_scores.csv", pd.DataFrame()).copy()
    scores = scores.loc[(scores["scenario"] == scenario) & (scores["quarter_index"] == quarter_index)].copy()
    if scores.empty:
        return go.Figure()

    scores = scores.sort_values("composite_score", ascending=True)
    max_rank = scores["rank"].min() + 4

    def label_for_country(country: str) -> str:
        style = COUNTRY_STYLE_MAP.get(country, {"flag": "", "short": country})
        show_flag = country == "Canada" or float(scores.loc[scores["country"] == country, "rank"].iloc[0]) <= max_rank
        prefix = f"{style['flag']} " if show_flag and style.get("flag") else ""
        return prefix + style.get("short", country)

    scores["display_country"] = scores["country"].map(label_for_country)
    scores["bar_color"] = scores["country"].map(
        lambda c: COUNTRY_STYLE_MAP.get(c, {}).get("color", MUTED_NEUTRAL)
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=scores["composite_score"],
            y=scores["display_country"],
            orientation="h",
            marker={
                "color": [CANADA_HIGHLIGHT if country == "Canada" else color for country, color in zip(scores["country"], scores["bar_color"])],
                "line": {"color": "#FFFFFF", "width": 0.5},
            },
            customdata=scores[["country", "rank"]],
            hovertemplate="%{customdata[0]}<br>Rank: %{customdata[1]:.0f}<br>Composite: %{x:.2f}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        title={"text": DASHBOARD_B_TEXT["rank_title"], "font": {"size": 18, "color": TEXT_PRIMARY}},
        height=460,
        margin={"l": 10, "r": 10, "t": 65, "b": 30},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        xaxis={"title": "Composite score", "gridcolor": GRIDLINE},
        yaxis={"title": "Country"},
        font={"color": TEXT_PRIMARY},
    )
    return fig


def build_selected_quarter_chips(bundle: DashboardDataBundle, scenario: str, quarter_index: int) -> dict[str, str]:
    """Build score chip metrics for selected scenario and quarter."""

    trajectory = bundle.frames.get("canada_rank_trajectory.csv", pd.DataFrame()).copy()
    if trajectory.empty:
        return {
            "scenario": SCENARIO_LABELS.get(scenario, scenario),
            "composite": "N/A",
            "rank": "N/A",
            "delta_baseline": "N/A",
            "delta_start": "N/A",
        }

    selected = trajectory.loc[(trajectory["scenario"] == scenario) & (trajectory["quarter_index"] == quarter_index)].head(1)
    baseline_selected = trajectory.loc[(trajectory["scenario"] == "baseline") & (trajectory["quarter_index"] == quarter_index)].head(1)
    start_selected = trajectory.loc[(trajectory["scenario"] == scenario) & (trajectory["quarter_index"] == 1)].head(1)

    if selected.empty:
        return {
            "scenario": SCENARIO_LABELS.get(scenario, scenario),
            "composite": "N/A",
            "rank": "N/A",
            "delta_baseline": "N/A",
            "delta_start": "N/A",
        }

    composite = float(selected["composite_score_median"].iloc[0])
    rank = int(round(float(selected["rank_median"].iloc[0])))

    baseline_composite = float(baseline_selected["composite_score_median"].iloc[0]) if not baseline_selected.empty else composite
    delta_baseline = composite - baseline_composite

    start_composite = float(start_selected["composite_score_median"].iloc[0]) if not start_selected.empty else composite
    delta_start = composite - start_composite

    return {
        "scenario": SCENARIO_LABELS.get(scenario, scenario),
        "composite": f"{composite:.2f}",
        "rank": f"#{rank}",
        "delta_baseline": f"{delta_baseline:+.2f}",
        "delta_start": f"{delta_start:+.2f}",
    }


def build_dashboard_b_header_html() -> str:
    """Build static HTML card markup for Dashboard B heading."""

    return (
        f"<div style='padding:4px 4px 8px 4px;'>"
        f"<div style='font-size:38px;font-weight:800;color:{TEXT_PRIMARY};line-height:1.15'>{DASHBOARD_B_TEXT['title']}</div>"
        f"<div style='font-size:17px;color:{TEXT_SECONDARY};margin-top:8px;'>{DASHBOARD_B_TEXT['subtitle']}</div>"
        f"</div>"
    )
