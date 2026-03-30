# Technical Methodology Reference — Phases 1 to 6

## 1. Purpose of this document
This document is the technical companion to the final project deliverables. It records the implemented workflow used to generate baseline scores, calibrated policy effects, quarterly simulation outputs, attribution tables, and dashboard artifacts.

Primary uses:
- reproducibility reference for evaluators and technical reviewers
- grounding source for chatbot Q&A during the final presentation
- traceable map from code and data inputs to final outputs

This is not the business-facing consulting narrative. It is a technical methods record tied to repository implementation.

## 2. Project modeling scope summary
Locked scope reflected in repository code and decision docs:
- Geography and ranking universe: Canada evaluated against 13-country baseline set.
- Recommendation set: three recommendation bundles (`rec1`, `rec2`, `rec3`) with detailed levers.
- Time granularity: quarterly.
- Horizon: 16 quarters starting at `2026Q1` (through `2029Q4`).
- Scenarios simulated in Phase 4:
  - `baseline`
  - `rec1_only`
  - `rec2_only`
  - `rec3_only`
  - `all_recommendations`
- Uncertainty reporting: Monte Carlo draw distribution summarized with p10 / median / p90.
- Benchmark views in attribution outputs:
  - `peer_best` (labeled "Peer-Cluster Best")
  - `global_best`
- Attribution framing: stand-alone counterfactual per scenario (non-additive across recommendations).

## 3. End-to-end data flow across Phases 1–6
Pipeline implemented in code:

raw workbook + canada gap csv
-> Phase 1 baseline reconstruction + validation
-> Phase 2 calibration libraries (effect size / lag / drift / rollout schedule)
-> Phase 3 recommendation-to-KPI impact metadata + wide matrix
-> Phase 4 quarterly Monte Carlo simulation (5 scenarios)
-> Phase 5 KPI gap reduction attribution (peer/global benchmark views)
-> Phase 6 dashboard data loading + chart payloads + HTML dashboard exports

Representative path map:
- Phase 1 outputs feed Phases 3, 4, 5, 6.
- Phase 2 calibration files feed Phases 3, 4, 6.
- Phase 3 outputs feed Phase 4 and dashboard context.
- Phase 4 outputs feed Phase 5 and Phase 6.
- Phase 5 outputs feed Phase 6 overview impact panels.

## 4. Phase-by-phase methodology

## 4.1 Phase 1 — Baseline rebuild and validation
### Objective
Reconstruct baseline country and KPI scores from the source workbook, validate Canada targets and rank ordering, and produce canonical baseline tables used by downstream phases.

### Why this phase was necessary
All simulation and attribution steps require a stable baseline state. If baseline KPI and country scores are not reproduced deterministically, subsequent policy impact and rank-change analysis is not trustworthy.

### Main input files
- `data/raw/AI_Competitiveness_Rankings_and_Weights (1).xlsx`
  - sheets: `KPI Scores and Weights`, `Final Rankings`
- `data/raw/canada_combined_kpi_weights_gaps.csv`
- code:
  - `src/scoring/baseline_reproduction.py`
  - `src/io/xlsx_package.py`

### Main output files
- `outputs/tables/baseline_country_scores.csv`
- `outputs/tables/baseline_kpi_scores.csv`
- `outputs/tables/validation_report.md`

### Core methods used
1. Workbook loading and strict sheet mapping:
- `load_xlsx_sheets` reads workbook XML and preserves blanks.
- `map_required_sheet_names` validates required sheets with deterministic matching.

2. KPI metadata extraction:
- Parses pillar, sub-pillar, L1 sub-pillar weights, KPI names, KPI L2 weights, scales.
- Builds long KPI table by country with:
  - `kpi_score`
  - `weighted_kpi_score = kpi_score * kpi_weight`

3. Sub-pillar and country aggregation:
- `subpillar_score = sum(weighted_kpi_score within subpillar)`
- `weighted_subpillar_score = subpillar_score * subpillar_weight`
- `composite_score = sum(weighted_subpillar_score across subpillars)`
- country rank is recomputed from descending composite score.

