"""Export interactive HTML files for the copied overview and timeline dashboards."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.dashboard_config import RECOMMENDATION_STYLE, SCENARIO_LABELS
from src.dashboard.load_dashboard_data import load_dashboard_data
from src.visualization.dashboard_copy_components import (
    build_competitiveness_stacked_figure,
    build_country_rank_bars_copy,
    build_selected_kpi_lines_copy,
    build_success_stacked_figure,
    build_timeline_gantt_copy,
    scenario_header_text,
)


def _overview_html(bundle) -> str:
    success_fig = build_success_stacked_figure(bundle)
    kpi_fig = build_competitiveness_stacked_figure(bundle)

    return f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Dashboard Copy - Overview</title>
  <style>
    body {{
      margin: 0;
      background: #F7F8FA;
      color: #1F2937;
      font-family: Segoe UI, Arial, sans-serif;
      padding: 18px;
    }}
    .panel {{
      background: #FFFFFF;
      border: 1px solid #D9E0EA;
      border-radius: 16px;
      box-shadow: 0 6px 18px rgba(16,24,40,0.06);
      padding: 12px;
      margin-bottom: 14px;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .meta {{ color: #667085; font-size: 14px; }}
  </style>
</head>
<body>
  <div class=\"panel\">
    <h1 style=\"margin:0 0 6px 0\">Overview Dashboard (Interactive Copy)</h1>
    <div class=\"meta\">Same data and palette as the revised Streamlit copy. Interactive charts enabled.</div>
  </div>
  <div class=\"panel\">
    <div style=\"display:flex; gap:8px; flex-wrap:wrap;\">
      <span style=\"background:{RECOMMENDATION_STYLE['R1']['tint']}; padding:6px 10px; border-radius:999px; border:1px solid #D9E0EA\">REC1 palette</span>
      <span style=\"background:{RECOMMENDATION_STYLE['R2']['tint']}; padding:6px 10px; border-radius:999px; border:1px solid #D9E0EA\">REC2 palette</span>
      <span style=\"background:{RECOMMENDATION_STYLE['R3']['tint']}; padding:6px 10px; border-radius:999px; border:1px solid #D9E0EA\">REC3 palette</span>
    </div>
  </div>
  <div class=\"grid-2\">
    <div class=\"panel\">{success_fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>
    <div class=\"panel\">{kpi_fig.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
</body>
</html>
"""


def _timeline_html(bundle, scenario: str, quarter_index: int) -> str:
    title = scenario_header_text(bundle, scenario=scenario, quarter_index=quarter_index)
    timeline_fig = build_timeline_gantt_copy(bundle, quarter_index=quarter_index)
    kpi_fig = build_selected_kpi_lines_copy(bundle, scenario=scenario, quarter_index=quarter_index)
    rank_fig = build_country_rank_bars_copy(bundle, scenario=scenario, quarter_index=quarter_index)

    return f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Dashboard Copy - Timeline</title>
  <style>
    body {{
      margin: 0;
      background: #F7F8FA;
      color: #1F2937;
      font-family: Segoe UI, Arial, sans-serif;
      padding: 18px;
    }}
    .panel {{
      background: #FFFFFF;
      border: 1px solid #D9E0EA;
      border-radius: 16px;
      box-shadow: 0 6px 18px rgba(16,24,40,0.06);
      padding: 12px;
      margin-bottom: 14px;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .meta {{ color: #667085; font-size: 14px; }}
  </style>
</head>
<body>
  <div class=\"panel\">
    <h1 style=\"margin:0 0 6px 0\">Timeline Dashboard (Interactive Copy)</h1>
    <div class=\"meta\">Scenario: {SCENARIO_LABELS.get(scenario, scenario)} | Quarter: {quarter_index}</div>
    <div style=\"margin-top:6px;font-weight:600\">{title}</div>
  </div>
  <div class=\"panel\">{timeline_fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>
  <div class=\"grid-2\">
    <div class=\"panel\">{kpi_fig.to_html(full_html=False, include_plotlyjs=False)}</div>
    <div class=\"panel\">{rank_fig.to_html(full_html=False, include_plotlyjs=False)}</div>
  </div>
</body>
</html>
"""


def main() -> None:
    bundle = load_dashboard_data(PROJECT_ROOT)
    out_dir = PROJECT_ROOT / "outputs" / "dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)

    overview_path = out_dir / "overview_dashboard_interactive.html"
    timeline_path = out_dir / "timeline_dashboard_interactive.html"

    overview_path.write_text(_overview_html(bundle), encoding="utf-8")
    timeline_path.write_text(_timeline_html(bundle, scenario="all_recommendations", quarter_index=16), encoding="utf-8")

    print(f"overview_html: {overview_path}")
    print(f"timeline_html: {timeline_path}")


if __name__ == "__main__":
    main()
