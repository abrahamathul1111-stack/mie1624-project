# Revised Phase 6 Dashboard Specification (dashboard_spec_v1)

## Assumptions used

1. **Phase 6 is presentation-only.** The scoring engine, calibration logic, recommendation-to-KPI mapping, Monte Carlo backend, and gap-attribution logic are already frozen from Phases 1–5. Dashboard work should only consume existing outputs and not introduce new modeled values.

2. **The simulation horizon is 16 quarters (2026Q1 to 2029Q4).**  
   Available scenario labels in the current outputs are:
   - `baseline`
   - `rec1_only`
   - `rec2_only`
   - `rec3_only`
   - `all_recommendations`

3. **Canada baseline for display purposes is the 2026Q1 starting point.**
   - baseline composite score: **32.864**
   - baseline rank: **#5**
   - baseline subpillar anchors: Talent **41.94**, Commercial Ecosystem **10.27**, Development **15.80**, Government Strategy **100.00**

4. **For dynamic ranking views, competitor drift is already embedded in the simulation outputs.**  
   This means Canada’s baseline score can stay flat while its rank changes over time. In the current files, Canada’s baseline rank slips from **#5** to **#6** by the later quarters, so the dashboard should not assume a fixed baseline rank across the full horizon.

5. **Dashboard A is static and executive-facing.**  
   It should use:
   - baseline 2026Q1 values for current-state framing
   - quarter 16 / 2029Q4 values for recommendation impact and stand-alone gap-closure comparisons

6. **Dashboard B is dynamic and simulation-facing.**  
   It should default to:
   - scenario = `all_recommendations`
   - time view = **median**
   - quarter = current slider selection
   - optional uncertainty toggle = on/off for p10–p90 only where files support it

7. **Benchmarking rule for the main presentation:**  
   Use **peer-cluster best** as the default benchmark in Dashboard A.  
   Use **global best** only as an optional appendix/secondary toggle because the current file `kpi_gap_reduction_by_recommendation.csv` contains both benchmark modes.

8. **Success metrics are intentionally separate from competitiveness KPIs.**  
   The bottom-left chart in Dashboard A must use operational implementation metrics from `success_metrics_tracking.csv`, not KPI-engine metrics such as Tortoise scores or AI Adoption.

9. **Success-metric data is available for the primary Phase 6 chart.**  
   The current file now contains a usable primary success metric for each recommendation:
   - R1: Core AI team attrition among supported firms (**20 → 15**)
   - R2: % of subsidized pilots converting to paid commercial contracts (**25 → 50+**)
   - R3: % of credit-subsidized deployments converting to multi-year commercial contracts (**25 → 50+**)

10. **Important credibility caveat for success metrics:**  
    The current baselines for R2 and R3 are credible **federal analog proxies**, not AI-only observed baselines. They are dashboard-usable, but this proxy status should be footnoted.

---

## Dashboard A specification

### Dashboard A role

**Dashboard A = Executive Overview Dashboard**

This is the boardroom page. It should answer four questions quickly:

1. What are the 3 structural problems?
2. What is the action under each problem?
3. How will we know each action is operationally working?
4. Which competitiveness KPIs improve by the end of the modeled horizon?

### Recommended canvas and layout

- **Format:** 1920 × 1080 presentation canvas
- **Grid:** 12-column layout
- **Style:** rounded consulting cards, generous whitespace, soft shadows, muted background, dark text, family-tinted cards
- **Card radius:** 20–24 px
- **Spacing:** 20–28 px gutters
- **Label style:** executive language first, file-backed metric labels second

### A0. Header strip

**Purpose**  
Establish the storyline and anchor the baseline.

**Content**
- Title: project story headline
- Subtitle: one-line framing statement
- 3 small KPI chips:
  - Canada baseline rank
  - Canada baseline composite score
  - 2029Q4 `all_recommendations` median composite score and/or rank

**Recommended display values**
- Baseline rank: **#5**
- Baseline composite: **32.86**
- 2029Q4 all-recommendations median composite: **36.93**
- 2029Q4 all-recommendations median rank: **#4**

**Primary files**
- `baseline_country_scores.csv`
- `scenario_comparison.csv`
- `simulation_summary.csv`

**Availability**
- Available now

---

### A1. Problem cards (top row)