4. AHP weight validation:
- Validates expected L1 and L2 weights against hard-coded expected maps in `baseline_reproduction.py`.

5. Cross-file consistency checks:
- Aligns workbook metadata to `canada_combined_kpi_weights_gaps.csv` by order/names/weights/source/scale.

### Assumptions introduced
- Workbook values used in this phase are treated as scoring-ready values (no additional normalization step in this baseline rebuild module).
- Country universe is fixed to 13 countries.
- Expected schema/labels in workbook are fixed; deviations fail fast.

### Validation / QA checks
Implemented in `build_validation_checks` and emitted to `validation_report.md`:
- required sheet presence and mapping
- country count = 13, KPI count = 26
- L1/L2 weight checks and weight sums
- Canada sub-pillar and pillar target checks
- Canada composite and rank checks
- full country rank-order match against workbook
- cross-file alignment with Canada gap CSV

### Key implementation notes
- No artifact named `baseline_master_table` is created in current code. Closest baseline master outputs are:
  - `baseline_country_scores.csv` (country-level master)
  - `baseline_kpi_scores.csv` (KPI-level master)
- Baseline outputs include workbook comparison fields and deltas.

## 4.2 Phase 2 — External calibration library
### Objective
Provide external calibration priors for policy effect magnitude, response lags, competitor drift, and rollout timing.

### Why this phase was necessary
The simulation engine needs policy-response parameters and competitor movement assumptions not directly available in baseline tables.

### Main input files
- `data/calibration/calibration_effects.csv`
- `data/calibration/calibration_lags.csv`
- `data/calibration/competitor_drift.csv`
- `data/calibration/implementation_schedule.csv`
- supporting methodology notes:
  - `DOCS/DECISIONS/calibration_notes.md`

### Main output files
Phase 2 is primarily parameter-library creation (input artifacts consumed downstream). No separate executable output table is required beyond these calibration CSVs.

### Core methods used
1. Effect calibration structure (`calibration_effects.csv`):
- stores low/base/high textual anchors and confidence labels by lever.
- later converted into numeric multipliers/coefficient scaling in Phase 3 and uncertainty multipliers in Phase 4.

2. Lag calibration structure (`calibration_lags.csv`):
- stores low/base/high lag quarter values and ramp archetype.
- later mapped from lag class to lag quarters and sampled in Phase 4.

3. Competitor drift priors (`competitor_drift.csv`):
- cluster-level drift anchors by KPI bundles.
- used in Phase 4 to generate quarterly drift rates for non-Canada countries.

4. Implementation schedule (`implementation_schedule.csv`):
- defines `start_quarter`, `full_effect_quarter`, and `rollout_pattern` per lever.

### Assumptions introduced
- Low/base/high anchors are proxied from adjacent evidence where direct AI-only policy elasticities are unavailable.
- Confidence labels (`weak`, `medium`, etc.) are explicit uncertainty signals used in later scaling.
- `implementation_schedule.csv` includes inferred starter assumptions (explicitly noted in file `notes` column).

### Validation / QA checks
- Required-column validation in downstream loaders (`policy_impact_matrix.py`, `state_transition.py`, `load_dashboard_data.py`).
- Lever-id uniqueness and cross-file lever-id integrity are checked in Phase 4 input loader.

### Key implementation notes
- This phase is intentionally calibration-oriented and not causal-identification complete.
- Evidence strength is encoded as confidence categories, then converted to numeric factors downstream.

## 4.3 Phase 3 — Recommendation-to-KPI impact matrix
### Objective
Translate recommendations/levers into simulation-ready KPI effect coefficients and lag metadata.

### Why this phase was necessary
It is the bridge between policy design language and quantitative simulation inputs.

### Main input files
- `data/processed/impact_matrix_long.csv` (recommendation/lever/KPI mapping)
- `data/calibration/calibration_effects.csv`
- `data/calibration/calibration_lags.csv`
- `outputs/tables/baseline_kpi_scores.csv`
- code: `src/scoring/policy_impact_matrix.py`

