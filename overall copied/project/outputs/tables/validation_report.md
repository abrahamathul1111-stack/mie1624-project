# Baseline Validation Report

## Inputs
- Workbook: `C:\Users\dayab\UofT\WINTER 2026\MIE1624H Intro to Data\course project\EXECUTION\project\data\raw\AI_Competitiveness_Rankings_and_Weights (1) - Copy.xlsx`
- Canada gap CSV: `C:\Users\dayab\UofT\WINTER 2026\MIE1624H Intro to Data\course project\EXECUTION\project\data\raw\canada_combined_kpi_weights_gaps - Copy.csv`
- Sheet mapping: KPI Scores and Weights -> KPI Scores and Weights, Final Rankings -> Final Rankings
- Countries detected: 13
- KPI columns detected: 26

## Summary
- Canada composite recomputed to 32.864453 and displays as 32.86.
- Canada rank recomputed to 5 of 13.
- No ambiguous sheet mapping was required because both expected workbook sheet names were present exactly.
- Canada pillar scores are validated from the Canada gap CSV because it carries explicit pillar-level share columns.

## Validation Checks
| section | check | actual | expected | passed | note |
| --- | --- | --- | --- | --- | --- |
| Workbook | Sheet mapping | KPI Scores and Weights -> KPI Scores and Weights, Final Rankings -> Final Rankings | KPI Scores and Weights, Final Rankings | PASS | Exact sheet names were present, so no fallback mapping was needed. |
| Workbook | Country count | 13 | 13 | PASS |  |
| Workbook | KPI count | 26 | 26 | PASS |  |
| Weights | Talent L1 weight | 0.2456 | 0.2456 | PASS |  |
| Weights | Infrastructure L1 weight | 0.0870 | 0.0870 | PASS |  |
| Weights | Operating Environment L1 weight | 0.0424 | 0.0424 | PASS |  |
| Weights | Research L1 weight | 0.2136 | 0.2136 | PASS |  |
| Weights | Development L1 weight | 0.1655 | 0.1655 | PASS |  |
| Weights | Commercial Ecosystem L1 weight | 0.1930 | 0.1930 | PASS |  |
| Weights | Government Strategy L1 weight | 0.0529 | 0.0529 | PASS |  |
| Weights | Level 1 weight sum | 1.0000 | 1.0000 | PASS |  |
| Weights | Talent L2 weights | 31.10 / 14.39 / 17.49 / 10.23 / 14.30 / 12.49 | 31.10 / 14.39 / 17.49 / 10.23 / 14.30 / 12.49 | PASS |  |
| Weights | Infrastructure L2 weights | 38.88 / 29.64 / 12.37 / 8.41 / 10.70 | 38.88 / 29.64 / 12.37 / 8.41 / 10.70 | PASS |  |
| Weights | Operating Environment L2 weights | 51.68 / 12.83 / 16.18 / 19.31 | 51.68 / 12.83 / 16.18 / 19.31 | PASS |  |
| Weights | Research L2 weights | 40.33 / 19.56 / 19.56 / 13.31 / 7.23 | 40.33 / 19.56 / 19.56 / 13.31 / 7.23 | PASS |  |
| Weights | Development L2 weights | 60.00 / 40.00 | 60.00 / 40.00 | PASS |  |
| Weights | Commercial Ecosystem L2 weights | 53.90 / 29.73 / 16.38 | 53.90 / 29.73 / 16.38 | PASS |  |
| Weights | Government Strategy L2 weights | 100.00 | 100.00 | PASS |  |
| Canada Targets | Talent score | 41.9401 | 41.94 | PASS |  |
| Canada Targets | Infrastructure score | 40.9220 | 40.92 | PASS |  |
| Canada Targets | Operating Environment score | 69.8187 | 69.82 | PASS |  |
| Canada Targets | Research score | 28.8220 | 28.82 | PASS |  |
| Canada Targets | Development score | 15.8000 | 15.80 | PASS |  |
| Canada Targets | Commercial Ecosystem score | 10.2702 | 10.27 | PASS |  |
| Canada Targets | Government Strategy score | 100.0000 | 100.00 | PASS |  |
| Canada Targets | Canada composite score | 32.864453 | 32.8645 | PASS |  |
| Canada Targets | Canada displayed composite score | 32.86 | 32.86 | PASS |  |
| Canada Targets | Canada rank | 5 | 5 | PASS |  |
| Weights | Implementation pillar weight | 0.3751 | 0.3751 | PASS | Validated from the Canada gap CSV pillar summary columns. |
| Weights | Innovation pillar weight | 0.3790 | 0.3790 | PASS | Validated from the Canada gap CSV pillar summary columns. |
| Weights | Investment pillar weight | 0.2459 | 0.2459 | PASS | Validated from the Canada gap CSV pillar summary columns. |
| Canada Targets | Implementation pillar score | 44.8557 | 44.8557 | PASS | Validated from the Canada gap CSV, which carries pillar-level shares. |
| Canada Targets | Innovation pillar score | 23.1360 | 23.1360 | PASS | Validated from the Canada gap CSV, which carries pillar-level shares. |
| Canada Targets | Investment pillar score | 29.5734 | 29.5734 | PASS | Validated from the Canada gap CSV, which carries pillar-level shares. |
| Canada Spot Checks | Tortoise Talent Score | 31.28 | 31.28 | PASS |  |
| Canada Spot Checks | AI Hiring Rate YoY Ratio | 73.73 | 73.73 | PASS |  |
| Canada Spot Checks | Net Migration Flow of AI Skills | 48.96 | 48.96 | PASS |  |
| Canada Spot Checks | Tortoise Infrastructure Score | 77.05 | 77.05 | PASS |  |
| Canada Spot Checks | Compute Hardware Index | 3.61 | 3.61 | PASS |  |
| Canada Spot Checks | Energy Resilience Score | 86.16 | 86.16 | PASS |  |
| Canada Spot Checks | Tortoise Operating Environment Score | 93.94 | 93.94 | PASS |  |
| Canada Spot Checks | Open Data Score | 92.86 | 92.86 | PASS |  |
| Canada Spot Checks | Tortoise Research Score | 30.67 | 30.67 | PASS |  |
| Canada Spot Checks | AI Publications (Total) | 34.73 | 34.73 | PASS |  |
| Canada Spot Checks | AI Citations (% of World Total) | 10.72 | 10.72 | PASS |  |
| Canada Spot Checks | Notable AI Models | 2.50 | 2.50 | PASS |  |
| Canada Spot Checks | Tortoise Development Score | 25.78 | 25.78 | PASS |  |
| Canada Spot Checks | AI Patent Grants (per 100k) | 0.83 | 0.83 | PASS |  |
| Canada Spot Checks | Tortoise Commercial Score | 14.88 | 14.88 | PASS |  |
| Canada Spot Checks | AI Investment Activity | 3.16 | 3.16 | PASS |  |
| Canada Spot Checks | AI Adoption (%) | 8.00 | 8.00 | PASS |  |
| Canada Spot Checks | Tortoise Government Strategy Score | 100.00 | 100.00 | PASS |  |
| Ranking | Full country rank order | United States of America > China > South Korea > Singapore > Canada > United Kingdom > Germany > India > Israel > France > UAE > Japan > Spain | United States of America > China > South Korea > Singapore > Canada > United Kingdom > Germany > India > Israel > France > UAE > Japan > Spain | PASS |  |
| Ranking | Composite scores reproduce workbook display | 0.006260 | <= 0.010000 | PASS | The workbook stores displayed two-decimal composites, so an exact delta of zero is not expected. |
| Cross-file | Canada gap KPI alignment | Matched 26 KPI rows by order, names, weights, and sources | Exact match | PASS |  |

## Canada Pillar Scores From Gap CSV
| Pillar | Weight | Canada Score |
| --- | --- | --- |
| Implementation | 0.3751 | 44.8557 |
| Innovation | 0.3790 | 23.1360 |
| Investment | 0.2459 | 29.5734 |

## Exports
- `baseline_country_scores.csv` contains recomputed country-level sub-pillar, pillar, composite, and workbook comparison columns.
- `baseline_kpi_scores.csv` contains country/KPI scores, workbook weights, and weighted KPI contributions.
- This report is written as `validation_report.md` beside the CSV outputs.
