# AI Competitiveness Policy Simulation

This project is a clean Python 3 starter for building an AI competitiveness policy simulation workflow. The scaffold is organized for notebook exploration, reusable modeling code, and a lightweight dashboard layer.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app/dashboard_app.py
```

## Project Layout

```text
project/
  data/
    raw/
    processed/
  outputs/
    tables/
    figures/
    dashboard/
  notebooks/
  src/
    io/
    scoring/
    simulation/
    calibration/
    visualization/
  app/
  requirements.txt
  README.md
```

## Module Guide

- `src/io/data_loading.py`: notebook-friendly helpers for loading CSV, Excel, and Parquet inputs.
- `src/scoring/baseline_scoring.py`: KPI normalization and baseline competitiveness scoring.
- `src/scoring/impact_matrix.py`: recommendation-to-KPI impact matrix utilities.
- `src/simulation/quarterly_simulation.py`: deterministic quarter-by-quarter scenario projection.
- `src/simulation/monte_carlo.py`: uncertainty-aware simulation wrappers.
- `src/calibration/parameter_templates.py`: starter assumptions, weight tables, and adoption-plan templates.
- `src/visualization/dashboard_export.py`: export model outputs to JSON and CSV for dashboards.
- `app/dashboard_app.py`: Streamlit starter app for exploring exported outputs.

## Notebook Workflow

If you work from `notebooks/`, use the helper below in your first cell so imports resolve cleanly:

```python
from notebook_setup import ensure_project_root_on_path

PROJECT_ROOT = ensure_project_root_on_path()
```

## Modeling Assumptions

The starter simulation assumes KPI columns are numeric and scaled to a comparable `0-1` range before policy impacts are applied. That keeps the initial code simple and makes it easy to swap in richer calibration logic later.