### Main output files
- `outputs/tables/impact_matrix_long.csv` (enriched long metadata)
- `outputs/tables/impact_matrix.csv` (wide lever x KPI matrix)

### Core methods used
1. Mapping ingestion:
- Requires columns including `effect_strength`, `lag_class`, `directness`.

2. Lever and recommendation canonicalization:
- Recommendation names map to `rec1`/`rec2`/`rec3` IDs.
- Lever text maps to deterministic lever configs (`lever_id`, default archetypes).

3. Archetype assignment logic:
- `choose_effect_archetype` and `choose_lag_archetype` apply lever/KPI-specific overrides (especially for commercialization vs research/development KPIs).

4. Numeric coefficient conversion:
- starts from strength bucket base values:
  - 0 -> 0.0000
  - 1 -> 0.0100
  - 2 -> 0.0250
  - 3 -> 0.0400
- applies anchor parsing from `effect_low/base/high` text.
- applies confidence scaling (`CONFIDENCE_FACTORS`).
- applies sign from `effect_direction`.
- outputs `numeric_coefficient` in scale `normalized_0_to_1_additive_delta_at_full_adoption`.

5. Lag conversion:
- lag class -> selected calibrated lag quarters:
  - immediate -> low lag
  - medium -> base lag
  - long -> high lag

6. Matrix generation:
- wide pivot: rows = lever_name, columns = baseline KPI list, values = `numeric_coefficient`.
- missing cells filled with 0.

### Assumptions introduced
- direct/indirect/spillover flags are structural priors from mapping file, not estimated causal effects.
- effect anchors are parsed from text and bounded conservatively.
- lever-to-archetype borrow rules are hand-specified where exact calibration rows are unavailable.

### Validation / QA checks
- baseline KPI existence check for each mapped KPI.
- duplicate `(lever_name, KPI)` detection.
- required-column checks for all inputs.
- cross-consistency between long metadata and wide matrix.

### Key implementation notes
- Long vs wide outputs are both required:
  - long = full metadata + rationale fields
  - wide = simulation-ready coefficient matrix
- This phase explicitly links policy wording to modeled KPI channels.

## 4.4 Phase 4 — Simulation engine
### Objective
Simulate quarterly KPI, composite, and rank trajectories across five scenarios using calibrated policy effects plus competitor drift and Monte Carlo uncertainty.

### Why this phase was necessary
This phase produces the core counterfactual trajectories and headline scenario outcomes used by attribution and dashboards.

### Main input files
- `outputs/tables/baseline_country_scores.csv`
- `outputs/tables/baseline_kpi_scores.csv`
- `outputs/tables/impact_matrix.csv`
- `outputs/tables/impact_matrix_long.csv`
- `data/calibration/implementation_schedule.csv`
- `data/calibration/calibration_effects.csv`
- `data/calibration/calibration_lags.csv`
- `data/calibration/competitor_drift.csv`
- code: `src/simulation/state_transition.py`

### Main output files
- `outputs/tables/simulation_summary.csv`
- `outputs/tables/country_quarter_scores.csv`
- `outputs/tables/canada_kpi_trajectories.csv`
- `outputs/tables/canada_rank_trajectory.csv`
- `outputs/tables/scenario_comparison.csv`

### Core methods used
1. Time and scenario setup:
- quarterly index from `2026Q1`, length 16.
- scenarios from `SCENARIO_DEFINITIONS`.

2. Baseline matrix construction:
- country x KPI baseline matrix from baseline KPI export.
- KPI metadata-derived aggregation tensors:
  - KPI -> sub-pillar weights
  - sub-pillar -> pillar shares
  - sub-pillar absolute weights

3. Policy shift modeling (Canada only):
- active recommendations selected per scenario.
- schedule profile generated from `start_quarter`, `full_effect_quarter`, `rollout_pattern`.
- effect profile combines:
  - implementation rollout shape
  - lag response curve by ramp type
- coefficient converted to score-point shift with `* 100` scale.

4. Competitor drift modeling (non-Canada):
- cluster priors parsed from textual anchors in `competitor_drift.csv`.
- per cluster/KPI low-base-high quarterly rates generated.
- Monte Carlo triangular sampling for drift rates.
- Canada excluded from competitor-drift updates.

