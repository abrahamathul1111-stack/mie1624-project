import json, os

cells = []

cells.append({
    "cell_type": "markdown", "id": "a1b2c3d4", "metadata": {},
    "source": [
        "# Canada AI Competitiveness \u2014 Policy Impact Visualizations\n\n",
        "Produces two presentation-quality figures:\n\n",
        "| Figure | Title | Output files |\n",
        "|--------|-------|--------------|\n",
        "| 1 | Canada AI Rank Trajectory by Quarter | `canada_rank_trajectory.png/.pdf` |\n",
        "| 2 | KPI Gap Reduction by Recommendation (vs. Global Best, 2029 Q4) | `kpi_gap_reduction_2029q4.png/.pdf` |\n\n",
        "---\n\n## Expected Input Files\n\n",
        "| Variable | Default path | Description |\n",
        "|----------|-------------|-------------|\n",
        "| `RANK_FILE` | `outputs/tables/canada_rank_trajectory.csv` | Long-format rank trajectory |\n",
        "| `KPI_FILE` | `outputs/tables/kpi_gap_reduction_global_best.csv` | KPI gap reduction at final period |\n",
        "| `OUTPUT_DIR` | `outputs/figures` | Where PNGs and PDFs are saved |\n\n",
        "**Figure 2 automatically excludes KPIs where all scenarios show 0% gap closure.**"
    ]
})

cells.append({
    "cell_type": "code", "execution_count": None, "id": "b2c3d4e5",
    "metadata": {}, "outputs": [],
    "source": [
        "# ============================================================\n",
        "# CONFIGURATION\n",
        "# ============================================================\n",
        "import os\n\n",
        "BASE_DIR   = os.path.join(os.path.dirname(os.path.abspath('.')), 'project')\n",
        "# BASE_DIR = r'C:\\Users\\dayab\\UofT\\WINTER 2026\\MIE1624H Intro to Data\\course project\\EXECUTION\\project'\n\n",
        "RANK_FILE  = os.path.join(BASE_DIR, 'outputs', 'tables', 'canada_rank_trajectory.csv')\n",
        "KPI_FILE   = os.path.join(BASE_DIR, 'outputs', 'tables', 'kpi_gap_reduction_global_best.csv')\n",
        "OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs', 'figures')\n\n",
        "COL_SCENARIO    = 'scenario'\n",
        "COL_QUARTER     = 'quarter'\n",
        "COL_QUARTER_IDX = 'quarter_index'\n",
        "COL_RANK_MED    = 'rank_median'\n",
        "COL_RANK_P10    = 'rank_p10'\n",
        "COL_RANK_P90    = 'rank_p90'\n",
        "COL_KPI         = 'kpi'\n",
        "COL_KPI_ORDER   = 'kpi_order'\n",
        "COL_SUBPILLAR   = 'subpillar'\n",
        "COL_PCT_GAP     = 'percent_gap_reduction'\n",
        "FINAL_PERIOD_IDX = 16\n\n",
        "SCENARIO_LABELS = {\n",
        "    'baseline':            'Baseline (No Action)',\n",
        "    'rec1_only':           'Rec 1: Career Moats',\n",
        "    'rec2_only':           'Rec 2: Scale AI',\n",
        "    'rec3_only':           'Rec 3: B2B Demand',\n",
        "    'all_recommendations': 'All Three Combined',\n",
        "}\n\n",
        "EXPORT_DPI = 300\n",
        "os.makedirs(OUTPUT_DIR, exist_ok=True)\n",
        "print(f'Output directory: {OUTPUT_DIR}')\n",
        "print('Configuration loaded.')"
    ]
})

