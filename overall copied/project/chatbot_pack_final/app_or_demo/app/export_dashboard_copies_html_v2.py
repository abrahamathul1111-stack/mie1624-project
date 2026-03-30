"""Export interactive HTML dashboard copies matching attached interaction patterns."""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.dashboard_config import PROBLEM_CARDS, RECOMMENDATION_CARDS, RECOMMENDATION_STYLE
from src.dashboard.load_dashboard_data import build_timeline_frame, load_dashboard_data, parse_success_metrics


def _parse_target(value: object) -> float:
    text = str(value).strip()
    if not text:
        return 0.0
    if "-" in text:
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
        return float(sum(nums) / len(nums)) if nums else 0.0
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else 0.0


def _urgency_by_rec(gap_df: pd.DataFrame, scenario: str) -> int:
    rows = gap_df.loc[
        (gap_df["scenario"] == scenario)
        & (gap_df["benchmark_type"] == "peer_best")
        & (gap_df["quarter_index"] == 16)
    ]
    if rows.empty:
        return 75
    score = float(rows["baseline_gap"].mean())
    return int(max(55, min(90, round(score))))


def build_overview_payload(bundle) -> dict[str, object]:
    gap = bundle.frames["kpi_gap_reduction_by_recommendation.csv"].copy()
    baseline_country = bundle.frames["baseline_country_scores.csv"].copy()
    scenario_comparison = bundle.frames["scenario_comparison.csv"].copy()
    success = parse_success_metrics(bundle)

    baseline_row = baseline_country.loc[baseline_country["country"] == "Canada"].iloc[0]
    final_row = scenario_comparison.loc[
        (scenario_comparison["scenario"] == "all_recommendations") & (scenario_comparison["quarter_index"] == 16)
    ].iloc[0]

    talent_score = baseline_country.loc[baseline_country["country"] == "Canada", "talent_score"].iloc[0]
    commercial_score = baseline_country.loc[
        baseline_country["country"] == "Canada", "commercial_ecosystem_score"
    ].iloc[0]

    problems = []
    scenario_map = {"R1": "rec1_only", "R2": "rec2_only", "R3": "rec3_only"}
    for card in PROBLEM_CARDS:
        rec_id = card["id"]
        scenario = scenario_map[rec_id]
        urgency = _urgency_by_rec(gap, scenario)

        evidence = card["evidence"][0]
        if rec_id == "R2":
            evidence = f"Commercial Ecosystem score = {commercial_score:.2f}"
        if rec_id == "R1":
            evidence = f"Talent score anchor = {talent_score:.2f}"

        problems.append(
            {
                "title": card["title"],
                "tag": card["evidence"][0],
                "severity": urgency,
                "text": card["diagnosis"],
                "color": RECOMMENDATION_STYLE[rec_id]["tint"],
                "evidence": evidence,
            }
        )

    rec_rows = []
    for card in RECOMMENDATION_CARDS:
        rec_id = card["id"]
        scenario = scenario_map[rec_id]
        active = gap.loc[
            (gap["scenario"] == scenario)
            & (gap["benchmark_type"] == "peer_best")
            & (gap["quarter_index"] == 16)
            & (gap["percent_gap_reduction"] > 0)
        ]
        close_count = int(active["kpi"].nunique())
        rec_rows.append(
            {
                "id": rec_id.lower().replace("r", "rec"),
                "label": rec_id,
                "title": RECOMMENDATION_STYLE[rec_id]["label"],
                "color": RECOMMENDATION_STYLE[rec_id]["tint"],
                "core": RECOMMENDATION_STYLE[rec_id]["core"],
                "actions": card["bullets"],
                "time": "1-3 years",
                "money": "Policy package",
                "closes": close_count,
            }
        )

    success_all = success.copy()
    success_all["target_numeric"] = success_all["target_value"].map(_parse_target)

    direct_metrics = []
    for row in success_all.itertuples(index=False):
        cur = float(row.current_numeric) if row.current_numeric is not None else 0.0
        tgt = float(row.target_numeric)
        if tgt <= 0:
            actual_pct = 0.0
        elif row.direction == "lower_is_better":
            actual_pct = min(100.0, (tgt / max(cur, 1e-9)) * 100.0)
        else:
            actual_pct = min(100.0, (cur / tgt) * 100.0)

        metric_id = str(getattr(row, "action_id", row.metric_name)).strip().lower()
        metric_id = re.sub(r"[^a-z0-9]+", "_", metric_id).strip("_")
        rec_key = str(row.recommendation_id).strip().lower().replace("r", "rec", 1)
        direct_metrics.append(
            {
                "id": metric_id,
                "name": row.metric_name,
                "actual": round(actual_pct, 2),
                "target": 100.0,
                "rec": rec_key,
            }
        )

    baseline_kpis = bundle.frames["baseline_kpi_scores.csv"].copy()
    canada_base = baseline_kpis.loc[baseline_kpis["country"] == "Canada", ["kpi", "kpi_score"]]

    top_impacted = gap.loc[
        (gap["scenario"] == "all_recommendations")
        & (gap["benchmark_type"] == "global_best")
        & (gap["quarter_index"] == 16)
        & (gap["absolute_gap_reduction"] > 0)
    ].sort_values("absolute_gap_reduction", ascending=False)

    workbook_pick = top_impacted["kpi"].head(12).astype(str).tolist()

    workbook_id_map = {
        kpi: re.sub(r"[^a-z0-9]+", "_", kpi.lower()).strip("_") for kpi in workbook_pick
    }

    workbook_metrics = []
    for kpi in workbook_pick:
        score_row = canada_base.loc[canada_base["kpi"] == kpi]
        if score_row.empty:
            continue
        workbook_metrics.append(
            {
                "id": workbook_id_map[kpi],
                "name": kpi,
                "actual": float(score_row["kpi_score"].iloc[0]),
                "target": 100.0,
            }
        )

    impacts = {
        "rec1": {},
        "rec2": {},
        "rec3": {},
    }

    for rec_key, scenario in {"rec1": "rec1_only", "rec2": "rec2_only", "rec3": "rec3_only"}.items():
        rows = gap.loc[
            (gap["scenario"] == scenario)
        & (gap["benchmark_type"] == "global_best")
            & (gap["quarter_index"] == 16)
        ]
        for row in rows.itertuples(index=False):
            kpi = str(row.kpi)
            if kpi not in workbook_id_map:
                continue
            impacts[rec_key][workbook_id_map[kpi]] = max(0.0, float(row.absolute_gap_reduction))

    return {
        "summary": {
            "baseline_rank": int(baseline_row["rank"]),
            "baseline_composite": float(baseline_row["composite_score"]),
            "final_rank": int(final_row["rank_median"]),
            "final_composite": float(final_row["composite_score_median"]),
            "final_quarter": str(final_row["quarter"]),
        },
        "problems": problems,
        "recs": rec_rows,
        "kpisDirect": direct_metrics,
        "kpisWorkbook": workbook_metrics,
        "impacts": impacts,
        "colors": {
            "rec1": RECOMMENDATION_STYLE["R1"]["tint"],
            "rec2": RECOMMENDATION_STYLE["R2"]["tint"],
            "rec3": RECOMMENDATION_STYLE["R3"]["tint"],
            "rec1_core": RECOMMENDATION_STYLE["R1"]["core"],
            "rec2_core": RECOMMENDATION_STYLE["R2"]["core"],
            "rec3_core": RECOMMENDATION_STYLE["R3"]["core"],
            "actual": "#cfe9d2",
            "gap": "#FBE3D6",
        },
    }


