"""Notebook-friendly helpers for loading raw and processed project datasets.

The goal of this module is to keep path handling and file-format detection out of
analysis notebooks so data work stays concise and reusable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls", ".parquet"}


def resolve_data_path(project_root: str | Path, *parts: str) -> Path:
    """Return an absolute path inside the project for reproducible data access."""

    return Path(project_root).expanduser().resolve().joinpath(*parts)


def load_tabular_data(path: str | Path, **kwargs) -> pd.DataFrame:
    """Load a supported tabular dataset into a pandas ``DataFrame``.

    Supported formats are CSV, Excel, and Parquet. Extra keyword arguments are
    passed through to the appropriate pandas loader.
    """

    dataset_path = Path(path).expanduser().resolve()
    suffix = dataset_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(dataset_path, **kwargs)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(dataset_path, **kwargs)
    if suffix == ".parquet":
        return pd.read_parquet(dataset_path, **kwargs)

    raise ValueError(
        f"Unsupported file type '{suffix}'. Expected one of {sorted(SUPPORTED_SUFFIXES)}."
    )


def validate_required_columns(
    frame: pd.DataFrame, required_columns: Iterable[str], frame_name: str = "input frame"
) -> None:
    """Raise an informative error when a DataFrame is missing required columns."""

    missing_columns = sorted(set(required_columns) - set(frame.columns))
    if missing_columns:
        raise KeyError(f"{frame_name} is missing required columns: {missing_columns}")


def load_input_bundle(raw_data_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load every supported file in a directory into a dictionary of DataFrames.

    The dictionary key is the filename stem, which keeps the function convenient
    for interactive notebook use.
    """

    raw_path = Path(raw_data_dir).expanduser().resolve()
    bundle: dict[str, pd.DataFrame] = {}

    for path in sorted(raw_path.iterdir()):
        if not path.is_file():
            continue
        if path.name.startswith("~$") or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        bundle[path.stem] = load_tabular_data(path)

    return bundle