Create **3 equal-width problem cards** across the top row.

#### Problem card 1
- **Title:** Canada’s AI Talent Paradox
- **Short diagnosis:** High acquisition, weak retention; Canada trains and attracts talent but leaks senior value creation south.
- **Evidence chip:** **20% attrition baseline**
- **Support chip:** baseline Talent score or talent-related KPI callout if needed

**Primary text sources**
- `PROBLEM AND RECOMMENDATION 1&2.pptx`
- `MIE1624_Final_Project.pptx`

**Supporting data sources**
- `success_metrics_tracking.csv`
- `baseline_country_scores.csv`
- `baseline_kpi_scores.csv`

#### Problem card 2
- **Title:** The Commercialization “Valley of Death”
- **Short diagnosis:** Canada produces research and technical feasibility, but scale-up and domestic commercial capture remain weak.
- **Evidence chip:** **Commercial Ecosystem score = 10.27**
- **Optional support chip:** Recommendation 2 contract conversion baseline proxy = **25%**

**Primary text sources**
- `PROBLEM AND RECOMMENDATION 1&2.pptx`
- `MIE1624_Final_Project.pptx`

**Supporting data sources**
- `baseline_country_scores.csv`
- `success_metrics_tracking.csv`

#### Problem card 3
- **Title:** Weak Market Validation / First-Customer Gap
- **Short diagnosis:** Risk-averse adoption and weak first-buyer pathways stop domestic firms from proving market value.
- **Evidence chip:** **R3 conversion baseline proxy = 25%**
- **Optional support chip:** **Launch-registry baseline proxy = 44 firms**

**Primary text sources**
- `PROBLEM AND RECOMMENDATION 3.pdf`
- `MIE1624_Final_Project.pptx`

**Supporting data sources**
- `success_metrics_tracking.csv`
- `baseline_kpi_scores.csv`

**Availability**
- Available now

**Design note**  
Each problem card should use the tinted background for its recommendation family.

---

### A2. Recommendation / action cards (middle row)

Place **3 action cards directly below the 3 problem cards** so the top half reads as a paired story: problem above, answer below.

Each recommendation card should contain:
- recommendation title
- one-sentence objective
- 2–3 action bullets
- small footer tags showing the most relevant operational action IDs or lever groups if needed
- a compact horizon chip (`1–3 years`)

#### Recommendation card 1
- **Recommendation title:** Build Career Moats for Talent
- **Use action wording from files:**
  - Elite equity tax exemption
  - 1:1 salary-matching tax credit
  - AI Elite fast-track visa / PR mechanism

**Primary files**
- `PROBLEM AND RECOMMENDATION 1&2.pptx`
- `MIE1624_Final_Project.pptx`
- `docs/decisions/recommendation_kpi_mapping.md`
- `data/processed/impact_matrix_long.csv`

#### Recommendation card 2
- **Recommendation title:** Build the Conditions to Scale AI in Canada
- **Use action wording from files:**
  - Compute utilization / access support
  - Procurement / pilot-to-contract conversion
  - Growth-stage co-investment / later-stage capital

**Primary files**
- `PROBLEM AND RECOMMENDATION 1&2.pptx`
- `MIE1624_Final_Project.pptx`
- `docs/decisions/recommendation_kpi_mapping.md`
- `data/processed/impact_matrix_long.csv`
- `calibration_effects.csv`

#### Recommendation card 3
- **Recommendation title:** Stimulate B2B Demand via Adoption Credits
- **Use action wording from files:**
  - Refundable first-customer AI adoption credit
  - Canadian-owned/IP eligibility rules
  - conversion mandate / clawback logic

**Primary files**
- `PROBLEM AND RECOMMENDATION 3.pdf`
- `docs/decisions/recommendation_kpi_mapping.md`
- `data/processed/impact_matrix_long.csv`
- `calibration_effects.csv`

**Availability**
- Available now

**Design note**  
Do not place long mechanism text on the card face. Use a short executive objective line and 2–3 bullets only.

---

### A3. Bottom-left chart = Success metrics of recommendations/actions

**Recommended chart form**  
Use **3 vertically stacked bullet/progress mini-cards** inside one panel, not one shared-axis bar chart.

**Why**
- The success metrics have different units and different target semantics.
- One shared axis would be visually misleading.
- Mini-cards let each recommendation have a clearly labeled current state, target marker, and direction-of-success.