cells.append({
    "cell_type": "code", "execution_count": None, "id": "c3d4e5f6",
    "metadata": {}, "outputs": [],
    "source": [
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "import matplotlib.patches as mpatches\n",
        "import matplotlib.ticker as mticker\n",
        "import numpy as np\n",
        "import warnings\n",
        "warnings.filterwarnings('ignore')\n\n",
        "plt.rcParams.update({\n",
        "    'font.family': 'DejaVu Sans',\n",
        "    'axes.spines.top': False, 'axes.spines.right': False,\n",
        "    'axes.grid': True, 'grid.color': '#e5e5e5', 'grid.linewidth': 0.7,\n",
        "    'axes.titlesize': 14, 'axes.labelsize': 11,\n",
        "    'xtick.labelsize': 9, 'ytick.labelsize': 9,\n",
        "    'legend.fontsize': 9, 'legend.framealpha': 0.9,\n",
        "    'figure.facecolor': 'white', 'axes.facecolor': 'white',\n",
        "})\n",
        "print('Imports successful.')"
    ]
})

cells.append({
    "cell_type": "code", "execution_count": None, "id": "d4e5f6a7",
    "metadata": {}, "outputs": [],
    "source": [
        "def _load(path, label):\n",
        "    ext = os.path.splitext(path)[1].lower()\n",
        "    df  = pd.read_excel(path) if ext in ('.xlsx', '.xls') else pd.read_csv(path)\n",
        "    print(f'[{label}] loaded: {os.path.basename(path)}  ({len(df):,} rows x {len(df.columns)} cols)')\n",
        "    return df\n\n",
        "def _check_cols(df, required, label):\n",
        "    missing = [c for c in required if c not in df.columns]\n",
        "    if missing:\n",
        "        raise ValueError(f'[{label}] Missing required columns: {missing}')\n",
        "    print(f'[{label}] all required columns present \u2713')\n\n",
        "rank_df = _load(RANK_FILE, 'Figure 1')\n",
        "_check_cols(rank_df, [COL_SCENARIO, COL_QUARTER, COL_QUARTER_IDX, COL_RANK_MED], 'Figure 1')\n",
        "has_bands = (COL_RANK_P10 and COL_RANK_P10 in rank_df.columns and\n",
        "             COL_RANK_P90 and COL_RANK_P90 in rank_df.columns)\n",
        "print('[Figure 1] uncertainty-band columns found \u2713' if has_bands\n",
        "      else '[Figure 1] WARNING: uncertainty-band columns not found \u2014 band skipped.')\n\n",
        "kpi_df = _load(KPI_FILE, 'Figure 2')\n",
        "_check_cols(kpi_df, [COL_SCENARIO, COL_KPI, COL_KPI_ORDER, COL_PCT_GAP], 'Figure 2')\n",
        "if COL_QUARTER_IDX in kpi_df.columns and FINAL_PERIOD_IDX in kpi_df[COL_QUARTER_IDX].unique():\n",
        "    kpi_df = kpi_df[kpi_df[COL_QUARTER_IDX] == FINAL_PERIOD_IDX].copy()\n",
        "    print(f'[Figure 2] filtered to quarter_index={FINAL_PERIOD_IDX}  ({len(kpi_df)} rows remain)')\n",
        "for s in ['rec1_only', 'rec2_only', 'rec3_only', 'all_recommendations']:\n",
        "    status = '\u2713' if s in kpi_df[COL_SCENARIO].unique() else 'WARNING: missing'\n",
        "    print(f'[Figure 2] scenario \"{s}\" {status}')\n",
        "print('\\nData loading complete.')"
    ]
})

cells.append({
    "cell_type": "markdown", "id": "e5f6a7b8", "metadata": {},
    "source": [
        "---\n## Figure 1 \u2014 Canada AI Rank Trajectory by Quarter\n\n",
        "The chart tracks **Canada\u2019s projected global AI competitiveness rank** from 2026 Q1 through 2029 Q4 under five scenarios: doing nothing (Baseline), each of the three individual policy recommendations, and the combined package. The y-axis is inverted so that a better rank appears higher. The shaded band shows the P10\u2013P90 simulation uncertainty range for the combined scenario.\n\n",
        "Reference lines mark the **4th-place target** and the **6th-place baseline drift**."
    ]
})

