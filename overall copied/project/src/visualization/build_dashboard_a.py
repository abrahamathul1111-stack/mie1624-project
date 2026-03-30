"""Dashboard A (Executive Overview) figure builders."""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.dashboard.dashboard_config import (
    A4_DEFAULT_KPIS,
    CANADA_LIGHT_FILL,
    CARD_BACKGROUND,
    CARD_BORDER,
    DASHBOARD_A_TEXT,
    DARK_NEUTRAL,
    GRIDLINE,
    MUTED_NEUTRAL,
    PROBLEM_CARDS,
    RECOMMENDATION_CARDS,
    RECOMMENDATION_STYLE,
    SCENARIO_LABELS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from src.dashboard.load_dashboard_data import DashboardDataBundle, parse_success_metrics, select_gap_panel_rows


def build_header_metrics(bundle: DashboardDataBundle) -> dict[str, str]:
    """Build key metric chips for dashboard header."""

    baseline = bundle.frames.get("baseline_country_scores.csv", pd.DataFrame())
    comparison = bundle.frames.get("scenario_comparison.csv", pd.DataFrame())

    canada_row = baseline.loc[baseline["country"] == "Canada"].head(1)
    baseline_rank = int(canada_row["rank"].iloc[0]) if not canada_row.empty else 5
    baseline_score = float(canada_row["composite_score"].iloc[0]) if not canada_row.empty else 32.86

    final_all_row = comparison.loc[comparison["scenario"] == "all_recommendations"].head(1)
    final_score = (
        float(final_all_row["composite_score_median"].iloc[0])
        if not final_all_row.empty
        else 36.93
    )
    final_rank = int(round(float(final_all_row["rank_median"].iloc[0]))) if not final_all_row.empty else 4

    return {
        "baseline_rank": f"#{baseline_rank}",
        "baseline_score": f"{baseline_score:.2f}",
        "final_all": f"{final_score:.2f} / #{final_rank}",
    }


def render_problem_cards_html() -> str:
    """Render Dashboard A problem cards as HTML blocks for Streamlit."""

    card_html: list[str] = []
    for card in PROBLEM_CARDS:
        style = RECOMMENDATION_STYLE[card["id"]]
        evidence = "".join(
            [
                f'<span style="display:inline-block;margin:4px 6px 0 0;padding:6px 10px;border-radius:999px;background:#ffffff;border:1px solid {CARD_BORDER};font-size:12px;color:{TEXT_PRIMARY};">{chip}</span>'
                for chip in card["evidence"]
            ]
        )
        card_html.append(
            f"""
            <div style="background:{style['tint']};border:1px solid {CARD_BORDER};border-radius:20px;padding:18px;min-height:210px;box-shadow:0 8px 20px rgba(16,24,40,0.06);">
              <div style="font-size:20px;font-weight:700;color:{style['dark']};line-height:1.2;">{card['title']}</div>
              <div style="margin-top:10px;font-size:14px;color:{TEXT_PRIMARY};line-height:1.5;">{card['diagnosis']}</div>
              <div style="margin-top:14px;">{evidence}</div>
            </div>
            """
        )
    return "\n".join(card_html)


def render_recommendation_cards_html() -> str:
    """Render Dashboard A recommendation cards as HTML blocks for Streamlit."""

    card_html: list[str] = []
    for card in RECOMMENDATION_CARDS:
        style = RECOMMENDATION_STYLE[card["id"]]
        bullets = "".join([f"<li style='margin-bottom:6px'>{bullet}</li>" for bullet in card["bullets"]])
        card_html.append(
            f"""
            <div style="background:{CARD_BACKGROUND};border:1px solid {CARD_BORDER};border-radius:22px;padding:18px;min-height:250px;box-shadow:0 8px 20px rgba(16,24,40,0.06);position:relative;overflow:hidden;">
              <div style="position:absolute;left:0;top:0;height:100%;width:8px;background:{style['core']};"></div>
              <div style="margin-left:12px;">
                <div style="font-size:19px;font-weight:700;color:{style['dark']};line-height:1.2;">{card['title']}</div>
                <div style="margin-top:8px;font-size:14px;color:{TEXT_PRIMARY};line-height:1.45;">{card['objective']}</div>
                <ul style="margin-top:10px;padding-left:18px;color:{TEXT_PRIMARY};font-size:14px;line-height:1.35;">{bullets}</ul>
                <span style="display:inline-block;margin-top:4px;padding:5px 10px;border-radius:999px;background:{style['tint']};border:1px solid {CARD_BORDER};font-size:12px;color:{style['dark']};font-weight:600;">{card['horizon']}</span>
              </div>
            </div>
            """
        )
    return "\n".join(card_html)


def _status_label(direction: str, current: float, target: float) -> str:
    if direction == "lower_is_better":
        if current <= target:
            return "target met"
        if current <= (target + (0.25 * max(target, 1.0))):
            return "on path"
        return "needs improvement"
    if current >= target:
        return "target met"
    if current >= (0.7 * target):
        return "on path"
    return "needs improvement"


def build_success_metrics_figure(bundle: DashboardDataBundle) -> go.Figure:
    """Build A3 as three stacked bullet/progress mini-cards."""

    success = parse_success_metrics(bundle)
    primary = success.loc[success["is_primary_metric"]].copy()
    primary = primary.sort_values("recommendation_id")

    fig = make_subplots(rows=3, cols=1, shared_xaxes=False, vertical_spacing=0.16)

    for index, row in enumerate(primary.itertuples(index=False), start=1):
        style = RECOMMENDATION_STYLE[row.recommendation_id]
        current = float(row.current_numeric) if row.current_numeric is not None else 0.0
        target = float(row.target_numeric) if row.target_numeric is not None else current
        max_axis = max(current, target) * 1.15 if max(current, target) > 0 else 100.0

        if row.direction == "lower_is_better":
            progress_ratio = max(0.0, min(1.0, (max_axis - current) / max(max_axis - target, 1e-9)))
        else:
            progress_ratio = max(0.0, min(1.0, current / max(target, 1e-9)))

        status = _status_label(row.direction, current, target)

        fig.add_trace(
            go.Bar(
                x=[max_axis],
                y=[row.metric_name],
                marker_color="#E8ECF4",
                orientation="h",
                hoverinfo="skip",
                showlegend=False,
            ),
            row=index,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=[max_axis * progress_ratio],
                y=[row.metric_name],
                marker_color=style["core"],
                orientation="h",
                name=row.recommendation_id,
                hovertemplate="Current: %{x:.1f}<extra></extra>",
                showlegend=False,
            ),
            row=index,
            col=1,
        )

        fig.add_vline(
            x=target,
            row=index,
            col=1,
            line_width=2,
            line_color=style["dark"],
            line_dash="dash",
        )
        fig.add_annotation(
            x=max_axis,
            y=row.metric_name,
            text=f"Current {row.current_value} | Target {row.target_value} | {status}",
            showarrow=False,
            xanchor="right",
            yanchor="middle",
            font={"size": 11, "color": TEXT_PRIMARY},
            row=index,
            col=1,
        )

        fig.update_xaxes(range=[0, max_axis], showgrid=True, gridcolor=GRIDLINE, row=index, col=1)

    fig.update_layout(
        title={
            "text": f"{DASHBOARD_A_TEXT['success_title']}<br><sup>{DASHBOARD_A_TEXT['success_subtitle']}</sup>",
            "font": {"size": 18, "color": TEXT_PRIMARY},
        },
        barmode="overlay",
        height=500,
        margin={"l": 10, "r": 10, "t": 90, "b": 60},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        font={"color": TEXT_PRIMARY},
    )

    fig.add_annotation(
        x=0,
        y=-0.18,
        xref="paper",
        yref="paper",
        text=(
            "R2 and R3 current baselines are proxy operational analogs from federal commercialization "
            "or first-buyer programs, not AI-only observed program baselines."
        ),
        showarrow=False,
        align="left",
        font={"size": 11, "color": TEXT_SECONDARY},
    )
    return fig


