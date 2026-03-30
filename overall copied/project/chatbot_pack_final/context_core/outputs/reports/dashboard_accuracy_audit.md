# Dashboard Accuracy Audit

## Source Files Used

- DOCS/DECISIONS/dashboard_spec_v1.md
- DOCS/DECISIONS/model_scope_v1.md
- DOCS/DECISIONS/recommendation_kpi_mapping.md
- src/dashboard/dashboard_config.py
- app/export_dashboard_copies_html_v2.py
- outputs/tables/baseline_country_scores.csv
- outputs/tables/baseline_kpi_scores.csv
- outputs/tables/scenario_comparison.csv
- outputs/tables/simulation_summary.csv
- outputs/tables/country_quarter_scores.csv
- outputs/tables/canada_rank_trajectory.csv
- outputs/tables/canada_kpi_trajectories.csv
- outputs/tables/kpi_gap_reduction_by_recommendation.csv
- outputs/tables/impact_matrix_long.csv
- data/processed/impact_matrix_long.csv
- data/calibration/implementation_schedule.csv
- data/calibration/calibration_effects.csv
- data/calibration/calibration_lags.csv
- data/processed/success_metrics_tracking.csv
- data/raw/canada_combined_kpi_weights_gaps.csv
- data/raw/PROBLEM AND RECOMMENDATION 1&2.pptx
- data/raw/PROBLEM AND RECOMMENDATION 3.pdf
- data/raw/MIE1624_Final_Project.pptx
- data/raw/Methodology_Report.docx

## What Was Checked

- Problems, recommendation titles, and recommendation action bullets against configuration and decision documents.
- KPI names and baseline KPI values in overview bottom-right chart against baseline_kpi_scores.csv.
- Recommendation-to-KPI impact linkage against peer_best quarter_index=16 values in kpi_gap_reduction_by_recommendation.csv.
- Success metrics panel values against success_metrics_tracking.csv with direction handling.
- Sensitive KPI set: Compute Hardware Index, Tortoise Talent Score, Tortoise Commercial Score, Tortoise Development Score, AI Investment Activity, AI Adoption (%), AI Hiring Rate YoY Ratio.
- Baseline and projected rank/composite values against baseline_country_scores.csv and scenario_comparison.csv.
- Timeline action start/full-effect quarters and rollout pattern against implementation_schedule.csv and calibration files.
- Timeline KPI and rank quarter alignment against canada_kpi_trajectories.csv, country_quarter_scores.csv, and canada_rank_trajectory.csv.
- Scenario labels and quarter labeling behavior in timeline dashboard components.

## Errors Found

1. Overview recommendation-impact logic in bottom-right chart mixed peer-best and global-best behavior via a fallback.
2. Overview success metrics chart included synthetic recommendation impact values not traceable to source data.
3. Timeline default scenario was baseline, conflicting with dashboard specification default of all_recommendations.
4. Timeline Recommendation 2 summary label text diverged from source recommendation label.
5. Timeline quarter text formatting was inconsistent between components.

## What Was Corrected

1. Overview bottom-right recommendation impact now strictly uses peer_best at quarter_index=16 from kpi_gap_reduction_by_recommendation.csv.
2. Removed synthetic direct-impact additions from success metrics; chart now shows source-derived current value plus gap to target.
3. Added overview source-traceable summary chips for:
   - Canada baseline rank and composite.
   - 2029Q4 all_recommendations median composite and rank.
4. Timeline default scenario changed to all_recommendations.
5. Timeline Recommendation 2 summary label aligned to source: Build the Conditions to Scale AI in Canada.
6. Timeline quarter labels standardized to YYYYQ# in scenario banner and Gantt x-axis.

## Timeline Errors Found And Corrected

- Corrected scenario default state mismatch to all_recommendations.
- Corrected quarter label formatting mismatch by applying a single quarter index to YYYYQ# mapping rule.
- Confirmed displayed action timing (start quarter and full-effect quarter) follows implementation_schedule.csv mapping through parse_relative_quarter logic.

## What Could Not Be Corrected Due To Missing Data

- impact_matrix_long_validated.csv was not available in the workspace. The audit used impact_matrix_long.csv instead.
- No additional source file provided with recommendation-specific projected success-metric trajectories by quarter; therefore no synthetic per-recommendation success-metric uplift was introduced.

## Alignment Confirmation

- Both dashboards were corrected in the exporter logic and regenerated.
- Audited dashboard values, labels, KPI mapping, rank/composite values, and timeline quarter behavior are traceable to the listed source files.
- Compute Hardware Index was explicitly audited and remains non-recommendation-linked in the overview impact bars, consistent with source mapping scope and peer-best reduction outputs.