cells.append({
    "cell_type": "code", "execution_count": None, "id": "f6a7b8c9",
    "metadata": {}, "outputs": [],
    "source": [
        "rank_df_sorted = rank_df.sort_values(COL_QUARTER_IDX)\n",
        "quarters = rank_df_sorted[COL_QUARTER].unique().tolist()\n\n",
        "scenarios_to_plot = [\n",
        "    ('baseline',            dict(color='#888888', lw=1.8, ls='--', zorder=2)),\n",
        "    ('rec1_only',           dict(color='#E07B39', lw=2.0, ls='-',  zorder=3)),\n",
        "    ('rec2_only',           dict(color='#2E75B6', lw=2.0, ls='-',  zorder=3)),\n",
        "    ('rec3_only',           dict(color='#4CAF50', lw=2.0, ls='-',  zorder=3)),\n",
        "    ('all_recommendations', dict(color='#0D1B4B', lw=3.0, ls='-',  zorder=4)),\n",
        "]\n\n",
        "fig, ax = plt.subplots(figsize=(13, 6))\n",
        "legend_handles = []\n\n",
        "for scen_key, style in scenarios_to_plot:\n",
        "    subset = rank_df_sorted[rank_df_sorted[COL_SCENARIO] == scen_key]\n",
        "    if subset.empty: continue\n",
        "    q_to_x = {q: i for i, q in enumerate(quarters)}\n",
        "    xs = [q_to_x[q] for q in subset[COL_QUARTER]]\n",
        "    ys = subset[COL_RANK_MED].values\n",
        "    label = SCENARIO_LABELS.get(scen_key, scen_key)\n",
        "    line, = ax.plot(xs, ys, label=label, marker='o', markersize=4,\n",
        "                    markeredgewidth=0.5, markeredgecolor='white', **style)\n",
        "    legend_handles.append(line)\n",
        "    if scen_key == 'all_recommendations' and has_bands:\n",
        "        ax.fill_between(xs, subset[COL_RANK_P10].values, subset[COL_RANK_P90].values,\n",
        "                        color=style['color'], alpha=0.12, zorder=1)\n",
        "        legend_handles.append(mpatches.Patch(facecolor=style['color'], alpha=0.25,\n",
        "                                              label='All Three Combined: P10\u2013P90'))\n\n",
        "ax.axhline(4, color='#2E7D32', lw=1.4, ls=':', zorder=1)\n",
        "ax.text(len(quarters)-0.05, 4-0.08, '4th place target', color='#2E7D32',\n",
        "        fontsize=8.5, ha='right', va='bottom', style='italic')\n",
        "ax.axhline(6, color='#C62828', lw=1.4, ls=':', zorder=1)\n",
        "ax.text(len(quarters)-0.05, 6+0.08, 'Baseline drift to 6th', color='#C62828',\n",
        "        fontsize=8.5, ha='right', va='top', style='italic')\n\n",
        "_ar = rank_df_sorted[COL_RANK_MED].dropna()\n",
        "y_lo = min(3, max(1, int(_ar.min())-1))\n",
        "y_hi = max(7, int(_ar.max())+1)\n",
        "ax.set_ylim(y_hi+0.4, y_lo-0.4)\n",
        "rank_vals = list(range(y_lo, y_hi+1))\n",
        "ordinals  = {1:'1st', 2:'2nd', 3:'3rd', **{n:f'{n}th' for n in range(4,20)}}\n",
        "ax.set_yticks(rank_vals)\n",
        "ax.set_yticklabels([ordinals.get(r,str(r)) for r in rank_vals])\n",
        "ax.set_xticks(range(len(quarters)))\n",
        "ax.set_xticklabels(quarters, rotation=45, ha='right', fontsize=8.5)\n",
        "ax.set_xlim(-0.5, len(quarters)-0.5)\n",
        "ax.set_xlabel('Quarter', labelpad=8)\n",
        "ax.set_ylabel('Canada Global AI Rank\\n(higher = better)', labelpad=8)\n",
        "ax.set_title('Canada AI Rank Trajectory by Quarter\\n'\n",
        "             'Projected global rank under policy scenarios, 2026 Q1 \u2013 2029 Q4',\n",
        "             fontsize=14, fontweight='bold', pad=14)\n",
        "ax.legend(handles=legend_handles, loc='lower left', frameon=True, framealpha=0.95,\n",
        "          edgecolor='#cccccc', fontsize=9, title='Scenario', title_fontsize=9)\n",
        "plt.tight_layout(pad=1.5)\n\n",
        "out_png = os.path.join(OUTPUT_DIR, 'canada_rank_trajectory.png')\n",
        "out_pdf = os.path.join(OUTPUT_DIR, 'canada_rank_trajectory.pdf')\n",
        "fig.savefig(out_png, dpi=EXPORT_DPI, bbox_inches='tight')\n",
        "fig.savefig(out_pdf, bbox_inches='tight')\n",
        "print(f'Saved: {out_png}')\n",
        "print(f'Saved: {out_pdf}')\n",
        "plt.show()"
    ]
})

