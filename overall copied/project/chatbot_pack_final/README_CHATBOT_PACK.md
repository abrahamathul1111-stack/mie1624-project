# Chatbot Sharing Pack (Final)

## Purpose
This folder is a separate chatbot-focused sharing pack for demo and presentation usage.
It is designed so a chatbot can answer business, technical, and verification questions reliably from the files included here.

This pack is intentionally separate from the professor submission pack.
No files were moved or modified in the main submission package; this pack is copy-only.

## How this pack should be used
The chatbot should be grounded on files in this folder only.
Use the manifest and quickstart to control ingestion order and priority.

Primary guidance files:
- `chatbot_context_quickstart.md`
- `chatbot_context_manifest.csv`

## Folder contents
- `context_core/`
  - Final result tables and reporting artifacts used for executive answers and number verification.
  - Includes baseline/rank/KPI trajectory/scenario/attribution outputs and dashboard QA traceability files.
- `context_technical/`
  - Technical methodology references, assumptions table, inventory table, and decision docs.
  - Primary source for methodology, assumptions, and limitations Q&A.
- `dashboards/`
  - Final dashboard HTML artifacts plus dashboard data bundle/assets used for value traceability.
- `app_or_demo/`
  - App/demo runtime and inspection code for dashboard/chatbot-adjacent demo explanation.
- `optional_reference/`
  - Supporting calibration/raw/processed inputs and notebook references for deeper technical follow-up.

## Primary grounding sources (ingest first)
1. `context_technical/outputs/reports/technical_methodology_reference_phases_1_to_6.md`
2. `context_technical/outputs/reports/technical_methodology_assumptions_table.csv`
3. `context_technical/outputs/reports/technical_methodology_file_inventory.csv`
4. `context_core/outputs/tables/scenario_comparison.csv`
5. `context_core/outputs/tables/canada_rank_trajectory.csv`
6. `context_core/outputs/tables/canada_kpi_trajectories.csv`
7. `context_core/outputs/tables/kpi_gap_reduction_by_recommendation.csv`
8. `context_core/outputs/reports/dashboard_traceability_matrix.csv`
9. `dashboards/outputs/dashboard/overview_dashboard_interactive_v2_bold.html`
10. `dashboards/outputs/dashboard/timeline_dashboard_interactive_v2.html`

## Files required for result verification
- `context_core/outputs/tables/*.csv`
- `context_core/outputs/reports/dashboard_traceability_matrix.csv`
- `context_core/outputs/reports/dashboard_accuracy_audit.md`
- `context_core/outputs/reports/dashboard_corrections_summary.md`
- `dashboards/outputs/dashboard/dashboard_data_bundle/*`

## Files required for technical Q&A
- `context_technical/outputs/reports/technical_methodology_reference_phases_1_to_6.md`
- `context_technical/outputs/reports/technical_methodology_assumptions_table.csv`
- `context_technical/outputs/reports/technical_methodology_file_inventory.csv`
- `context_technical/DOCS/DECISIONS/*.md`

## Supplementary references
- `context_core/*.docx`
- `optional_reference/data/*`
- `optional_reference/notebooks/*`
- `app_or_demo/*` for runtime/inspection questions

## Known limitations
- Some methodology documents use original repository-relative paths (for example `outputs/...`, `DOCS/...`, `src/...`).
- In this pack, those files are included under themed folders (`context_core/`, `context_technical/`, `app_or_demo/`, etc.).
- Use `chatbot_context_manifest.csv` to map included files and priorities.
- See `missing_or_unresolved_files.md` for path-resolution notes.

## Best-first RAG ingestion order
1. Methodology files in `context_technical/outputs/reports/`
2. Core result tables in `context_core/outputs/tables/`
3. Dashboard traceability and audit files in `context_core/outputs/reports/`
4. Dashboard HTML + data bundle in `dashboards/outputs/dashboard/`
5. Decision docs in `context_technical/DOCS/DECISIONS/`
6. Runtime/demo code in `app_or_demo/`
7. Optional supporting data in `optional_reference/`
