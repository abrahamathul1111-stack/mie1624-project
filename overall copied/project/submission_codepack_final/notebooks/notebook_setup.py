"""Notebook helpers for importing the project package from the notebooks folder."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def ensure_project_root_on_path() -> Path:
    """Add the project root to ``sys.path`` and return it for notebook convenience."""

    project_root_text = str(PROJECT_ROOT)
    if project_root_text not in sys.path:
        sys.path.insert(0, project_root_text)
    return PROJECT_ROOT
