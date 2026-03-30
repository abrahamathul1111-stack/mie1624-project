# Notebook Dependency Map

## notebooks/submission_final_pipeline.ipynb

### Imports
- src.scoring.baseline_reproduction.reproduce_baseline
- src.scoring.policy_impact_matrix.build_policy_impact_artifacts
- src.simulation.state_transition.StateTransitionConfig
- src.simulation.state_transition.run_quarterly_state_transition
- src.simulation.recommendation_attribution.export_recommendation_attribution
- pandas

### Datasets read
- data/raw/AI_Competitiveness_Rankings_and_Weights (1).xlsx
- data/raw/canada_combined_kpi_weights_gaps.csv
- data/processed/impact_matrix_long.csv
- data/calibration/calibration_effects.csv
- data/calibration/calibration_lags.csv
- data/calibration/competitor_drift.csv
- data/calibration/implementation_schedule.csv

### Outputs written
- outputs/tables/baseline_country_scores.csv
- outputs/tables/baseline_kpi_scores.csv
- outputs/tables/validation_report.md
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

### Prior phase dependencies
- Phase 3 depends on Phase 1 output: outputs/tables/baseline_kpi_scores.csv
- Phase 4 depends on Phase 1 and Phase 3 outputs
- Phase 5 depends on Phase 1 and Phase 4 outputs

## notebooks/reproduce_ai_competitiveness_baseline_original_copy.ipynb

### Imports
- notebook_setup.ensure_project_root_on_path
- src.scoring.baseline_reproduction.reproduce_baseline

### Datasets read
- data/raw/AI_Competitiveness_Rankings_and_Weights (1) - Copy.xlsx (original reference notebook path)
- data/raw/canada_combined_kpi_weights_gaps - Copy.csv (original reference notebook path)

### Outputs written
- outputs/tables/baseline_country_scores.csv
- outputs/tables/baseline_kpi_scores.csv
- outputs/tables/validation_report.md

### Prior phase dependencies
- Baseline-only notebook; no prior phase dependency.

### Compatibility note
The baseline reference notebook keeps original file references by design. The submission notebook is the canonical runnable notebook for this package and uses canonical local file names without "- Copy" suffixes.