def build_timeline_payload(bundle) -> dict[str, object]:
    timeline = build_timeline_frame(bundle)
    canada_kpi = bundle.frames["canada_kpi_trajectories.csv"].copy()
    country_scores = bundle.frames["country_quarter_scores.csv"].copy()
    canada_rank = bundle.frames["canada_rank_trajectory.csv"].copy()

    timeline_rows = []
    for row in timeline.itertuples(index=False):
        rec_family = str(row.rec_family)
        timeline_rows.append(
            {
                "lever": str(row.display_lever),
                "rec": rec_family,
                "start": int(row.start_index),
                "end": int(row.full_index),
                "duration": int(row.duration),
                "rollout": str(row.rollout_pattern),
            }
        )

    watch = [
        "Tortoise Talent Score",
        "Tortoise Commercial Score",
        "AI Investment Activity",
        "AI Adoption (%)",
        "Tortoise Development Score",
    ]

    kpi_rows = canada_kpi.loc[canada_kpi["kpi"].isin(watch)].copy()
    kpi_records = kpi_rows[
        ["scenario", "quarter_index", "quarter", "kpi", "kpi_score_p10", "kpi_score_median", "kpi_score_p90"]
    ].to_dict(orient="records")

    country_records = country_scores[
        ["scenario", "quarter_index", "quarter", "country", "rank", "composite_score"]
    ].to_dict(orient="records")

    rank_records = canada_rank[
        ["scenario", "quarter_index", "quarter", "composite_score_median", "rank_median"]
    ].to_dict(orient="records")

    rec_summaries = []
    for rec in ["rec1", "rec2", "rec3"]:
        rows = [row for row in timeline_rows if row["rec"].lower() == rec.replace("rec", "r")]
        rec_summaries.append({"rec": rec, "rows": rows})

    return {
        "timelineRows": timeline_rows,
        "kpiRows": kpi_records,
        "countryRows": country_records,
        "rankRows": rank_records,
        "recSummaries": rec_summaries,
        "colors": {
            "rec1_core": RECOMMENDATION_STYLE["R1"]["core"],
            "rec2_core": RECOMMENDATION_STYLE["R2"]["core"],
            "rec3_core": RECOMMENDATION_STYLE["R3"]["core"],
            "rec1_tint": RECOMMENDATION_STYLE["R1"]["tint"],
            "rec2_tint": RECOMMENDATION_STYLE["R2"]["tint"],
            "rec3_tint": RECOMMENDATION_STYLE["R3"]["tint"],
            "rec1_light": RECOMMENDATION_STYLE["R1"]["light"],
            "rec1_dark": RECOMMENDATION_STYLE["R1"]["dark"],
            "rec2_dark": RECOMMENDATION_STYLE["R2"]["dark"],
            "rec3_dark": RECOMMENDATION_STYLE["R3"]["dark"],
            "canada": "#D52B1E",
        },
    }