def _scenario_to_family(scenario: str) -> str:
    return {
        "rec1_only": "R1",
        "rec2_only": "R2",
        "rec3_only": "R3",
    }[scenario]


def build_gap_closure_figure(bundle: DashboardDataBundle, benchmark_type: str = "peer_best") -> go.Figure:
    """Build A4 as a 3-panel KPI benchmark gap-closure dumbbell chart."""

    rows = select_gap_panel_rows(bundle, benchmark_type=benchmark_type)
    subplot_titles = [
        SCENARIO_LABELS["rec1_only"],
        SCENARIO_LABELS["rec2_only"],
        SCENARIO_LABELS["rec3_only"],
    ]
    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.08, subplot_titles=subplot_titles)

    for col_index, scenario in enumerate(["rec1_only", "rec2_only", "rec3_only"], start=1):
        family = _scenario_to_family(scenario)
        style = RECOMMENDATION_STYLE[family]
        scenario_rows = rows.loc[rows["scenario"] == scenario].copy()
        if scenario_rows.empty:
            continue

        scenario_rows["display_label"] = scenario_rows["kpi"].map(
            {kpi: f"{idx + 1}. {kpi}" for idx, kpi in enumerate(A4_DEFAULT_KPIS[scenario])}
        )
        scenario_rows = scenario_rows.sort_values("display_label")

        for row in scenario_rows.itertuples(index=False):
            y_label = row.display_label
            baseline = float(row.baseline_canada_score)
            post = float(row.scenario_canada_score)
            benchmark = float(row.benchmark_score)
            pct = float(row.percent_gap_reduction)

            fig.add_trace(
                go.Scatter(
                    x=[baseline, post],
                    y=[y_label, y_label],
                    mode="lines",
                    line={"color": style["core"], "width": 6},
                    hovertemplate="Improvement segment<extra></extra>",
                    showlegend=False,
                ),
                row=1,
                col=col_index,
            )
            fig.add_trace(
                go.Scatter(
                    x=[baseline],
                    y=[y_label],
                    mode="markers",
                    marker={"color": MUTED_NEUTRAL, "size": 10},
                    hovertemplate=f"Baseline: {baseline:.2f}<extra></extra>",
                    showlegend=False,
                ),
                row=1,
                col=col_index,
            )
            fig.add_trace(
                go.Scatter(
                    x=[post],
                    y=[y_label],
                    mode="markers+text",
                    marker={"color": style["dark"], "size": 12},
                    text=[f"{pct:.1f}%"],
                    textposition="middle right",
                    hovertemplate=f"Post-policy: {post:.2f}<extra></extra>",
                    showlegend=False,
                ),
                row=1,
                col=col_index,
            )
            fig.add_trace(
                go.Scatter(
                    x=[benchmark],
                    y=[y_label],
                    mode="markers",
                    marker={"color": DARK_NEUTRAL, "size": 11, "symbol": "diamond"},
                    hovertemplate=f"Benchmark: {benchmark:.2f}<extra></extra>",
                    showlegend=False,
                ),
                row=1,
                col=col_index,
            )

        max_x = float(math.ceil(max(scenario_rows["benchmark_score"].max(), scenario_rows["scenario_canada_score"].max()) / 5.0) * 5.0)
        fig.update_xaxes(range=[0, max_x], showgrid=True, gridcolor=GRIDLINE, row=1, col=col_index)

    fig.update_layout(
        title={
            "text": f"{DASHBOARD_A_TEXT['gap_title']}<br><sup>{DASHBOARD_A_TEXT['gap_subtitle']}</sup>",
            "font": {"size": 18, "color": TEXT_PRIMARY},
        },
        height=520,
        margin={"l": 20, "r": 20, "t": 90, "b": 80},
        paper_bgcolor=CARD_BACKGROUND,
        plot_bgcolor=CARD_BACKGROUND,
        font={"color": TEXT_PRIMARY},
    )

    fig.add_annotation(
        x=0,
        y=-0.2,
        xref="paper",
        yref="paper",
        text="Each recommendation is shown as a separate stand-alone counterfactual against the same Canada baseline. These impacts are not additive.",
        showarrow=False,
        align="left",
        font={"size": 11, "color": TEXT_SECONDARY},
    )
    return fig