cells.append({
    "cell_type": "markdown", "id": "a7b8c9d0", "metadata": {},
    "source": [
        "### Figure 1 \u2014 Key Takeaway\n\n",
        "**Under the baseline (no-action) scenario, Canada slides from 5th to 6th place globally by mid-2027 and stays there through 2029.** Each recommendation slows or reverses this drift:\n\n",
        "- **Rec 1: Career Moats** (orange) improves rank gradually, reflecting multi-year talent development lags.\n",
        "- **Rec 2: Scale AI** (blue) produces an earlier, more pronounced improvement via infrastructure-driven compounding gains.\n",
        "- **Rec 3: B2B Demand** (green) shows meaningful improvement that builds as commercial adoption accelerates.\n",
        "- **All Three Combined** (navy, bold) is the only scenario approaching the 4th-place target by 2029 Q4. Even the pessimistic P10 simulation outperforms the no-action baseline.\n\n",
        "**Decision-maker implication:** No single recommendation is sufficient. Delay risks locking in the 6th-place trajectory permanently."
    ]
})

cells.append({
    "cell_type": "markdown", "id": "b8c9d0e1", "metadata": {},
    "source": [
        "---\n## Figure 2 \u2014 KPI Gap Reduction by Recommendation (vs. Global Best, 2029 Q4)\n\n",
        "The chart shows, for each AI competitiveness KPI where **at least one recommendation closes a non-zero share of the gap**, what percentage of the gap between Canada and the global best performer is closed by 2029 Q4. ",
        "KPIs where all scenarios show 0% gap closure are excluded. ",
        "Bars are grouped by KPI and colored by scenario. KPIs follow the model\u2019s pillar ordering (Talent, Infrastructure, Operating Environment, Research, Development, Commercial Ecosystem, Government Strategy)."
    ]
})

