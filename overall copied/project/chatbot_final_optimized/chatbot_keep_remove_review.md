# Chatbot Keep/Remove Review

## Definitely Keep

- Runtime code and imports: `app/`, `src/`, `requirements.txt`.
- Loader-facing structured data: `data/`, `outputs/tables/`.
- Dashboard evidence and audit trail: `outputs/reports/dashboard_*`.
- Decision traceability docs used for narrative grounding: `DOCS/DECISIONS/`.
- Final demo HTML dashboards:
  - `outputs/dashboard/overview_dashboard_interactive_v2_bold.html`
  - `outputs/dashboard/timeline_dashboard_interactive_v2.html`
- Core narrative context:
  - `context/MIE1624_Final_Report_WithSuccessMetrics.docx`
  - `context/reproduce_ai_competitiveness_baseline.ipynb`

## Likely Remove / Exclude (Applied)

- Duplicate methodology family in separate context folder when canonical copy already retained in `outputs/reports/technical_methodology_*`.
- Non-interactive dashboard screenshots and static snapshot assets.
- Alternate/obsolete dashboard variants not in current demo path.
- Superseded package docs replaced by this optimized documentation set.
- Notebook setup helper not required for dashboard/chatbot runtime path.

## Uncertain Keep (Flagged)

- `context_core/MIE1624_Final_Report_WithCharts.docx` from original package:
  - Excluded to keep package lean.
  - Can be re-added if evaluator explicitly requires chart-heavy prose rather than final-success narrative doc.

## Deduplication Principle Used

When duplicate families existed, one canonical copy was kept based on:

1. Alignment with current loader/runtime path.
2. Alignment with final dashboard outputs.
3. Richness and traceability of context for explanation.
4. Lower packaging footprint.
