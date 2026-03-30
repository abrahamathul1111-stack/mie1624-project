"""Safe XLSX package readers for workbooks with fixed analytical layouts.

The helpers in this module intentionally avoid fuzzy sheet discovery. They read
the workbook package directly, preserve blank cells, and raise informative
errors when required sheets or cached cell values are missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pandas as pd


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_NS = {"main": MAIN_NS, "pkg": PKG_REL_NS}


class WorkbookLoadError(ValueError):
    """Raised when a workbook cannot be loaded deterministically."""


@dataclass(frozen=True, slots=True)
class WorkbookSheet:
    """A worksheet loaded from an XLSX package."""

    name: str
    frame: pd.DataFrame


def normalize_sheet_name(sheet_name: str) -> str:
    """Return a compact sheet-name key for strict normalized matching."""

    return "".join(character.lower() for character in sheet_name if character.isalnum())


def map_required_sheet_names(
    available_sheet_names: list[str], required_sheet_names: list[str]
) -> dict[str, str]:
    """Map required sheet names to workbook sheet names without silent guessing."""

    normalized_lookup: dict[str, list[str]] = {}
    for sheet_name in available_sheet_names:
        normalized_lookup.setdefault(normalize_sheet_name(sheet_name), []).append(sheet_name)

    mapping: dict[str, str] = {}
    for required_sheet_name in required_sheet_names:
        if required_sheet_name in available_sheet_names:
            mapping[required_sheet_name] = required_sheet_name
            continue

        normalized_matches = normalized_lookup.get(
            normalize_sheet_name(required_sheet_name),
            [],
        )
        if len(normalized_matches) == 1:
            mapping[required_sheet_name] = normalized_matches[0]
            continue
        if len(normalized_matches) > 1:
            raise WorkbookLoadError(
                "Ambiguous normalized sheet match for "
                f"'{required_sheet_name}': {normalized_matches}"
            )

        raise WorkbookLoadError(
            f"Required sheet '{required_sheet_name}' was not found. "
            f"Available sheets: {available_sheet_names}"
        )

    return mapping


def load_xlsx_sheets(path: str | Path) -> dict[str, WorkbookSheet]:
    """Load every worksheet from an XLSX file into blank-preserving DataFrames."""

    workbook_path = Path(path).expanduser().resolve()
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    if workbook_path.suffix.lower() != ".xlsx":
        raise WorkbookLoadError(
            f"Expected an .xlsx workbook, received '{workbook_path.suffix}'."
        )

    with ZipFile(workbook_path) as workbook_zip:
        sheet_targets = _load_sheet_targets(workbook_zip)
        shared_strings = _load_shared_strings(workbook_zip)
        sheets: dict[str, WorkbookSheet] = {}
        for sheet_name, target in sheet_targets.items():
            if target not in workbook_zip.namelist():
                raise WorkbookLoadError(
                    f"Worksheet XML '{target}' for sheet '{sheet_name}' is missing "
                    "from the workbook package."
                )
            sheets[sheet_name] = WorkbookSheet(
                name=sheet_name,
                frame=_read_sheet_frame(workbook_zip, target, shared_strings),
            )

    return sheets


def _load_sheet_targets(workbook_zip: ZipFile) -> dict[str, str]:
    workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
    relationship_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))

    relationship_targets: dict[str, str] = {}
    for relationship in relationship_root.findall("pkg:Relationship", XML_NS):
        relationship_id = relationship.attrib["Id"]
        target = relationship.attrib["Target"]
        relationship_targets[relationship_id] = _normalize_target_path(target)

    sheet_targets: dict[str, str] = {}
    for sheet in workbook_root.findall("main:sheets/main:sheet", XML_NS):
        relationship_id = sheet.attrib.get(f"{{{DOC_REL_NS}}}id")
        sheet_name = sheet.attrib["name"]
        if not relationship_id:
            raise WorkbookLoadError(
                f"Sheet '{sheet_name}' is missing a relationship id in workbook.xml."
            )
        target = relationship_targets.get(relationship_id)
        if not target:
            raise WorkbookLoadError(
                f"Sheet '{sheet_name}' points to unknown relationship '{relationship_id}'."
            )
        sheet_targets[sheet_name] = target

    if not sheet_targets:
        raise WorkbookLoadError("No worksheets were found in the workbook package.")

    return sheet_targets


def _normalize_target_path(target: str) -> str:
    normalized_target = target.replace("\\", "/")
    if normalized_target.startswith("/"):
        return normalized_target.lstrip("/")
    if normalized_target.startswith("xl/"):
        return normalized_target
    return f"xl/{normalized_target}"


def _load_shared_strings(workbook_zip: ZipFile) -> list[str]:
    shared_strings_path = "xl/sharedStrings.xml"
    if shared_strings_path not in workbook_zip.namelist():
        return []

    root = ET.fromstring(workbook_zip.read(shared_strings_path))
    shared_strings: list[str] = []
    for item in root.findall("main:si", XML_NS):
        text_fragments = [
            fragment.text or ""
            for fragment in item.findall(".//main:t", XML_NS)
        ]
        shared_strings.append("".join(text_fragments))
    return shared_strings


def _read_sheet_frame(
    workbook_zip: ZipFile,
    target: str,
    shared_strings: list[str],
) -> pd.DataFrame:
    root = ET.fromstring(workbook_zip.read(target))
    sheet_data = root.find("main:sheetData", XML_NS)
    if sheet_data is None:
        raise WorkbookLoadError(f"Worksheet XML '{target}' is missing sheetData.")

    cell_map: dict[tuple[int, int], object] = {}
    max_row = 0
    max_col = 0

    for row in sheet_data.findall("main:row", XML_NS):
        row_index = int(row.attrib["r"]) - 1
        max_row = max(max_row, row_index + 1)
        for cell in row.findall("main:c", XML_NS):
            column_index = _excel_column_to_index(_extract_cell_column(cell.attrib["r"]))
            max_col = max(max_col, column_index + 1)
            cell_map[(row_index, column_index)] = _parse_cell_value(cell, shared_strings)

    if max_row == 0 or max_col == 0:
        return pd.DataFrame()

    frame = pd.DataFrame(index=range(max_row), columns=range(max_col), dtype="object")
    for (row_index, column_index), value in cell_map.items():
        frame.iat[row_index, column_index] = value
    return frame


def _extract_cell_column(cell_reference: str) -> str:
    return "".join(character for character in cell_reference if character.isalpha())


def _excel_column_to_index(column_ref: str) -> int:
    column_index = 0
    for character in column_ref.upper():
        column_index = (column_index * 26) + (ord(character) - ord("A") + 1)
    return column_index - 1


def _parse_cell_value(cell: ET.Element, shared_strings: list[str]) -> object:
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        return "".join(
            fragment.text or ""
            for fragment in cell.findall(".//main:t", XML_NS)
        )

    value_node = cell.find("main:v", XML_NS)
    value_text = value_node.text if value_node is not None else None

    if cell_type == "s":
        if value_text is None:
            raise WorkbookLoadError("Shared-string cell is missing its string index.")
        string_index = int(value_text)
        try:
            return shared_strings[string_index]
        except IndexError as exc:
            raise WorkbookLoadError(
                f"Shared-string index {string_index} is out of range."
            ) from exc

    if cell_type == "b":
        return value_text == "1"

    if value_text is None:
        formula_node = cell.find("main:f", XML_NS)
        if formula_node is not None:
            raise WorkbookLoadError(
                f"Formula cell '{cell.attrib.get('r', '?')}' is missing a cached value."
            )
        return None

    return _coerce_scalar(value_text)


def _coerce_scalar(value_text: str) -> object:
    if value_text == "":
        return ""

    try:
        numeric_value = float(value_text)
    except ValueError:
        return value_text

    if numeric_value.is_integer():
        return int(numeric_value)
    return numeric_value