cells.append({
    "cell_type": "code", "execution_count": None, "id": "c9d0e1f2",
    "metadata": {}, "outputs": [],
    "source": [
        "from itertools import groupby\n\n",
        "kpi_scenarios_ordered = [\n",
        "    ('rec1_only',           'Rec 1: Career Moats',  '#E07B39'),\n",
        "    ('rec2_only',           'Rec 2: Scale AI',       '#2E75B6'),\n",
        "    ('rec3_only',           'Rec 3: B2B Demand',     '#4CAF50'),\n",
        "    ('all_recommendations', 'All Three Combined',    '#0D1B4B'),\n",
        "]\n",
        "n_scen = len(kpi_scenarios_ordered)\n\n",
        "# --- Build ordered KPI list ---\n",
        "ref_scen   = kpi_df[kpi_df[COL_SCENARIO] == 'rec1_only']\n",
        "if ref_scen.empty: ref_scen = kpi_df\n",
        "extra_cols = [COL_SUBPILLAR] if COL_SUBPILLAR in kpi_df.columns else []\n",
        "kpi_meta   = (\n",
        "    ref_scen[[COL_KPI, COL_KPI_ORDER] + extra_cols]\n",
        "    .drop_duplicates(subset=[COL_KPI]).sort_values(COL_KPI_ORDER)\n",
        ")\n",
        "kpi_list = kpi_meta[COL_KPI].tolist()\n",
        "n_kpi    = len(kpi_list)\n\n",
        "# --- Build value matrix ---\n",
        "val_matrix = np.zeros((n_kpi, n_scen), dtype=float)\n",
        "for j, (scen_key, _, _) in enumerate(kpi_scenarios_ordered):\n",
        "    subset = kpi_df[kpi_df[COL_SCENARIO] == scen_key]\n",
        "    if subset.empty:\n",
        "        print(f'WARNING: scenario \"{scen_key}\" not found \u2014 bars will be zero.')\n",
        "        continue\n",
        "    lookup = subset.set_index(COL_KPI)[COL_PCT_GAP].to_dict()\n",
        "    for i, kpi in enumerate(kpi_list):\n",
        "        val_matrix[i, j] = lookup.get(kpi, 0.0)\n\n",
        "# --- Drop KPIs where every scenario is 0 ---\n",
        "keep_mask = val_matrix.sum(axis=1) > 0\n",
        "removed   = [k for k, keep in zip(kpi_list, keep_mask) if not keep]\n",
        "if removed:\n",
        "    print(f'Dropping {len(removed)} all-zero KPI(s): {removed}')\n",
        "val_matrix = val_matrix[keep_mask]\n",
        "kpi_list   = [k for k, keep in zip(kpi_list, keep_mask) if keep]\n",
        "kpi_meta   = kpi_meta[kpi_meta[COL_KPI].isin(kpi_list)].copy()\n",
        "n_kpi      = len(kpi_list)\n",
        "print(f'Plotting {n_kpi} KPIs with at least one non-zero value.')\n\n",
        "# --- Layout ---\n",
        "bar_h        = 0.18\n",
        "group_gap    = 0.12\n",
        "group_height = n_scen * bar_h + group_gap\n",
        "y_centers    = np.array([i * group_height for i in range(n_kpi)])\n",
        "fig2, ax2    = plt.subplots(figsize=(12, max(10, n_kpi * group_height + 2)))\n\n",
        "for j, (scen_key, label, color) in enumerate(kpi_scenarios_ordered):\n",
        "    offset   = (j - (n_scen-1)/2) * bar_h\n",
        "    bar_vals = val_matrix[:, j]\n",
        "    bars = ax2.barh(y_centers + offset, bar_vals,\n",
        "                    height=bar_h * 0.92, color=color, alpha=0.88, label=label, zorder=2)\n",
        "    for bar, val in zip(bars, bar_vals):\n",
        "        if val > 0.3:\n",
        "            ax2.text(val + 0.4, bar.get_y() + bar.get_height()/2,\n",
        "                     f'{val:.1f}%', va='center', ha='left', fontsize=6.5, color='#333333')\n\n",
        "ax2.set_yticks(y_centers)\n",
        "ax2.set_yticklabels(kpi_list, fontsize=8)\n",
        "ax2.invert_yaxis()\n\n",
        "if extra_cols:\n",
        "    subpillar_vals = kpi_meta[COL_SUBPILLAR].tolist()\n",
        "    prev = None\n",
        "    for i, sp in enumerate(subpillar_vals):\n",
        "        if sp != prev and i > 0:\n",
        "            ax2.axhline((y_centers[i]+y_centers[i-1])/2, color='#cccccc', lw=0.8, zorder=1)\n",
        "        prev = sp\n",
        "    sp_groups = [(sp, list(idxs)) for sp, idxs in\n",
        "                 groupby(range(n_kpi), key=lambda i: subpillar_vals[i])]\n",
        "    x_r = ax2.get_xlim()[1]\n",
        "    for sp_name, idxs in sp_groups:\n",
        "        ax2.text(x_r*1.01, np.mean(y_centers[idxs]), sp_name,\n",
        "                 va='center', ha='left', fontsize=7.5, color='#555555',\n",
        "                 style='italic', transform=ax2.transData)\n\n",
        "x_max_val = np.nanmax(val_matrix)\n",
        "ax2.set_xlim(0, min(x_max_val * 1.30, 105))\n",
        "ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))\n",
        "ax2.set_xlabel('% of Benchmark Gap Closed (vs. Global Best)', labelpad=8)\n",
        "ax2.set_title('KPI Gap Reduction by Recommendation\\n'\n",
        "              'vs. Global Best \u2014 2029 Q4 (KPIs with non-zero impact only)',\n",
        "              fontsize=14, fontweight='bold', pad=14)\n",
        "ax2.legend(loc='lower right', frameon=True, framealpha=0.95,\n",
        "           edgecolor='#cccccc', fontsize=9, title='Scenario', title_fontsize=9)\n",
        "ax2.grid(axis='x', color='#e5e5e5', linewidth=0.7, zorder=0)\n",
        "ax2.grid(axis='y', visible=False)\n",
        "plt.tight_layout(pad=1.5)\n\n",
        "out2_png = os.path.join(OUTPUT_DIR, 'kpi_gap_reduction_2029q4.png')\n",
        "out2_pdf = os.path.join(OUTPUT_DIR, 'kpi_gap_reduction_2029q4.pdf')\n",
        "fig2.savefig(out2_png, dpi=EXPORT_DPI, bbox_inches='tight')\n",
        "fig2.savefig(out2_pdf, bbox_inches='tight')\n",
        "print(f'Saved: {out2_png}')\n",
        "print(f'Saved: {out2_pdf}')\n",
        "plt.show()"
    ]
})

