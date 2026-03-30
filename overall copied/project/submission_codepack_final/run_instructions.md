# Run Instructions

## Environment setup
1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Notebook execution order
1. Open notebooks/submission_final_pipeline.ipynb
2. Run all cells from top to bottom.
3. Optional: open notebooks/reproduce_ai_competitiveness_baseline_original_copy.ipynb for baseline-only reproduction reference.

## What each notebook run produces
- Section 2 (baseline):
  - outputs/tables/baseline_country_scores.csv
  - outputs/tables/baseline_kpi_scores.csv
  - outputs/tables/validation_report.md
- Section 4 (impact matrix):
  - outputs/tables/impact_matrix.csv
  - outputs/tables/impact_matrix_long.csv
- Section 5 (simulation):
  - outputs/tables/simulation_summary.csv
  - outputs/tables/country_quarter_scores.csv
  - outputs/tables/canada_kpi_trajectories.csv
  - outputs/tables/canada_rank_trajectory.csv
  - outputs/tables/scenario_comparison.csv
- Section 7 (attribution):
  - outputs/tables/kpi_gap_reduction_by_recommendation.csv
  - outputs/tables/kpi_gap_reduction_peer_best.csv
  - outputs/tables/kpi_gap_reduction_global_best.csv
  - outputs/figures/recommendation_kpi_heatmap.png
  - outputs/figures/rec1_gap_reduction.png
  - outputs/figures/rec2_gap_reduction.png
  - outputs/figures/rec3_gap_reduction.png
  - outputs/figures/combined_gap_reduction.png

## Notes
- All paths are relative to package root.
- No web scraping/API/authenticated session is required.
- If running in Colab, upload the package and run notebook from the notebooks folder.