5. Monte Carlo draws and uncertainty:
- default draws = 10000 per scenario.
- per quarter, per metric, computes percentiles:
  - p10 = 10th percentile
  - median = 50th percentile
  - p90 = 90th percentile

6. Score and rank recomputation each quarter:
- sub-pillar score via KPI weighted aggregation.
- pillar score via sub-pillar shares.
- composite score via sub-pillar absolute weights.
- ranks recomputed per draw by descending composite with deterministic tie-break.

### Assumptions introduced
- Canada policy effects modeled as additive KPI-point shifts on baseline Canada vector.
- Competitors evolve through drift toward upper bound via rate term:
  - update form: `state += drift_rate * ((100 - state)/100)`
- Uncertainty sampling is triangular around calibrated low/base/high settings.

### Validation / QA checks
- required-column and schema checks on all input tables.
- country count and KPI count checks.
- impact metadata and matrix consistency check.
- baseline recomputation check from KPI matrix to composite scores.
- lever-id cross-file integrity checks across metadata/effects/lags/schedule.

### Key implementation notes
- `quarterly_simulation.py` and `monte_carlo.py` exist as utility modules, but Phase 4 project outputs are generated by `state_transition.py`.
- Reported dashboard values typically use median paths, while p10/p90 remain available in outputs.

## 4.5 Phase 5 — KPI gap reduction attribution
### Objective
Quantify how each stand-alone recommendation scenario reduces Canada’s KPI gap versus benchmarks at final horizon.

### Why this phase was necessary
Simulation outputs show trajectories, but attribution is needed to express KPI-level policy contribution relative to benchmark gaps.

### Main input files
- `outputs/tables/baseline_kpi_scores.csv`
- `outputs/tables/canada_kpi_trajectories.csv`
- code: `src/simulation/recommendation_attribution.py`

### Main output files
- `outputs/tables/kpi_gap_reduction_by_recommendation.csv`
- `outputs/tables/kpi_gap_reduction_peer_best.csv`
- `outputs/tables/kpi_gap_reduction_global_best.csv`
- `outputs/figures/recommendation_kpi_heatmap.png`
- `outputs/figures/rec1_gap_reduction.png`
- `outputs/figures/rec2_gap_reduction.png`
- `outputs/figures/rec3_gap_reduction.png`
- `outputs/figures/combined_gap_reduction.png`

### Core methods used
1. Benchmark construction from baseline KPI table:
- `peer_best`: best KPI score within Canada’s mapped cluster peers.
- `global_best`: best KPI score globally across all baseline countries.

2. Final-quarter scenario extraction:
- uses maximum quarter in `canada_kpi_trajectories.csv`.

3. Gap formulas per KPI and benchmark:
- `baseline_gap = max(benchmark_score - baseline_canada_score, 0)`
- `post_policy_gap = max(benchmark_score - scenario_canada_score, 0)`
- `absolute_gap_reduction = baseline_gap - post_policy_gap`
- `percent_gap_reduction = (absolute_gap_reduction / baseline_gap) * 100` when baseline gap > 0 else 0

### Assumptions introduced
- attribution is evaluated at final quarter snapshot (not cumulative path decomposition).
- scenarios are treated as independent stand-alone counterfactuals.

### Validation / QA checks
- required scenario presence in trajectory file.
- duplicate `(scenario, kpi)` at final quarter disallowed.
- alignment checks between benchmark frame and scenario rows.

### Key implementation notes
- Output uses benchmark types `peer_best` and `global_best` (labels include "Peer-Cluster Best").
- Stand-alone scenario effects are not additive by design; overlap and interaction prevent simple summation.

## 4.6 Phase 6 — Dashboard build
### Objective
Create presentation-facing interactive dashboards (overview and timeline) from modeled outputs with traceable data linkage.

### Why this phase was necessary
Phases 1–5 produce technical tables; Phase 6 packages key outputs into decision-oriented visuals for final presentation use.