**Panel purpose**  
Show whether each recommendation is operationally succeeding, separate from whether competitiveness KPIs are improving.

**Exact content**
- one bullet/progress visual per recommendation
- current value shown as a filled bar
- target shown as a marker / vertical line / goal chip
- status label:
  - `needs improvement`
  - `on path`
  - `target met`  
  (status logic can be computed visually but should not invent new performance categories if not implemented)

**Primary metric to use for each recommendation**
- **R1:** Core AI team attrition among supported firms — **20 → 15**
- **R2:** % of subsidized pilots converting to paid commercial contracts — **25 → 50+**
- **R3:** % of credit-subsidized deployments converting to multi-year commercial contracts — **25 → 50+**

**Optional secondary metrics**
Only show as footnotes, hover text, or small callout chips if there is space:
- R3 launch registry: **44 → 200+**
- R3 anchor-adopter deals: **11 → 25–40**

**Primary file**
- `success_metrics_tracking.csv`

**Availability**
- Available now for the primary chart

**Required chart logic**
- reverse-direction display for R1 because **lower is better**
- normal upward display for R2 and R3 because **higher is better**
- show source-confidence footnote marker because R2 and R3 use federal analog proxies

**Do not do**
- Do not use Tortoise scores here
- Do not use AI Adoption (%) here if it is already in the KPI chart
- Do not place all metrics on one axis

**Footnote required**
> R2 and R3 current baselines are proxy operational analogs from federal commercialization / first-buyer programs, not AI-only observed program baselines.

---

### A4. Bottom-right chart = AI competitiveness KPI improvement / gap-closure view

**Recommended chart form**  
Use a **3-panel benchmark gap-closure dumbbell chart**.

Each panel corresponds to one recommendation and contains **3 KPI rows**.

Each KPI row should show:
- baseline Canada score
- stand-alone scenario score at 2029Q4
- peer-cluster best benchmark score
- labeled `% of gap closed`

**Why**
- It shows movement, remaining distance, and benchmark context at the same time.
- It is more executive-friendly than a technical waterfall.
- It aligns with the current `kpi_gap_reduction_by_recommendation.csv` structure without inventing extra transformations.

**Default benchmark mode**
- `benchmark_type = peer_best`

**Optional toggle**
- secondary toggle = `global_best`

**Quarter to use**
- `quarter_index = 16` only  
  (because the current file contains final-quarter attribution only)

**Recommended KPI selection rule**
Use 3 KPI rows per recommendation:
- prefer highest positive `percent_gap_reduction`
- keep only recommendation-relevant KPIs
- avoid duplicate low-information rows with 0% reduction

**Recommended default KPI rows**
- **R1:** Tortoise Talent Score; Relative AI Skill Penetration; Net Migration Flow of AI Skills
- **R2:** Tortoise Commercial Score; AI Investment Activity; AI Adoption (%)
- **R3:** AI Adoption (%); Tortoise Commercial Score; AI Investment Activity

**Primary file**
- `kpi_gap_reduction_by_recommendation.csv`

**Supporting files**
- `data/processed/impact_matrix_long.csv`
- `docs/decisions/recommendation_kpi_mapping.md`

**Availability**
- Available now

**Design note**
Use one color family per recommendation panel:
- baseline point = neutral slate
- improvement segment = recommendation family core
- post-policy point = recommendation family dark
- benchmark marker = charcoal / dark neutral

**Required caveat under chart**
> Each recommendation is shown as a separate stand-alone counterfactual against the same Canada baseline. These impacts are not additive.

---

## Dashboard B specification

### Dashboard B role

**Dashboard B = Policy Timeline Simulation Dashboard**

This is the dynamic execution page. It should answer:
1. When do policy levers start?
2. Which KPIs move first?
3. How does Canada’s score and rank change quarter by quarter?
4. What does the scenario look like relative to the rest of the field?

### Recommended canvas and layout

- **Format:** 1920 × 1080 presentation canvas
- **Structure:** control ribbon at top, Gantt timeline in upper half, KPI trajectory lower-left, ranking lower-right, small chips upper-right
- **Look and feel:** cleaner than the current reference, less cluttered, fewer but larger marks

### B0. Control ribbon