cells.append({
    "cell_type": "markdown", "id": "d0e1f2a3", "metadata": {},
    "source": [
        "### Figure 2 \u2014 Key Takeaway\n\n",
        "**Policy impact is highly concentrated, not evenly spread, across Canada\u2019s AI competitiveness KPIs.** Several patterns are clear:\n\n",
        "- **Talent KPIs respond primarily to Rec 1 (Career Moats)**: AI Talent Score, AI Hiring Rate, and Net Migration of AI Skills show the largest gap closures, confirming these policies are well-targeted at Canada\u2019s most visible weakness.\n",
        "- **Commercial and Development KPIs respond most to Rec 2 (Scale AI) and Rec 3 (B2B Demand)**: Adoption, commercial score, and investment metrics improve under these recommendations, reflecting their demand-side and deployment focus.\n",
        "- **The \u201cAll Three Combined\u201d bars (navy) are the largest across every category**, confirming the recommendations work as a complementary system.\n",
        "- **KPIs with all-zero values (primarily Infrastructure and some Research metrics) are excluded from this chart**, flagging them as a second-phase policy agenda beyond the scope of these three recommendations.\n\n",
        "**Decision-maker implication:** Rec 1 builds the talent foundation; Rec 2 and Rec 3 accelerate commercialization. Only together do they close the gaps that move Canada\u2019s global rank."
    ]
})

cells.append({
    "cell_type": "markdown", "id": "e1f2a3b4", "metadata": {},
    "source": [
        "---\n## Overall Takeaway \u2014 Canada AI Competitiveness Policy Package\n\n",
        "**1. Inaction is a declining trajectory.** Without policy change, Canada slides from 5th to 6th place by mid-2027 and stays there through 2029.\n\n",
        "**2. The three recommendations are individually beneficial but collectively transformational.** None alone reaches the 4th-place target; only the combined package approaches it by 2029 Q4, and robustly so across the uncertainty simulation.\n\n",
        "**3. The KPI evidence explains why the combined package wins.** Rec 1 closes talent gaps, Rec 2 accelerates commercial deployment, Rec 3 stimulates B2B demand \u2014 complementary levers, not substitutes.\n\n",
        "**4. Some gaps require a second-phase agenda.** Infrastructure and research-volume KPIs show zero movement under these three recommendations. Closing those gaps demands capital-intensive interventions outside the current policy package.\n\n",
        "**Recommended action:** Pursue all three recommendations in parallel, prioritize early implementation, and begin designing the infrastructure/research phase before current-package gains plateau."
    ]
})

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"}
    },
    "cells": cells
}

out_path = os.path.join(os.path.dirname(__file__), 'canada_ai_policy_visualizations.ipynb')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

size = os.path.getsize(out_path)
print(f'Written: {out_path}  ({size:,} bytes, {len(cells)} cells)')
