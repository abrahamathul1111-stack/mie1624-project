# Recommendation-to-KPI Impact Mapping

## Purpose
This note translates the project's three final recommendations into a simulation-ready recommendation-to-KPI impact matrix for Canada's quarterly AI competitiveness model.

## Source basis
This mapping was built from the uploaded project materials:
- `PROBLEM AND RECOMMENDATION 1&2.pptx`
- `PROBLEM AND RECOMMENDATION 3.pdf`
- `MIE1624_Final_Project.pptx`
- `AI_Competitiveness_Strategy_Analysis_Federal_Only_Revised.docx`
- `Methodology_Report.docx`
- `baseline_kpi_scores.csv`

## Recommendation scope used
1. **Build Career Moats for Talent**
   - Elite equity tax exemption
   - 1:1 salary-matching tax credit
   - AI Elite fast-track visa / PR stream

2. **Build the Conditions to Scale AI in Canada**
   - Compute utilization subsidy for domestic AI firms
   - Growth-stage co-investment and later-stage capital
   - Federal procurement challenge / pilot-to-contract conversion

3. **Stimulate B2B Demand via Adoption Credits**
   - 30–40% refundable first-customer AI adoption tax credit
   - Eligibility rules favoring Canadian-owned IP and Canadian AI scale-ups
   - 18-month conversion mandate with clawback for failed pilots

## Mapping rules used
- **direct**: the lever is explicitly designed to move this KPI or the KPI is named as an addressed / monitored outcome in the project files.
- **indirect**: the KPI should move through a first-order business mechanism, but it is not the main target of the lever.
- **long-run spillover**: the KPI may improve after firm growth, retention, or productization compounds over several quarters.

## Lag classes used
- **immediate** = 1–2 quarters
- **medium** = 3–4 quarters
- **long** = 5–8 quarters

## Deliberate scope decisions
The matrix focuses on **policy-sensitive KPIs** that the three recommendations can plausibly move in a 1–3 year federal strategy window.

### Included as active movers
- Talent KPIs: `Tortoise Talent Score`, `Relative AI Skill Penetration`, `AI Hiring Rate YoY Ratio`, `AI Talent Concentration`, `AI Job Postings (% of Total)`, `Net Migration Flow of AI Skills`
- Innovation / scale conversion KPIs: `Tortoise Research Score`, `Tortoise Development Score`, `AI Patent Grants (per 100k)`, `Notable AI Models`, `Academia-Industry Concentration`
- Commercial KPIs: `Tortoise Commercial Score`, `AI Investment Activity`, `AI Adoption (%)`

### Not mapped as primary movers in this matrix
These were left out because the current three recommendations do not move them cleanly in a quarterly 1–3 year simulation, or because they are already structurally maxed / too indirect:
- `Tortoise Infrastructure Score`
- `Compute Hardware Index`
- `Parts Semiconductor Devices Exports`
- `Internet Speed`
- `Energy Resilience Score`
- `Tortoise Operating Environment Score`
- `AI Social Media Sentiment`
- `Conference Submissions on RAI Topics`
- `Open Data Score`
- `Tortoise Government Strategy Score`

## Summary counts
| recommendation                             |   levers |   kpi_links |   direct_kpis |   indirect_kpis |   spillovers |
|:-------------------------------------------|---------:|------------:|--------------:|----------------:|-------------:|
| Build Career Moats for Talent              |        3 |          17 |             8 |               5 |            4 |
| Build the Conditions to Scale AI in Canada |        3 |          17 |             5 |               6 |            6 |
| Stimulate B2B Demand via Adoption Credits  |        3 |          14 |             5 |               4 |            5 |

## Notes for simulation use
- `Tortoise Commercial Score` is the most cross-cutting downstream KPI and appears in all three recommendations.
- `AI Investment Activity`, `AI Adoption (%)`, and `AI Job Postings (% of Total)` are the most plausible **early-moving** KPIs.
- `Tortoise Talent Score`, `Net Migration Flow of AI Skills`, `Tortoise Development Score`, `AI Patent Grants (per 100k)`, and `Notable AI Models` should generally be treated as **later-moving**.
- For simulation, the matrix is best used as a **structural prior** for sign, lag, and relative strength—not as a claim of causal point estimates.

## Machine-readable file
See `data/processed/impact_matrix_long.csv`.