**Purpose**  
Provide simulation control in a presentation-friendly way.

**Controls**
- play / pause button
- quarter slider (1–16)
- scenario selector dropdown
- optional uncertainty toggle
- optional benchmark toggle (peer/global) if needed for auxiliary annotations

**Default state**
- scenario = `all_recommendations`
- quarter = `2029Q4` on first render for the story frame, with playback available back to 2026Q1
- view = `median`

**Primary files**
- `simulation_summary.csv`
- `scenario_comparison.csv`
- `canada_rank_trajectory.csv`

**Availability**
- Available now

---

### B1. Policy-action timeline / Gantt

**Purpose**  
Show when the levers start and when they are expected to reach full modeled effect.

**Recommended visual**
- grouped Gantt / lane chart
- group lanes by recommendation
- one bar per lever
- start = `start_quarter`
- end = `full_effect_quarter`
- bar style / pattern label = `rollout_pattern`

**Rows (joined from files)**
- R1 / rec1_lever1 — High-skill immigration fast-track and STEM-prioritized PR pathway
- R1 / rec1_lever2 — Transition-to-PR retention pipeline
- R2 / rec2_lever1 — Direct co-investment and commercialization-stage support
- R2 / rec2_lever2 — R&D tax incentives / direct funding for commercialization-ready firms
- R3 / rec3_lever1 — Refundable adoption subsidy / voucher for first deployment
- R3 / rec3_lever2 — Lead-customer validation / procurement-style demand pull

**Primary files**
- `implementation_schedule.csv`
- `calibration_effects.csv`
- `calibration_lags.csv`

**Availability**
- Available now

**Design note**
- bar color by recommendation family
- inline labels on bars, not a separate legend if space allows
- show full-effect quarter as a darker end cap or marker

---

### B2. Selected KPI trajectory chart

**Purpose**  
Show which Canada KPIs move first and how they evolve over time under the selected scenario.

**Recommended visual**
- multi-line trajectory chart
- limit to **3–5 KPI lines**
- default line = median
- optional shaded band = p10 to p90
- endpoint labels shown directly on the right edge

**Default KPI watchlist**
- Tortoise Talent Score
- Tortoise Commercial Score
- AI Investment Activity
- AI Adoption (%)
- Tortoise Development Score

**Alternative watchlist option**
Allow a small selector if Codex can support it; otherwise hard-code the default 5.

**Primary file**
- `canada_kpi_trajectories.csv`

**Availability**
- Available now

**Important note**
The file contains p10 / median / p90 values, so uncertainty can be shown for KPI lines if desired.

**Design note**
- keep max 5 lines
- avoid a dense legend; direct-label line ends
- if scenario = `rec1_only`, favor the R1 family tint for the most relevant lines and neutralize the rest
- if scenario = `all_recommendations`, use a neutral multi-line palette to avoid implying that all KPI lines belong to one recommendation family

---

### B3. Country ranking bar chart

**Purpose**  
Show Canada’s selected-quarter position versus the country field.

**Recommended visual**
- horizontal sorted bar chart
- one bar per country
- Canada highlighted strongly
- all other countries neutral or muted
- optional thin outline for peer-cluster countries

**Default data view**
- selected scenario
- selected quarter
- ranking based on `composite_score`

**Primary file**
- `country_quarter_scores.csv`

**Supporting file**
- `simulation_summary.csv`

**Availability**
- Available now

**Design note**
- Canada bar = Canada highlight red
- non-Canada bars = slate/grey
- label top 6 or all countries depending on available width
- keep this chart clean; no uncertainty ribbons

---

### B4. Selected-quarter score chips

**Purpose**  
Provide quick readout for the selected scenario and quarter.

**Recommended chips**
- Canada composite score (median)
- Canada rank (median)
- delta vs baseline at same quarter
- delta vs start (optional)

**Primary files**
- `simulation_summary.csv`
- `scenario_comparison.csv`
- `canada_rank_trajectory.csv`

**Availability**
- Available now

**Recommended default content**
For 2029Q4:
- `all_recommendations`: composite **36.93**, rank **#4**
- `rec1_only`: composite **33.87**, rank **#5**
- `rec2_only`: composite **34.42**, rank **#4**
- `rec3_only`: composite **34.36**, rank **#4**

---

## Data mapping table

