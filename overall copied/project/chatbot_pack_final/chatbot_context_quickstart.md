# Chatbot Context Quickstart

## Recommended ingestion order
1. `context_technical/outputs/reports/technical_methodology_reference_phases_1_to_6.md`
2. `context_technical/outputs/reports/technical_methodology_assumptions_table.csv`
3. `context_technical/outputs/reports/technical_methodology_file_inventory.csv`
4. `context_core/outputs/tables/scenario_comparison.csv`
5. `context_core/outputs/tables/canada_rank_trajectory.csv`
6. `context_core/outputs/tables/canada_kpi_trajectories.csv`
7. `context_core/outputs/tables/kpi_gap_reduction_by_recommendation.csv`
8. `context_core/outputs/tables/impact_matrix_long.csv`
9. `context_core/outputs/reports/dashboard_traceability_matrix.csv`
10. `dashboards/outputs/dashboard/overview_dashboard_interactive_v2_bold.html`
11. `dashboards/outputs/dashboard/timeline_dashboard_interactive_v2.html`
12. `context_technical/DOCS/DECISIONS/*.md`

## Minimum context set (fast and reliable)
- `context_technical/outputs/reports/technical_methodology_reference_phases_1_to_6.md`
- `context_technical/outputs/reports/technical_methodology_assumptions_table.csv`
- `context_core/outputs/tables/scenario_comparison.csv`
- `context_core/outputs/tables/canada_rank_trajectory.csv`
- `context_core/outputs/tables/canada_kpi_trajectories.csv`
- `context_core/outputs/tables/kpi_gap_reduction_by_recommendation.csv`
- `context_core/outputs/reports/dashboard_traceability_matrix.csv`
- `dashboards/outputs/dashboard/overview_dashboard_interactive_v2_bold.html`

## Full context set (best accuracy)
Ingest all files listed in `chatbot_context_manifest.csv`, prioritizing `critical` then `high`.

## File subsets by question type

### a) Executive/business answers
- `context_core/outputs/tables/scenario_comparison.csv`
- `context_core/outputs/tables/canada_rank_trajectory.csv`
- `context_core/outputs/tables/kpi_gap_reduction_by_recommendation.csv`
- `context_core/*.docx`
- `dashboards/outputs/dashboard/overview_dashboard_interactive_v2_bold.html`

### b) Technical methodology answers
- `context_technical/outputs/reports/technical_methodology_reference_phases_1_to_6.md`
- `context_technical/outputs/reports/technical_methodology_file_inventory.csv`
- `context_technical/outputs/reports/technical_methodology_assumptions_table.csv`
- `context_technical/DOCS/DECISIONS/*.md`

### c) Dashboard/result verification
- `context_core/outputs/reports/dashboard_traceability_matrix.csv`
- `context_core/outputs/reports/dashboard_accuracy_audit.md`
- `context_core/outputs/reports/dashboard_corrections_summary.md`
- `context_core/outputs/tables/*.csv`
- `dashboards/outputs/dashboard/dashboard_data_bundle/*`

### d) Assumptions/limitations questions
- `context_technical/outputs/reports/technical_methodology_assumptions_table.csv`
- `context_technical/DOCS/DECISIONS/calibration_notes.md`
- `context_technical/DOCS/DECISIONS/model_scope_v1.md`
- `context_core/outputs/reports/dashboard_unresolved_dependencies.md`

### e) Recommendation rationale questions
- `context_technical/DOCS/DECISIONS/recommendation_kpi_mapping.md`
- `context_core/outputs/tables/impact_matrix_long.csv`
- `context_core/outputs/tables/kpi_gap_reduction_by_recommendation.csv`
- `context_core/outputs/tables/scenario_comparison.csv`

### f) Chatbot demo/runtime inspection
- `app_or_demo/requirements.txt`
- `app_or_demo/app/*.py`
- `app_or_demo/src/dashboard/*.py`
- `app_or_demo/src/visualization/*.py`

## Practical note
If context size must be reduced, start with the Minimum context set and add files progressively based on unanswered question types.
