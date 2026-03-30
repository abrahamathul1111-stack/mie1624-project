# Dashboard Component (Phase 6)

This folder adds a conservative dashboard reproducibility/access layer to the submission package.

## Included
- `src/`: snapshot of dashboard source files used for Streamlit runtime and HTML export logic
- `data_bundle/`: canonical dashboard CSV bundle used by exported HTML outputs
- `outputs/`: required final HTML artifacts
  - `overview_dashboard_interactive_v2_bold.html`
  - `timeline_dashboard_interactive_v2.html`

## Purpose
- Provide direct access to final dashboard deliverables.
- Preserve the source used to build/rebuild dashboard HTML outputs.

## Notes
- Final HTML outputs are self-contained and can be opened directly in a browser.
- Optional rebuild support is also included in `submission_codepack_final/app/` and `submission_codepack_final/src/dashboard`.
