# Calibration notes

## Sources used
- Statistics Canada
- CIFAR AI impact reporting
- Global Skills Strategy / IRCC Canada
- ISED Departmental Results Reports
- NRC IRAP IP Assist evaluation
- OECD microBeRD and OECD AI / SME digitalisation sources
- Stanford HAI AI Index 2025
- IMDA Singapore Digital Economy 2025
- AI Singapore 100E
- UK AI Sector Study 2024

## Weak assumptions
- No Canada-specific quasi-experimental estimate was found for an AI-only talent-retention subsidy, AI scale-up co-investment facility, or AI first-customer tax credit.
- Most usable calibration numbers are adjacent-policy anchors rather than direct AI-policy elasticities.
- Published evidence rarely reports quarterly lags; lag values should be treated as calibration assumptions informed by program timing.
- There is no authoritative direct mapping from these program outcomes to normalized composite KPI-point gains.

## Manual overrides
- `implementation_schedule.csv` was inferred from lag ranges and ramp descriptions so the downstream simulator has a usable starter schedule.
- `unit` was standardized as `anchor_statistic` in the CSV files because the phase-2 research output reported policy anchors, not consistent causal units.

## Open questions
- Convert anchor statistics into numeric policy-to-KPI translation coefficients in Phase 3 / Phase 4.
- Decide whether each KPI will be simulated directly or through sub-pillars.
- Review implementation start/full-effect quarters against the final federal rollout narrative before dashboard build.
