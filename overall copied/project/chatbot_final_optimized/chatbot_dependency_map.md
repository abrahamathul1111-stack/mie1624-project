# Chatbot Dependency Map

## Runtime Entry Points

- `app/dashboard_app.py`
- `app/dashboard_overview_copy.py`
- `app/dashboard_timeline_copy.py`
- `app/export_dashboard_copies_html_v2.py`

## Python Module Dependencies

- `app/dashboard_app.py` -> `src/dashboard/dashboard_config.py`
- `app/dashboard_app.py` -> `src/dashboard/load_dashboard_data.py`
- `app/dashboard_app.py` -> `src/visualization/build_dashboard_a.py`
- `app/dashboard_app.py` -> `src/visualization/build_dashboard_b.py`
- Overview/timeline copy apps -> `src/visualization/dashboard_copy_components.py`
- Export helpers -> `src/visualization/dashboard_export.py`

## Data Dependencies (Primary)

- Raw and calibration inputs: `data/raw/`, `data/calibration/`, `data/processed/`
- Scenario and KPI tables: `outputs/tables/*.csv`
- Validation and inventory context: `outputs/reports/dashboard_*`

## Context/Grounding Dependencies

- Methodology references: `outputs/reports/technical_methodology_*`
- Decision baselines/rules: `DOCS/DECISIONS/*.md`
- Narrative report + reproducibility notebook: `context/*`

## Optional or Missing Inputs (Non-blocking for current path)

- `data/raw/PROBLEM AND RECOMMENDATION 1&2.pptx`
- `data/raw/PROBLEM AND RECOMMENDATION 3.pdf`
- `data/raw/MIE1624_Final_Project.pptx`
- `data/raw/Methodology_Report.docx`
- `outputs/tables/impact_matrix_long_validated.csv` (fallback to `impact_matrix_long.csv`)