| dashboard | section | visual / component | purpose | primary files | key fields | already available? | additional data needed |
|---|---|---|---|---|---|---|---|
| A | A0 | header strip + chips | anchor baseline and 2029Q4 outcome | `baseline_country_scores.csv`, `scenario_comparison.csv`, `simulation_summary.csv` | `composite_score`, `rank`, `composite_score_median`, `rank_median` | Yes | none |
| A | A1 | problem cards | show 3 structural failures | `PROBLEM AND RECOMMENDATION 1&2.pptx`, `PROBLEM AND RECOMMENDATION 3.pdf`, `MIE1624_Final_Project.pptx`, `baseline_country_scores.csv`, `success_metrics_tracking.csv` | narrative text, evidence chips | Yes | none |
| A | A2 | recommendation cards | show 3 action packages | `PROBLEM AND RECOMMENDATION 1&2.pptx`, `PROBLEM AND RECOMMENDATION 3.pdf`, `docs/decisions/recommendation_kpi_mapping.md`, `data/processed/impact_matrix_long.csv`, `calibration_effects.csv` | recommendation names, lever names, rationale, KPI tags | Yes | none |
| A | A3 | success-metric mini bullet cards | show operational success of each recommendation | `success_metrics_tracking.csv` | `metric_name`, `current_value`, `target_value`, `unit`, `recommendation_id`, `notes` | Yes | none for primary chart |
| A | A4 | 3-panel KPI gap-closure dumbbell | show recommendation-level KPI improvement vs benchmark at end of horizon | `kpi_gap_reduction_by_recommendation.csv`, `data/processed/impact_matrix_long.csv` | `scenario`, `benchmark_type`, `baseline_canada_score`, `scenario_canada_score`, `benchmark_score`, `percent_gap_reduction` | Yes | none |
| B | B0 | controls | playback and scenario selection | `simulation_summary.csv`, `scenario_comparison.csv`, `canada_rank_trajectory.csv` | `scenario`, `quarter_index`, `quarter` | Yes | none |
| B | B1 | policy-action Gantt | show rollout timing | `implementation_schedule.csv`, `calibration_effects.csv`, `calibration_lags.csv` | `recommendation_id`, `lever_id`, `start_quarter`, `full_effect_quarter`, `rollout_pattern`, `lever_name` | Yes | none |
| B | B2 | KPI trajectory chart | show quarter-by-quarter KPI evolution | `canada_kpi_trajectories.csv` | `scenario`, `quarter`, `kpi`, `kpi_score_p10`, `kpi_score_median`, `kpi_score_p90` | Yes | none |
| B | B3 | country ranking bar chart | show Canada’s position vs country field | `country_quarter_scores.csv` | `scenario`, `quarter`, `country`, `rank`, `composite_score` | Yes | none |
| B | B4 | selected-quarter score chips | quick score / rank readout | `simulation_summary.csv`, `scenario_comparison.csv` | `composite_score_median`, `rank_median`, `composite_score_delta_vs_baseline`, `rank_delta_vs_baseline` | Yes | none |

---

## Missing data gaps

### No blocking data gap remains for the core Phase 6 build

The currently attached files are sufficient to build both dashboard faces with real project data.

### Remaining non-blocking gaps / cautions

1. **R2 and R3 success baselines are analog proxies.**  
   The current `success_metrics_tracking.csv` uses supportable federal analog baselines for commercialization / first-buyer conversion, but they are not AI-only observed baselines. This is acceptable for the dashboard if footnoted.

2. **`kpi_gap_reduction_by_recommendation.csv` is end-horizon only.**  
   It supports a static Dashboard A impact view, but not a quarter-by-quarter gap-closure animation. If you later want dynamic gap closure by quarter, a new export would be needed.

3. **Narrative labels and backend IDs should be cross-walked once before build.**  
   Example:
   - `Build Career Moats for Talent` ↔ `rec1_only`
   - `Build the Conditions to Scale AI in Canada` ↔ `rec2_only`
   - `Stimulate B2B Demand via Adoption Credits` ↔ `rec3_only`  
   This can be handled in a front-end mapping object and does not require a new data file.

4. **Problem-card proof points should remain limited.**  
   The source decks contain more text than the dashboard should display. The build should deliberately shorten narrative copy rather than import full paragraphs.

---

## Color palette with hex codes