### Main input files
Core data dependencies loaded by dashboard loader (`src/dashboard/load_dashboard_data.py`):
- `outputs/tables/baseline_country_scores.csv`
- `outputs/tables/baseline_kpi_scores.csv`
- `outputs/tables/simulation_summary.csv`
- `outputs/tables/scenario_comparison.csv`
- `outputs/tables/country_quarter_scores.csv`
- `outputs/tables/canada_rank_trajectory.csv`
- `outputs/tables/canada_kpi_trajectories.csv`
- `outputs/tables/kpi_gap_reduction_by_recommendation.csv`
- `outputs/tables/impact_matrix_long.csv` (or `data/processed/impact_matrix_long.csv`)
- `data/calibration/implementation_schedule.csv`
- `data/calibration/calibration_effects.csv`
- `data/calibration/calibration_lags.csv`
- `data/processed/success_metrics_tracking.csv`

Primary code:
- `app/dashboard_overview_copy.py`
- `app/dashboard_timeline_copy.py`
- `app/export_dashboard_copies_html_v2.py`
- `src/dashboard/dashboard_config.py`
- `src/dashboard/load_dashboard_data.py`
- `src/visualization/dashboard_copy_components.py`

### Main output files
- interactive HTML outputs:
  - `outputs/dashboard/overview_dashboard_interactive_v2_bold.html`
  - `outputs/dashboard/timeline_dashboard_interactive_v2.html`
  - (export script also generates `overview_dashboard_interactive_v2.html` and timeline v2 variants)
- dashboard QA/reporting artifacts:
  - `outputs/reports/dashboard_traceability_matrix.csv`
  - `outputs/reports/dashboard_corrections_summary.md`
  - `outputs/reports/dashboard_data_inventory.md`
  - `outputs/reports/dashboard_unresolved_dependencies.md`

### Core methods used
1. Data loading + schema validation:
- loader enforces required columns and logs unresolved dependencies.

2. Overview payload construction:
- composes summary chips, problem cards, recommendation cards, success metrics transforms, and KPI impact mapping.
- uses simulation and attribution outputs for terminal-quarter values.

3. Timeline payload construction:
- quarter slider + scenario selection.
- renders timeline action bars (schedule + calibration joins), KPI lines, and country rank bars.

4. Export path:
- `export_dashboard_copies_html_v2.py` writes self-contained HTML with embedded payload JSON and Plotly rendering logic.

### Assumptions introduced
- Dashboard headline uses median path values for clarity.
- Dashboard is simplified view of model outputs (selected KPIs/actions).
- Success metrics include proxy operational analogs for some recommendation tracking metrics.

### Validation / QA checks
- explicit traceability matrix linking dashboard sections to source fields.
- corrections summary documents post-audit fixes (including scenario defaults and quarter label consistency).
- unresolved dependency report is generated when optional files are absent.

### Key implementation notes
- Dashboard vocabulary avoids over-claiming causal certainty; it visualizes model-driven scenario outputs.
- Probability distributions are not front-and-center on main dashboard views even though backend p10/p90 exist in outputs.

## 5. Algorithms, formulas, and modeling logic used across phases

### 5.1 Baseline aggregation logic
- KPI contribution:
  - `weighted_kpi_score = kpi_score * kpi_weight`
- Sub-pillar:
  - `subpillar_score = sum(weighted_kpi_score)`
  - `weighted_subpillar_score = subpillar_score * subpillar_weight`
- Composite:
  - `composite_score = sum(weighted_subpillar_score across all subpillars)`

### 5.2 Country ranking logic
- Country rank is recomputed by sorting descending composite score.
- Ties are deterministically resolved in simulation rank function.

### 5.3 Impact coefficient logic (Phase 3)
- Base strength coefficients from `effect_strength` bucket (0/1/2/3).
- Coefficient scaled by:
  - parsed anchor magnitude from low/base/high textual calibration
  - confidence factor
  - effect direction sign
- Output:
  - `numeric_coefficient` in normalized additive scale.

### 5.4 KPI transition logic (Phase 4)
For each quarter and draw:
- Non-Canada drift update:
  - `state_next = state + drift_rate * ((100 - state) / 100)` (clipped to [0, 100])
