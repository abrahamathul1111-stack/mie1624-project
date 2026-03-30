# Dashboard Build Notes

## Scope

- Built Dashboard A (Executive Overview) and Dashboard B (Policy Timeline Simulation) using existing Phase 1-5 outputs only.
- Applied dashboard_spec_v1 as source-of-truth for layout, benchmark defaults, caveats, and chart logic.
- Implemented Streamlit + Plotly package with static export helpers.

## Data Caveats

- Success metrics for R2 and R3 are proxy operational analogs and are explicitly footnoted in Dashboard A.
- KPI gap-closure panel uses stand-alone recommendation scenarios and is explicitly labeled non-additive.

## Unresolved Inputs

- Missing required file: impact_matrix_long_validated.csv. Tried: outputs\tables\impact_matrix_long_validated.csv
- Optional validated impact matrix is unavailable: impact_matrix_long_validated.csv. Using impact_matrix_long.csv instead.