### Family 1 — Problem 1 / Recommendation 1 (Talent / retention)

| role | hex | use |
|---|---|---|
| dark | `#183B66` | active headers, key labels, post-policy marker |
| core | `#4F7CCB` | main bar/line/segment |
| light | `#AFC6F2` | secondary fill, muted segment |
| tint | `#EEF4FF` | card background tint |

### Family 2 — Problem 2 / Recommendation 2 (Commercialization / scale-up)

| role | hex | use |
|---|---|---|
| dark | `#7A4614` | active headers, key labels, post-policy marker |
| core | `#D4832E` | main bar/line/segment |
| light | `#F2BE84` | secondary fill, muted segment |
| tint | `#FFF4E8` | card background tint |

### Family 3 — Problem 3 / Recommendation 3 (Adoption / first-customer market pull)

| role | hex | use |
|---|---|---|
| dark | `#0F5C55` | active headers, key labels, post-policy marker |
| core | `#2E9C8F` | main bar/line/segment |
| light | `#98D9CF` | secondary fill, muted segment |
| tint | `#EAF8F5` | card background tint |

### Neutrals / background / Canada highlight

| role | hex | use |
|---|---|---|
| page background | `#F7F8FA` | full canvas background |
| card background | `#FFFFFF` | inner card surface |
| card border | `#D9E0EA` | border / separators |
| primary text | `#1F2937` | titles and labels |
| secondary text | `#667085` | subtitles, notes |
| muted neutral | `#B7C2D6` | tracks, baseline points, inactive bars |
| dark neutral | `#344054` | benchmark markers / dark accents |
| gridline | `#E5E7EB` | chart grids |
| Canada highlight | `#D52B1E` | Canada bar in ranking chart |
| Canada light fill | `#FDECEC` | Canada annotation chip / subtle highlight |

### Color application rules

1. **Dashboard A only:**  
   Recommendation/problem family colors must be used consistently across:
   - problem card tint
   - recommendation card accent strip
   - success-metric mini-card
   - corresponding KPI gap-closure panel

2. **Dashboard B:**  
   Keep the timeline bars recommendation-colored.  
   Keep the ranking chart Canada-highlighted in red.  
   Keep the KPI trajectory chart cleaner and more neutral if the scenario is `all_recommendations`.

3. **Benchmark markers:**  
   Use dark neutral, not a recommendation family color.

4. **Baseline points:**  
   Use muted neutral, not black.

---

## Executive chart titles

### Dashboard A

- **Main title:** Canada’s AI competitiveness problem is conversion, not strategy
- **Subtitle:** Three federal-style actions to retain talent, scale firms, and create domestic demand

- **Problem card 1:** Talent in, value out
- **Problem card 2:** Research is not becoming scale
- **Problem card 3:** No first customer, no flywheel

- **Bottom-left chart title:** How we will know each recommendation is working
- **Bottom-left subtitle:** Operational success metrics, separate from competitiveness KPIs

- **Bottom-right chart title:** Where each recommendation closes Canada’s KPI gap by 2029Q4
- **Bottom-right subtitle:** Stand-alone impact vs peer-cluster best benchmark

### Dashboard B

- **Main title:** Policy timeline simulation: Canada’s competitiveness path quarter by quarter
- **Subtitle:** Quarterly policy rollout, KPI movement, and rank position under the selected scenario

- **Timeline title:** When the policy levers start to bite
- **KPI chart title:** Selected KPI trajectories
- **KPI chart subtitle:** Median path with optional p10–p90 band
- **Ranking chart title:** Canada’s position versus the field
- **Chips title (if needed):** Selected-quarter outcome

---

## Prompt to collect missing success-metric data

### Current status
No new data collection is required to build the **primary** success-metrics chart in Dashboard A.

### Use the prompt below only if you want to replace the current R2/R3 proxy baselines with stricter AI-only operational baselines