- Canada policy update:
  - `canada_state = baseline_canada + policy_shift` (clipped to [0, 100])
- Policy shift derived from:
  - implementation profile from schedule
  - lagged response curve from lag class/ramp type
  - coefficient scaled to score points

### 5.5 Monte Carlo logic
- Draw-level uncertainty uses triangular sampling for:
  - competitor drift rates (low/base/high)
  - effect multipliers around coefficient by confidence band
  - lag realization within class-calibrated bounds
- Percentiles used in outputs:
  - p10 = 10th percentile
  - median = 50th percentile
  - p90 = 90th percentile

### 5.6 Attribution formulas
Implemented exactly in recommendation attribution module:
- `baseline_gap = benchmark_score - canada_baseline_score` (floored at 0)
- `post_policy_gap = benchmark_score - canada_postpolicy_score` (floored at 0)
- `gap_reduction_absolute = baseline_gap - post_policy_gap`
- `gap_reduction_percent = gap_reduction_absolute / baseline_gap` (if baseline_gap > 0)

### 5.7 Dashboard mapping logic
- Overview cards and timeline visuals map directly to simulation/attribution/calibration outputs.
- Dashboard traceability matrix records source file, fields, and transform rule for each displayed element.

## 6. Assumptions register

### Data assumptions
- Baseline workbook is treated as canonical scoring source for the 13-country, 26-KPI setup.
- Country universe remains fixed; changing it can alter relative scaling and ranks.
- Importance: strong

### Calibration assumptions
- External anchors are often adjacent-policy proxies (not always AI-only direct estimates).
- Confidence labels convert to numeric uncertainty scaling factors.
- Importance: strong

### Rollout/timing assumptions
- `implementation_schedule.csv` includes inferred starter timings and rollout patterns.
- Lag realization sampled around calibrated low/base/high values per lag class.
- Importance: strong

### Competitor drift assumptions
- Non-Canada countries drift by cluster/KPI priors; Canada drift is policy-shift based.
- Drift anchors are parsed from textual priors and mapped to bounded quarterly rates.
- Importance: moderate to strong

### Attribution assumptions
- Attribution compares stand-alone scenarios at final quarter.
- Recommendation effects are non-additive in combined interpretation.
- Importance: strong

### Dashboard simplification assumptions
- Dashboard foregrounds median path and selected KPI subsets.
- Backend uncertainty exists but is simplified in executive views.
- Importance: moderate

## 7. Output file map

| phase | file | purpose | used downstream in phase(s) |
|---|---|---|---|
| 1 | `outputs/tables/baseline_country_scores.csv` | baseline country composite/sub-pillar/pillar table | 3, 4, 6 |
| 1 | `outputs/tables/baseline_kpi_scores.csv` | baseline country-KPI table | 3, 4, 5, 6 |
| 1 | `outputs/tables/validation_report.md` | baseline QA record | reference |
| 2 | `data/calibration/calibration_effects.csv` | effect priors and confidence | 3, 4, 6 |
| 2 | `data/calibration/calibration_lags.csv` | lag priors and ramp types | 3, 4, 6 |
| 2 | `data/calibration/competitor_drift.csv` | cluster drift priors | 4 |
| 2 | `data/calibration/implementation_schedule.csv` | rollout timing patterns | 4, 6 |
| 3 | `outputs/tables/impact_matrix_long.csv` | enriched mapping metadata | 4, 6 |
| 3 | `outputs/tables/impact_matrix.csv` | wide lever x KPI coefficients | 4 |
| 4 | `outputs/tables/simulation_summary.csv` | full country-quarter quantiles | 6 |
| 4 | `outputs/tables/country_quarter_scores.csv` | median country-quarter trajectories | 6 |
| 4 | `outputs/tables/canada_kpi_trajectories.csv` | Canada KPI p10/median/p90 trajectory | 5, 6 |
| 4 | `outputs/tables/canada_rank_trajectory.csv` | Canada rank/composite p10/median/p90 trajectory | 5, 6 |
| 4 | `outputs/tables/scenario_comparison.csv` | final-quarter scenario comparison | 6 |
| 5 | `outputs/tables/kpi_gap_reduction_by_recommendation.csv` | KPI gap reduction for stand-alone scenarios | 6 |
| 5 | `outputs/tables/kpi_gap_reduction_peer_best.csv` | peer benchmark subset | 6/reference |
| 5 | `outputs/tables/kpi_gap_reduction_global_best.csv` | global benchmark subset | 6/reference |
| 5 | `outputs/figures/recommendation_kpi_heatmap.png` | KPI gap reduction heatmap | reporting |
| 6 | `outputs/dashboard/overview_dashboard_interactive_v2_bold.html` | overview dashboard artifact | presentation |
| 6 | `outputs/dashboard/timeline_dashboard_interactive_v2.html` | timeline dashboard artifact | presentation |

