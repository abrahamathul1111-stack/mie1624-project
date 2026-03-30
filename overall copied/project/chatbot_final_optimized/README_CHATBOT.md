# Chatbot Final Optimized Package

This package is a conservative, runnable, and context-complete optimization of the original chatbot package.

## What This Package Contains

- Execution code for Phase 6 dashboard/chatbot context flow (`app/`, `src/`, `requirements.txt`).
- Canonical data inputs needed by loaders and dashboard views (`data/`, `outputs/tables/`).
- Grounding and decision artifacts for explanation traceability (`DOCS/DECISIONS/`, `outputs/reports/`, `context/`).
- Two final interactive dashboard HTML artifacts (`outputs/dashboard/`).
- Packaging documentation and keep/remove audit files (this README plus companion docs).

## Optimization Strategy

- Non-destructive approach: created `chatbot_final_optimized` as a clean copy.
- Kept one canonical copy of duplicated methodology and dashboard context families.
- Removed obvious redundant/non-interactive snapshot artifacts from the optimized package.
- Preserved files needed for runtime loading, explanation traceability, and demo context.

## Included Documentation

- `run_chatbot.md`: exact setup and execution commands.
- `chatbot_manifest.csv`: file-level keep/remove/uncertain manifest.
- `chatbot_keep_remove_review.md`: rationale for keep/exclude/uncertain decisions.
- `chatbot_dependency_map.md`: runtime and context dependency map.
- `chatbot_package_qa_summary.md`: validation checks and residual risks.

## Known Residual Dependency Notes

The data loader flags a small set of unresolved optional source files in `data/raw/` and one optional validated matrix:

- `PROBLEM AND RECOMMENDATION 1&2.pptx`
- `PROBLEM AND RECOMMENDATION 3.pdf`
- `MIE1624_Final_Project.pptx`
- `Methodology_Report.docx`
- `outputs/tables/impact_matrix_long_validated.csv` (falls back to `impact_matrix_long.csv`)

These are non-blocking for the current dashboard data-loading pathway.