def _overview_html(payload: dict[str, object]) -> str:
    data_json = json.dumps(payload, ensure_ascii=True)

    template = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Overview Copy v2</title>
  <script src=\"https://cdn.plot.ly/plotly-2.32.0.min.js\"></script>
  <style>
    :root {
      --ink: #0f172a;
      --bg: #f8fafc;
      --panel: #ffffff;
      --muted: #64748b;
    }
    * { box-sizing: border-box; }
    body { margin:0; padding:24px; font-family: Segoe UI, Inter, system-ui, sans-serif; color:var(--ink); background:var(--bg); }
    h1 { margin:0 0 6px; }
    .row { display:grid; grid-template-columns:48px 1fr; gap:10px; margin-bottom:14px; }
    .vert-label { writing-mode:vertical-rl; transform:rotate(180deg); text-align:center; font-weight:700; letter-spacing:1px; color:#f8fafc; font-size:12px; display:flex; align-items:center; justify-content:center; background:#1f2937; border-radius:12px; padding:8px 6px; }
    .grid-cols { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap:12px; }
    .card { background:var(--panel); border-radius:14px; padding:14px; border:1px solid #e2e8f0; }
    .pill { display:inline-flex; padding:6px 10px; border-radius:999px; font-size:12px; background:#fff; border:1px solid #e2e8f0; }
    .bar { position:relative; height:8px; background:rgba(15,23,42,0.08); border-radius:999px; overflow:hidden; margin:6px 0 2px; }
    .bar span { position:absolute; top:0; left:0; bottom:0; width:var(--w,0%); background:linear-gradient(90deg,#fbcfe8,#bfdbfe); }
    .actions { display:grid; gap:6px; margin-top:8px; }
    .action-tag { padding:6px 9px; border-radius:10px; background:#f1f5f9; font-size:13px; }
    .meta { display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }
    .badge { padding:4px 8px; border-radius:999px; font-size:12px; border:1px solid #e2e8f0; background:#fff; }
    .chart-grid { display:grid; grid-template-columns: repeat(auto-fit,minmax(320px,1fr)); gap:12px; }
    .top-chips { display:flex; gap:10px; flex-wrap:wrap; margin:8px 0 14px; }
    .chip { background:#fff; border:1px solid #e2e8f0; border-radius:999px; padding:6px 10px; font-size:12px; color:#334155; }
  </style>
</head>
<body>
  <h1>Overview</h1>
  <div class=\"top-chips\" id=\"summaryChips\"></div>
  <div class=\"row\"><div class=\"vert-label\">CHALLENGES</div><div class=\"grid-cols\" id=\"problemCols\"></div></div>
  <div class=\"row\"><div class=\"vert-label\">RECOMMENDATIONS &amp; ACTIONS</div><div class=\"grid-cols\" id=\"recCols\"></div></div>
  <div class=\"row\" style=\"margin-bottom:0;\"><div class=\"vert-label\">IMPACTS</div><div class=\"chart-grid\"><div class=\"card\"><h3>Success metrics</h3><div id=\"clustered\" style=\"height:360px;\"></div></div><div class=\"card\"><h3>AI competitiveness KPIs</h3><div id=\"stacked\" style=\"height:360px;\"></div></div></div></div>

  <script>
    const payload = __DATA_JSON__;
    const colors = payload.colors;

    const summary = payload.summary || {};
    const summaryChips = document.getElementById('summaryChips');
    summaryChips.innerHTML = ''
      + '<span class="chip">Canada baseline rank: #' + (summary.baseline_rank ?? 'N/A') + '</span>'
      + '<span class="chip">Canada baseline composite: ' + (typeof summary.baseline_composite === 'number' ? summary.baseline_composite.toFixed(2) : 'N/A') + '</span>'
      + '<span class="chip">' + (summary.final_quarter || '2029Q4') + ' all-recs median: '
      + (typeof summary.final_composite === 'number' ? summary.final_composite.toFixed(2) : 'N/A')
      + ' (rank #' + (summary.final_rank ?? 'N/A') + ')</span>';

    const problemEl = document.getElementById('problemCols');
    payload.problems.forEach((p) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.9), ' + p.color + ')';
      card.innerHTML = '<div class="pill">' + p.tag + '</div>'
        + '<h3>' + p.title + '</h3>'
        + '<div style="color:#64748b;font-size:14px">' + p.text + '</div>'
        + '<div class="bar" style="--w:' + p.severity + '%"><span></span></div>'
        + '<div style="color:#64748b;font-size:12px">Urgency index: ' + p.severity + '% | ' + p.evidence + '</div>';
      problemEl.appendChild(card);
    });

    const recEl = document.getElementById('recCols');
    payload.recs.forEach((rec) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.96), ' + rec.color + ')';
      const actions = rec.actions.map((a) => '<span class="action-tag">' + a + '</span>').join('');
      const titleColor = rec.core || '#334155';
      card.innerHTML = '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px"><input class="checkbox" type="checkbox" id="' + rec.id + '" checked />'
        + '<span style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.4px;background:' + rec.color + ';color:' + titleColor + ';border:1.5px solid ' + titleColor + '">' + rec.label + '</span></div>'
        + '<div style="font-size:14px;font-weight:700;color:#0f172a;line-height:1.3;margin-bottom:8px">' + (rec.title || '') + '</div>'
        + '<div class="actions">' + actions + '</div>'
        + '<div class="meta"><span class="badge">' + rec.time + '</span><span class="badge">' + rec.money + '</span></div>'
        + '<div style="color:#64748b;font-size:13px;margin-top:6px">Closes gaps on ' + rec.closes + ' KPIs</div>';
      recEl.appendChild(card);
    });

    function selectedRecs() {
      return payload.recs.filter((r) => document.getElementById(r.id)?.checked).map((r) => r.id);
    }

    function impactFor(recId, kpiId) {
      return payload.impacts[recId] && payload.impacts[recId][kpiId] ? payload.impacts[recId][kpiId] : 0;
    }

    function applyImprovement(kpis, ids) {
      return kpis.map((k) => {
        const imp = ids.reduce((sum, recId) => sum + impactFor(recId, k.id), 0);
        const maxGain = Math.max(0, k.target - k.actual);
        const used = Math.min(imp, maxGain);
        const improvedActual = k.actual + used;
        return { ...k, improvement: used, improvedActual: improvedActual, remainingGap: Math.max(0, k.target - improvedActual) };
      });
    }

    function wrapLabel(s, n) {
      const words = s.split(' ');
      const lines = [];
      let cur = '';
      words.forEach((w) => {
        const candidate = cur ? cur + ' ' + w : w;
        if (candidate.length > n && cur) { lines.push(cur); cur = w; }
        else { cur = candidate; }
      });
      if (cur) lines.push(cur);
      return lines.join('<br>');
    }

    function drawClustered(ids) {
      function recIdFromMetricId(metricId) {
        if ((metricId || '').startsWith('r1_')) return 'rec1';
        if ((metricId || '').startsWith('r2_')) return 'rec2';
        if ((metricId || '').startsWith('r3_')) return 'rec3';
        return '';
      }
      const enriched = payload.kpisDirect.map((k) => {
        const gap = Math.max(0, k.target - k.actual);
        const recId = recIdFromMetricId(k.id);
        const recSelected = ids.includes(recId);
        return { ...k, recId: recId, gap: gap, recSelected: recSelected };
      });
      const xOrig = enriched.map((k) => k.name);
      const xWrap = xOrig.map((s) => wrapLabel(s, 14));
      const traces = [
        { name: 'Current actual', type: 'bar', x: xOrig, y: enriched.map((k) => k.actual), marker: { color: colors.actual } }
      ];
      ['rec1', 'rec2', 'rec3'].forEach((recId) => {
        traces.push({
          name: recId.toUpperCase(),
          type: 'bar',
          x: xOrig,
          y: enriched.map((k) => k.recId === recId && k.recSelected ? k.gap : 0),
          marker: { color: colors[recId + '_core'] || colors[recId] }
        });
      });
      traces.push({
        name: 'Remaining gap',
        type: 'bar',
        x: xOrig,
        y: enriched.map((k) => k.recSelected ? 0 : k.gap),
        marker: { color: colors.gap, opacity: 0.35 }
      });
      Plotly.newPlot('clustered', traces, {
        barmode: 'stack',
        yaxis: { range: [0, 100], title: '% toward target', gridcolor: '#e5e7eb' },
        xaxis: { tickvals: xOrig, ticktext: xWrap, automargin: true },
        margin: { l: 70, r: 20, t: 55, b: 110 },
        legend: { orientation: 'h', x: 0, xanchor: 'left', y: 1.2, yanchor: 'bottom', bgcolor: 'rgba(255,255,255,0.85)', bordercolor: '#e2e8f0', borderwidth: 1, font: { size: 11 } },
        paper_bgcolor: '#ffffff', plot_bgcolor: '#f8fafc'
      }, { responsive: true, displaylogo: false });
    }

    function drawStacked(ids) {
      const enriched = applyImprovement(payload.kpisWorkbook, ids);
      const x = enriched.map((k) => k.name);
      const traces = [{ name: 'Current actual', type: 'bar', x: x, y: enriched.map((k) => k.actual), marker: { color: colors.actual } }];
      ['rec1', 'rec2', 'rec3'].forEach((recId) => {
        traces.push({
          name: recId.toUpperCase(),
          type: 'bar',
          x: x,
          y: enriched.map((k) => ids.includes(recId) ? impactFor(recId, k.id) : 0),
          marker: { color: colors[recId + '_core'] || colors[recId] }
        });
      });
      traces.push({ name: 'Remaining gap', type: 'bar', x: x, y: enriched.map((k) => k.remainingGap), marker: { color: colors.gap, opacity: 0.35 } });
      Plotly.newPlot('stacked', traces, {
        barmode: 'stack',
        yaxis: { range: [0, 100], title: '% toward target', gridcolor: '#e5e7eb' },
        xaxis: { tickangle: -30, automargin: true },
        margin: { l: 70, r: 20, t: 10, b: 100 },
        legend: { x: 0.98, xanchor: 'right', y: 0.98, yanchor: 'top', bgcolor: 'rgba(255,255,255,0.85)', bordercolor: '#e2e8f0', borderwidth: 1, font: { size: 11 } },
        paper_bgcolor: '#ffffff', plot_bgcolor: '#f8fafc'
      }, { responsive: true, displaylogo: false });
    }

    function refresh() {
      const ids = selectedRecs();
      drawClustered(ids);
      drawStacked(ids);
    }

    document.body.addEventListener('change', (e) => { if (e.target.matches('.checkbox')) refresh(); });
    refresh();
  </script>
</body>
</html>
"""
    return template.replace("__DATA_JSON__", data_json)


def _timeline_html(payload: dict[str, object]) -> str:
    data_json = json.dumps(payload, ensure_ascii=True)

    template = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Timeline Copy v2</title>
  <script src=\"https://cdn.plot.ly/plotly-2.32.0.min.js\"></script>
  <style>
    :root {{
      --ink: #0f172a;
      --bg: #f8fafc;
      --panel: #ffffff;
      --border: #e2e8f0;
      --muted: #64748b;
      --dark-label: #1f2937;
      --label-fg: #f8fafc;
      --grid: #e5e7eb;
      --rec1-core: #4F7CCB;
      --rec2-core: #D4832E;
      --rec3-core: #2E9C8F;
      --rec1-tint: #EEF4FF;
      --rec2-tint: #FFF4E8;
      --rec3-tint: #EAF8F5;
      --canada: #D52B1E;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; padding:20px 24px; font-family: Segoe UI, Inter, system-ui, -apple-system, sans-serif; background:var(--bg); color:var(--ink); }}
    h2 {{ margin:0 0 14px; font-size:20px; font-weight:700; letter-spacing:-0.3px; color:var(--ink); }}
    .card {{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:12px 14px; margin-bottom:10px; }}
    .top-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }}
    .controls {{ display:grid; grid-template-columns:88px 1fr 220px; gap:12px; align-items:center; }}
    .controls button {{ background:var(--dark-label); color:var(--label-fg); border:none; border-radius:8px; padding:8px 18px; font-size:13px; cursor:pointer; font-weight:600; }}
    .controls button:hover {{ background:#374151; }}
    .controls select {{ border:1px solid var(--border); border-radius:8px; padding:7px 10px; font-size:13px; background:var(--panel); color:var(--ink); }}
    .controls input[type=range] {{ accent-color:var(--dark-label); }}
    .bottom-grid {{ display:grid; grid-template-columns:1.1fr 0.9fr; gap:10px; }}
    .muted {{ color:var(--muted); font-size:12px; }}
    .rec-badge {{ display:inline-flex; align-items:center; gap:5px; padding:4px 9px; border-radius:999px; font-size:11px; font-weight:700; letter-spacing:.4px; border:1px solid var(--border); }}
    .scenario-banner {{ font-size:13px; font-weight:600; color:var(--ink); }}
    .scenario-banner span {{ color:var(--muted); font-weight:400; }}
  </style>
</head>
<body>
  <h2>Federal Policy Timeline Dashboard</h2>

  <div class=\"top-grid\" id=\"summaryGrid\"></div>

  <div class=\"card controls\">
    <button id=\"playBtn\">Play</button>
    <input id=\"quarterSlider\" type=\"range\" min=\"1\" max=\"16\" value=\"1\" />
    <select id=\"scenarioSelect\">
      <option value=\"baseline\">Baseline</option>
      <option value=\"rec1_only\">Rec 1 Only</option>
      <option value=\"rec2_only\">Rec 2 Only</option>
      <option value=\"rec3_only\">Rec 3 Only</option>
      <option value=\"all_recommendations\" selected>All Recs</option>
    </select>
  </div>
  <div class=\"card\" id=\"scenarioText\"></div>
  <div class=\"card\"><div id=\"gantt\" style=\"height:460px;\"></div></div>
  <div class=\"bottom-grid\">
    <div class=\"card\"><div id=\"kpiLine\" style=\"height:300px;\"></div></div>
    <div class=\"card\"><div id=\"rankBars\" style=\"height:300px;\"></div></div>
  </div>

  <script>
    const payload = __DATA_JSON__;
    const scenarioLabels = {{ baseline:'Baseline', rec1_only:'Rec 1 Only', rec2_only:'Rec 2 Only', rec3_only:'Rec 3 Only', all_recommendations:'All Recs' }};

    function quarterToLabel(q) {{
      const year = 2026 + Math.floor((q - 1) / 4);
      const qq = ((q - 1) % 4) + 1;
      return `${{year}}Q${{qq}}`;
    }}

    function recColor(rec) {{
      if (rec === 'R1') return payload.colors.rec1_core;
      if (rec === 'R2') return payload.colors.rec2_core;
      return payload.colors.rec3_core;
    }}

    // Derive which R-family bars to show from the scenario dropdown
    function activeRecsFromScenario(scenario) {{
      if (scenario === 'rec1_only') return new Set(['R1']);
      if (scenario === 'rec2_only') return new Set(['R2']);
      if (scenario === 'rec3_only') return new Set(['R3']);
      return new Set(['R1','R2','R3']);   // baseline / all_recommendations
    }}

    function renderSummaryCards() {{
      const recTints  = {{ rec1: payload.colors.rec1_tint,  rec2: payload.colors.rec2_tint,  rec3: payload.colors.rec3_tint  }};
      const recCores  = {{ rec1: payload.colors.rec1_core,  rec2: payload.colors.rec2_core,  rec3: payload.colors.rec3_core  }};
      const recLabels = {{ rec1: 'R1 — Build Career Moats for Talent', rec2: 'R2 — Build the Conditions to Scale AI in Canada', rec3: 'R3 — Stimulate B2B Demand via Adoption Credits' }};
      const grid = document.getElementById('summaryGrid');
      grid.innerHTML = '';
      payload.recSummaries.forEach(item => {{
        const card = document.createElement('div');
        card.className = 'card';
        card.style.background = 'linear-gradient(135deg, #fff 60%, ' + (recTints[item.rec] || '#f8fafc') + ')';
        const lines = item.rows.map(r => '<span style="display:block;padding:3px 0;font-size:12px;color:#64748b">• ' + r.lever.slice(0,55) + (r.lever.length > 55 ? '…' : '') + ' (Q' + r.start + '–Q' + r.end + ')</span>').join('');
        card.innerHTML = '<span class="rec-badge" style="background:' + (recTints[item.rec] || '#f1f5f9') + ';border-color:' + (recCores[item.rec] || '#e2e8f0') + ';color:' + (recCores[item.rec] || '#334155') + '">' + (recLabels[item.rec] || item.rec.toUpperCase()) + '</span>' + lines;
        grid.appendChild(card);
      }});
    }}

    function drawGantt(quarter, scenario) {{
      const activeRecs = activeRecsFromScenario(scenario);
      // Only show bars for selected recs that have started; clip at current quarter.
      const active = payload.timelineRows.filter(row => row.start <= quarter && activeRecs.has(row.rec));
      const traces = active.map(row => {{
        const clippedEnd = Math.min(row.end, quarter);
        const visibleDuration = Math.max(0, clippedEnd - row.start);
        const opacity = (row.end <= quarter) ? 1.0 : 0.65;
        return {{
          type: 'bar',
          orientation: 'h',
          x: [visibleDuration],
          y: [row.lever],
          base: [row.start],
          marker: {{ color: recColor(row.rec), opacity: opacity, line: {{color:'#ffffff', width:1}} }},
          hovertemplate: row.lever + '<br>Q' + row.start + '–Q' + row.end + '<br>' + row.rollout + '<extra></extra>',
          showlegend: false,
        }};
      }});

      const ghosts = payload.timelineRows
        .filter(row => activeRecs.has(row.rec))  // eslint-disable-line no-shadow
        .map(row => ({{
        type: 'bar', orientation: 'h',
        x: [row.duration], y: [row.lever], base: [row.start],
        marker: {{ color: 'rgba(0,0,0,0)', line: {{color:'rgba(0,0,0,0)', width:0}} }},
        hoverinfo: 'skip', showlegend: false,
      }}));

      const allLevers = payload.timelineRows
        .filter(row => activeRecs.has(row.rec))  // eslint-disable-line no-shadow
        .slice().sort((a, b) => a.start - b.start)
        .map(r => r.lever);

      Plotly.react('gantt', [...ghosts, ...traces], {{
        title: {{ text: 'Federal Policy Actions Over the 1–3 Year Timeline', font: {{ size:14, color:'#0f172a' }} }},
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#f8fafc',
        barmode: 'overlay',
        xaxis: {{
          title: {{ text:'Quarter', font:{{color:'#64748b', size:12}} }},
          range: [0, 17],
          tickvals: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16],
          ticktext: [quarterToLabel(1), quarterToLabel(2), quarterToLabel(3), quarterToLabel(4), quarterToLabel(5), quarterToLabel(6), quarterToLabel(7), quarterToLabel(8), quarterToLabel(9), quarterToLabel(10), quarterToLabel(11), quarterToLabel(12), quarterToLabel(13), quarterToLabel(14), quarterToLabel(15), quarterToLabel(16)],
          gridcolor: '#e5e7eb',
          linecolor: '#e2e8f0',
          tickfont: {{ color:'#64748b', size:11 }},
        }},
        yaxis: {{
          autorange: 'reversed',
          automargin: true,
          tickfont: {{ size: 11, color:'#334155' }},
          categoryarray: allLevers,
          categoryorder: 'array',
          gridcolor: '#e5e7eb',
          linecolor: '#e2e8f0',
        }},
        margin: {{ l: 320, r: 20, t: 50, b: 50 }},
      }}, {{responsive:true, displaylogo:false}});
    }}

    function drawKpiLine(scenario, quarter) {{
      const watch = ['Tortoise Talent Score','Tortoise Commercial Score','AI Investment Activity','AI Adoption (%)','Tortoise Development Score'];
      const rows = payload.kpiRows.filter(r => r.scenario === scenario && watch.includes(r.kpi));
      const kpiColors = [payload.colors.rec1_core, payload.colors.rec2_core, payload.colors.rec3_core, '#6366f1', '#f43f5e'];
      const traces = watch.map((kpi, idx) => {{
        const kRows = rows
          .filter(r => r.kpi === kpi && r.quarter_index <= quarter)
          .sort((a,b) => a.quarter_index - b.quarter_index);
        return {{
          type: 'scatter', mode: 'lines+markers', name: kpi,
          x: kRows.map(r => r.quarter_index),
          y: kRows.map(r => r.kpi_score_median),
          line: {{ width: 2, color: kpiColors[idx % kpiColors.length] }},
          marker: {{ size: kRows.map((r, i) => i === kRows.length - 1 ? 8 : 4), color: kpiColors[idx % kpiColors.length] }},
        }};
      }});

      Plotly.react('kpiLine', traces, {{
        title: {{ text:'KPI Improvement from Federal Actions', font:{{size:14, color:'#0f172a'}} }},
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#f8fafc',
        xaxis: {{ title:{{text:'Quarter', font:{{color:'#64748b',size:12}}}}, range:[1,16], dtick:1, gridcolor:'#e5e7eb', tickfont:{{color:'#64748b',size:11}} }},
        yaxis: {{ title:{{text:'Canada KPI score', font:{{color:'#64748b',size:12}}}}, gridcolor:'#e5e7eb', tickfont:{{color:'#64748b',size:11}} }},
        margin: {{ l:60, r:10, t:45, b:40 }},
        legend: {{ orientation:'v', x:0.01, y:0.98, font:{{size:11, color:'#334155'}}, bgcolor:'rgba(255,255,255,0.85)', bordercolor:'#e2e8f0', borderwidth:1 }},
      }}, {{responsive:true, displaylogo:false}});
    }}

    function drawRankBars(scenario, quarter) {{
      const rows = payload.countryRows
        .filter(r => r.scenario === scenario && r.quarter_index === quarter)
        .sort((a,b) => a.composite_score - b.composite_score);

      const traces = [{{
        type:'bar', orientation:'h',
        x: rows.map(r => r.composite_score),
        y: rows.map(r => r.country),
        marker: {{ color: rows.map(r => r.country === 'Canada' ? payload.colors.canada : payload.colors.rec1_light) }},
        customdata: rows.map(r => [r.country, r.rank]),
        hovertemplate:'%{{customdata[0]}}<br>Rank: %{{customdata[1]}}<br>Composite: %{{x:.2f}}<extra></extra>',
        showlegend:false
      }}];

      const canada = rows.find(r => r.country === 'Canada');
      const rankText = canada ? 'Rank ' + Math.round(canada.rank) : '';

      Plotly.react('rankBars', traces, {{
        title: {{ text:'Canada vs Peers | ' + rankText, font:{{size:14, color:'#0f172a'}} }},
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#f8fafc',
        xaxis:{{ title:{{text:'Composite score', font:{{color:'#64748b',size:12}}}}, gridcolor:'#e5e7eb', tickfont:{{color:'#64748b',size:11}} }},
        yaxis:{{ automargin:true, tickfont:{{color:'#334155',size:11}}, gridcolor:'#e5e7eb' }},
        margin:{{ l:10, r:10, t:45, b:30 }}
      }}, {{responsive:true, displaylogo:false}});
    }}

    function setScenarioText(scenario, quarter) {{
      const row = payload.rankRows.find(r => r.scenario === scenario && r.quarter_index === quarter);
      const composite = row ? row.composite_score_median.toFixed(2) : 'N/A';
      const label = scenarioLabels[scenario] || scenario;
      const qLabel = quarterToLabel(quarter);
      document.getElementById('scenarioText').innerHTML =
        '<span class="scenario-banner">Federal-Only Policy Simulation &nbsp;|&nbsp; ' + label + ' &nbsp;|&nbsp; Canada Composite <b>' + composite + '</b> &nbsp;<span>' + qLabel + '</span></span>';
    }}

    const slider = document.getElementById('quarterSlider');
    const select = document.getElementById('scenarioSelect');
    const playBtn = document.getElementById('playBtn');
    let timer = null;

    function redraw() {{
      const q = Number(slider.value);
      const scenario = select.value;
      setScenarioText(scenario, q);
      drawGantt(q, scenario);
      drawKpiLine(scenario, q);
      drawRankBars(scenario, q);
    }}

    playBtn.addEventListener('click', () => {{
      if (timer) {{
        clearInterval(timer);
        timer = null;
        playBtn.textContent = 'Play';
      }} else {{
        timer = setInterval(() => {{
          let q = Number(slider.value);
          q = q >= 16 ? 1 : q + 1;
          slider.value = q;
          redraw();
        }}, 850);
        playBtn.textContent = 'Pause';
      }}
    }});

    slider.addEventListener('input', redraw);
    select.addEventListener('change', redraw);

    renderSummaryCards();
    redraw();
  </script>
</body>
</html>
"""
    # Normalize escaped braces in the template BEFORE injecting data so that
    # }} inside the JSON payload is never mangled.
    clean = template.replace("{{", "{").replace("}}", "}")
    return clean.replace("__DATA_JSON__", data_json)


def main() -> None:
    bundle = load_dashboard_data(PROJECT_ROOT)
    out_dir = PROJECT_ROOT / "outputs" / "dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)

    overview_payload = build_overview_payload(bundle)
    timeline_payload = build_timeline_payload(bundle)

    overview_path = out_dir / "overview_dashboard_interactive_v2.html"
    timeline_path = out_dir / "timeline_dashboard_interactive_v2.html"

    overview_path.write_text(_overview_html(overview_payload), encoding="utf-8")
    timeline_path.write_text(_timeline_html(timeline_payload), encoding="utf-8")

    print(f"overview_v2_html: {overview_path}")
    print(f"timeline_v2_html: {timeline_path}")


if __name__ == "__main__":
    main()