## 8. How the final result values were obtained

### Example: where did 36.93 come from?
- File: `outputs/tables/scenario_comparison.csv`
- Row: `scenario = all_recommendations`, `quarter_index = 16`
- Field: `composite_score_median = 36.92993718919254`
- Display in dashboard/report is rounded to 36.93.

### Example: how was rank 4 obtained?
- Same row in `scenario_comparison.csv` gives `rank_median = 4.0`.
- Rank is derived in simulation by recomputing country ordering from draw-level composite scores each quarter and taking the median across draws.

### Example: how are KPI gap reduction percentages produced?
- Inputs:
  - Canada baseline KPI from `baseline_kpi_scores.csv`
  - Canada scenario KPI at final quarter from `canada_kpi_trajectories.csv`
  - benchmark KPI (peer/global best) from baseline benchmark construction
- Formula:
  - `percent_gap_reduction = (baseline_gap - post_policy_gap) / baseline_gap * 100`
- Output location:
  - `outputs/tables/kpi_gap_reduction_by_recommendation.csv`

### Example: dashboard values linkage
- Overview summary chips: baseline and final-quarter metrics from `baseline_country_scores.csv` and `scenario_comparison.csv`.
- Timeline chart values: selected scenario-quarter values from:
  - `country_quarter_scores.csv`
  - `canada_kpi_trajectories.csv`
  - `canada_rank_trajectory.csv`
- Action timeline bars: `implementation_schedule.csv` joined with calibration metadata.

## 9. Known limitations / interpretation notes
- Not every KPI is actively linked to recommendation levers in mapped impact matrix; several remain unaffected in stand-alone outputs.
- Calibration anchors are mixed-quality proxies in several cases; confidence scaling mitigates but does not remove this limitation.
- Stand-alone recommendation effects are non-additive.
- Benchmark choice changes interpretation materially (`peer_best` vs `global_best`).
- Dashboard KPI subsets are intentionally reduced relative to full backend KPI set.
- Some dashboard success metrics are proxy operational analogs, not direct AI-only observed program baselines.

## 10. Appendix

### 10.1 Glossary of scenario names
- `baseline`: no recommendation activated
- `rec1_only`: recommendation 1 stand-alone
- `rec2_only`: recommendation 2 stand-alone
- `rec3_only`: recommendation 3 stand-alone
- `all_recommendations`: combined scenario

### 10.2 Glossary of benchmark names
- `peer_best`: best KPI score among Canada peer-cluster comparator set (labeled Peer-Cluster Best)
- `global_best`: best KPI score globally in baseline country set

### 10.3 Dashboard file names and purpose
- `outputs/dashboard/overview_dashboard_interactive_v2_bold.html`: executive overview with problem/action/impact framing
- `outputs/dashboard/timeline_dashboard_interactive_v2.html`: quarter-by-quarter scenario timeline and rank context

### 10.4 Notes on partially implemented or auxiliary modules
- `src/simulation/quarterly_simulation.py` and `src/simulation/monte_carlo.py` provide reusable utilities.
- Project-critical scenario exports for Phases 4–5 are produced by `src/simulation/state_transition.py` and `src/simulation/recommendation_attribution.py`.