def build_dashboard_a_html(bundle: DashboardDataBundle) -> str:
    """Build static HTML card markup for Dashboard A shell elements."""

    metrics = build_header_metrics(bundle)
    problem_html = render_problem_cards_html()
    recommendation_html = render_recommendation_cards_html()

    chips = [
        ("Canada Baseline Rank", metrics["baseline_rank"]),
        ("Canada Baseline Composite", metrics["baseline_score"]),
        ("2029Q4 All Recs (Score / Rank)", metrics["final_all"]),
    ]
    chip_html = "".join(
        [
            f'<div style="background:{CANADA_LIGHT_FILL};border:1px solid {CARD_BORDER};border-radius:16px;padding:10px 14px;min-width:250px;">'
            f'<div style="font-size:12px;color:{TEXT_SECONDARY};">{label}</div><div style="font-size:24px;font-weight:700;color:{TEXT_PRIMARY};">{value}</div></div>'
            for label, value in chips
        ]
    )

    return f"""
    <div style="padding:8px 4px 2px 4px;">
      <div style="font-size:42px;font-weight:800;color:{TEXT_PRIMARY};line-height:1.15;">{DASHBOARD_A_TEXT['title']}</div>
      <div style="font-size:18px;color:{TEXT_SECONDARY};margin-top:8px;">{DASHBOARD_A_TEXT['subtitle']}</div>
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:16px;">{chip_html}</div>
      <div style="display:grid;grid-template-columns:repeat(3, minmax(0, 1fr));gap:20px;margin-top:20px;">{problem_html}</div>
      <div style="display:grid;grid-template-columns:repeat(3, minmax(0, 1fr));gap:20px;margin-top:20px;">{recommendation_html}</div>
    </div>
    """
