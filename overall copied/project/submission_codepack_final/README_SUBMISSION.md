# Submission Code Package (Final)

## 1) What this package is
This folder is a clean  code package for course submission. It contains final artifacts needed to run the final analysis pipeline notebook and reproduce canonical model outputs for baseline scoring, impact matrix construction, simulation, and KPI gap attribution.

## 2) How it differs from the full working repository
- Includes: final runnable notebook(s), required source modules, required local data inputs, canonical output examples, and phase traceability/check files.

## 3) Folder structure
- notebooks/: submission notebooks and notebook path helper
- src/: minimal source modules needed for execution
- data/raw/: baseline workbook and Canada gap CSV
- data/processed/: recommendation-to-KPI mapping input
- data/calibration/: calibration libraries (effects/lags/drift/schedule)
- outputs/tables/: canonical CSV outputs and validation report
- outputs/figures/: canonical attribution figures
- docs/decisions/: decision references for methodological context
- docs/phase_map/: phase-to-files traceability
- docs/methodology/: concise methodology note
- checks/: manifest, inclusion/exclusion rationale, dependency map, QA summary
- dashboard/: Phase 6 dashboard component (source snapshot, data bundle, final HTML outputs)

## 4) Notebook run order
1. notebooks/submission_final_pipeline.ipynb
2. notebooks/reproduce_ai_competitiveness_baseline_original_copy.ipynb (optional baseline-only reference)

## 5) Required data files
- data/raw/AI_Competitiveness_Rankings_and_Weights (1).xlsx
- data/raw/canada_combined_kpi_weights_gaps.csv
- data/processed/impact_matrix_long.csv
- data/calibration/calibration_effects.csv
- data/calibration/calibration_lags.csv
- data/calibration/competitor_drift.csv
- data/calibration/implementation_schedule.csv

## 6) Expected outputs
Main notebook generates/refreshes:
- outputs/tables/baseline_country_scores.csv
- outputs/tables/baseline_kpi_scores.csv
- outputs/tables/impact_matrix.csv
- outputs/tables/impact_matrix_long.csv
- outputs/tables/simulation_summary.csv
- outputs/tables/country_quarter_scores.csv
- outputs/tables/canada_kpi_trajectories.csv
- outputs/tables/canada_rank_trajectory.csv
- outputs/tables/scenario_comparison.csv
- outputs/tables/kpi_gap_reduction_by_recommendation.csv
- outputs/tables/kpi_gap_reduction_peer_best.csv
- outputs/tables/kpi_gap_reduction_global_best.csv
- outputs/figures/recommendation_kpi_heatmap.png
- outputs/figures/rec1_gap_reduction.png
- outputs/figures/rec2_gap_reduction.png
- outputs/figures/rec3_gap_reduction.png
- outputs/figures/combined_gap_reduction.png
- dashboard/outputs/overview_dashboard_interactive_v2_bold.html
- dashboard/outputs/timeline_dashboard_interactive_v2.html

## 7) Intentionally excluded
- report and slide drafting assets
- tests and development caches
- duplicate/obsolete raw copies not required by submission notebook

## 8) Colab notes
- Install dependencies from requirements.txt.
- Upload this folder (zip recommended) and run from notebooks/.
- Notebook bootstrap cell sets PROJECT_ROOT relative to notebook location.
- All runtime data access is local-file based (no API/web dependency).

## 9) Limitations
- Monte Carlo run with high draws can be compute-heavy in Colab free tier.
- Dashboard source is included for reproducibility, but optional loader warnings may appear for narrative files that are non-core to chart rendering.
