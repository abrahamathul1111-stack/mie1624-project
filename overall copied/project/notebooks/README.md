# Notebook Notes

Use `notebook_setup.py` in the first cell of a notebook so imports from the `src` package work consistently:

```python
from notebook_setup import ensure_project_root_on_path

PROJECT_ROOT = ensure_project_root_on_path()
```

From there you can import project modules such as:

```python
from src.io.data_loading import load_input_bundle
from src.scoring.baseline_scoring import compute_baseline_scores
```