```text
You are collecting stricter operational success-metric baselines for Phase 6 of a Canada AI competitiveness dashboard.

Goal:
Replace or strengthen the current proxy baselines for Recommendation 2 and Recommendation 3 with the most supportable Canada-relevant, AI-specific operational metrics available from credible sources.

Dashboard recommendations:
R2 = Commercialization / scale-up
R3 = First-customer market pull / adoption

Required output schema:
metric_name,recommendation_id,action_id,current_value,target_value,unit,baseline_date,target_horizon,source,confidence,notes

Rules:
- Use only authoritative sources: Government of Canada, Statistics Canada, ISED, NRC-IRAP, BDC, CIFAR, OECD, Stanford HAI, Tortoise, official program evaluations, and official budget/program documents.
- Do not invent any baselines or targets.
- If no AI-specific baseline exists, leave current_value blank and explain why.
- Prefer operational implementation metrics, not competitiveness KPIs.
- Metrics must remain separate from the KPI engine.

Priority metrics to research:
1. % of subsidized pilots converting to paid commercial contracts
2. % of first-customer / supported deployments converting to multi-year commercial contracts
3. count of pre-qualified Canadian AI scale-ups eligible for first-customer procurement support
4. count of anchor-adopter / first-buyer deals supporting Canadian AI scale-ups

Return:
1. CSV-ready rows only
2. a short note on what remains unavailable
3. source links and dates in notes if the value is proxy-based
```

---

## Codex handoff summary

### Build objective

Create **two polished presentation-style dashboards** from existing Phase 1–5 outputs without inventing any new values.

### Dashboard A build instructions

1. Use a **card-based executive layout**.
2. Top row = 3 problem cards.
3. Middle row = 3 recommendation cards aligned vertically under the matching problem.
4. Bottom-left = success metrics panel using only `success_metrics_tracking.csv`.
5. Bottom-right = KPI gap-closure panel using only `kpi_gap_reduction_by_recommendation.csv` plus recommendation/KPI mapping files.

### Dashboard A file usage

- narrative text:
  - `PROBLEM AND RECOMMENDATION 1&2.pptx`
  - `PROBLEM AND RECOMMENDATION 3.pdf`
  - `MIE1624_Final_Project.pptx`

- current-state / baseline values:
  - `baseline_country_scores.csv`
  - `baseline_kpi_scores.csv`
  - `canada_combined_kpi_weights_gaps.csv`

- operational success chart:
  - `success_metrics_tracking.csv`

- KPI impact chart:
  - `kpi_gap_reduction_by_recommendation.csv`
  - `data/processed/impact_matrix_long.csv`
  - `docs/decisions/recommendation_kpi_mapping.md`

### Dashboard A chart rules

- Success metrics chart must **not** reuse KPI-engine metrics.
- Use the primary metric rows only for the visible chart:
  - R1 attrition
  - R2 pilot-to-contract conversion
  - R3 deployment-to-multi-year conversion
- Use `benchmark_type = peer_best` by default for the KPI gap-closure panel.
- Show a footnote that recommendation impacts are **stand-alone and non-additive**.
- Show a footnote that R2/R3 current success-metric baselines are **federal analog proxies**.

### Dashboard B build instructions

1. Use a clean simulation layout with:
   - top control ribbon
   - policy-action timeline
   - KPI trajectory chart
   - country ranking chart
   - selected-quarter chips

2. Use scenario selector values exactly as:
   - `baseline`
   - `rec1_only`
   - `rec2_only`
   - `rec3_only`
   - `all_recommendations`

3. Default state:
   - scenario = `all_recommendations`
   - quarter = `2029Q4`
   - view = median

### Dashboard B file usage

- controls / chips:
  - `simulation_summary.csv`
  - `scenario_comparison.csv`
  - `canada_rank_trajectory.csv`

- timeline:
  - `implementation_schedule.csv`
  - `calibration_effects.csv`
  - `calibration_lags.csv`

- KPI trajectories:
  - `canada_kpi_trajectories.csv`

- ranking chart:
  - `country_quarter_scores.csv`

### Dashboard B chart rules

- Timeline bars should be colored by recommendation family.
- KPI trajectory chart should keep 3–5 lines max.
- Country ranking chart should highlight Canada in `#D52B1E`.
- Do not overload Dashboard B with all 26 KPIs at once.
- Allow optional p10–p90 shading only where the source file actually supports it.

### Final design rules

- Dashboard A must use family-aligned colors for each problem/recommendation.
- Dashboard B should be cleaner and more neutral overall.
- All labels should be executive-facing and presentation-ready.
- No dummy values.
- No technical calibration text on the chart face.
- Any non-obvious proxy metric should be footnoted, not hidden.

