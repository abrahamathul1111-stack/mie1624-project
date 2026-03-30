# Run Dashboard Assets

## A) Open final HTML outputs (recommended)
From `submission_codepack_final/dashboard/outputs/`, open:
- `overview_dashboard_interactive_v2_bold.html`
- `timeline_dashboard_interactive_v2.html`

## B) Optional: rebuild dashboard HTML in the submission package
Run from `submission_codepack_final/`:

```powershell
python app/export_dashboard_copies_html_v2.py
```

Expected regenerated files:
- `outputs/dashboard/overview_dashboard_interactive_v2.html`
- `outputs/dashboard/timeline_dashboard_interactive_v2.html`

## C) Optional: run Streamlit copies
Run from `submission_codepack_final/`:

```powershell
streamlit run app/dashboard_overview_copy.py
streamlit run app/dashboard_timeline_copy.py
```

Notes:
- These scripts use local files only.
- Some non-core narrative files referenced by the dashboard loader are optional; core dashboard CSV dependencies are included.
