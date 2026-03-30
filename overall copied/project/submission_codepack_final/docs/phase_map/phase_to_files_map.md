# Phase to Files Map

## Phase 0 — Scope lock
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 1)

Data inputs:
- docs/decisions/model_scope_v1.md

Scripts:
- notebooks/notebook_setup.py

Final outputs:
- checks/included_vs_excluded.md
- checks/submission_manifest.csv

## Phase 1 — Baseline rebuild and validation
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 2)
- notebooks/reproduce_ai_competitiveness_baseline_original_copy.ipynb (reference)

Data inputs:
- data/raw/AI_Competitiveness_Rankings_and_Weights (1).xlsx
- data/raw/canada_combined_kpi_weights_gaps.csv

Scripts:
- src/scoring/baseline_reproduction.py
- src/io/xlsx_package.py
- src/io/data_loading.py

Final outputs:
- outputs/tables/baseline_country_scores.csv
- outputs/tables/baseline_kpi_scores.csv
- outputs/tables/validation_report.md

## Phase 2 — External calibration library
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 3)

Data inputs:
- data/calibration/calibration_effects.csv
- data/calibration/calibration_lags.csv
- data/calibration/competitor_drift.csv
- data/calibration/implementation_schedule.csv

Scripts:
- src/scoring/policy_impact_matrix.py
- src/simulation/state_transition.py

Final outputs:
- calibration tables consumed by Phase 3 and Phase 4

## Phase 3 — Recommendation-to-KPI impact matrix
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 4)

Data inputs:
- data/processed/impact_matrix_long.csv
- outputs/tables/baseline_kpi_scores.csv
- data/calibration/calibration_effects.csv
- data/calibration/calibration_lags.csv

Scripts:
- src/scoring/policy_impact_matrix.py

Final outputs:
- outputs/tables/impact_matrix.csv
- outputs/tables/impact_matrix_long.csv

## Phase 4 — Simulation engine
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 5 and Section 6)

Data inputs:
- outputs/tables/baseline_country_scores.csv
- outputs/tables/baseline_kpi_scores.csv
- outputs/tables/impact_matrix.csv
- outputs/tables/impact_matrix_long.csv
- data/calibration/implementation_schedule.csv
- data/calibration/calibration_effects.csv
- data/calibration/calibration_lags.csv
- data/calibration/competitor_drift.csv

Scripts:
- src/simulation/state_transition.py

Final outputs:
- outputs/tables/simulation_summary.csv
- outputs/tables/country_quarter_scores.csv
- outputs/tables/canada_kpi_trajectories.csv
- outputs/tables/canada_rank_trajectory.csv
- outputs/tables/scenario_comparison.csv

## Phase 5 — KPI gap reduction attribution
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 7)

Data inputs:
- outputs/tables/baseline_kpi_scores.csv
- outputs/tables/canada_kpi_trajectories.csv

Scripts:
- src/simulation/recommendation_attribution.py

Final outputs:
- outputs/tables/kpi_gap_reduction_by_recommendation.csv
- outputs/tables/kpi_gap_reduction_peer_best.csv
- outputs/tables/kpi_gap_reduction_global_best.csv
- outputs/figures/recommendation_kpi_heatmap.png
- outputs/figures/rec1_gap_reduction.png
- outputs/figures/rec2_gap_reduction.png
- outputs/figures/rec3_gap_reduction.png
- outputs/figures/combined_gap_reduction.png

## Phase 6 — Dashboard build (only if relevant to code package)
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 8 references outputs only)

Data inputs:
- outputs/tables/scenario_comparison.csv
- outputs/tables/canada_rank_trajectory.csv
- outputs/tables/canada_kpi_trajectories.csv
- outputs/dashboard/dashboard_data_bundle/*.csv

Scripts:
- app/export_dashboard_copies_html_v2.py
- app/dashboard_overview_copy.py
- app/dashboard_timeline_copy.py
- src/dashboard/dashboard_config.py
- src/dashboard/load_dashboard_data.py
- src/visualization/dashboard_copy_components.py

Final outputs:
- dashboard/outputs/overview_dashboard_interactive_v2_bold.html
- dashboard/outputs/timeline_dashboard_interactive_v2.html
- outputs/dashboard/overview_dashboard_interactive_v2.html (optional rebuild target)
- outputs/dashboard/timeline_dashboard_interactive_v2.html (optional rebuild target)

## Phase 7 — Final reporting assets (only if relevant to code package)
Notebooks:
- notebooks/submission_final_pipeline.ipynb (Section 8)

Data inputs:
- outputs/tables/*.csv (final canonical outputs)

Scripts:
- src/simulation/recommendation_attribution.py (figure exports)

Final outputs:
- outputs/figures/*.png
- outputs/tables/kpi_gap_reduction_*.csv
