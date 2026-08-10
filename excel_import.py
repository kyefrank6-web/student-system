"""
Bulk learner import from .xlsx (first sheet).
Expected columns (header row): flexible names — see HEADER_TO_FIELD.
"""
from __future__ import annotations

import re
from io import BytesIO
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.utils.exceptions import InvalidFileException

from curriculum_ug import UG_CLASS_CODES

HEADER_TO_FIELD = {
    "name": "name",
    "full_name": "name",
    "learner_name": "name",
    "student_name": "name",
    "learner": "name",
    "class": "class_level",
    "class_level": "class_level",
    "form": "class_level",
    "grade": "class_level",
    "rfid": "rfid_tag",
    "rfid_tag": "rfid_tag",
    "tag": "rfid_tag",
    "card_id": "rfid_tag",
    "parent_email": "parent_email",
    "parent_e_mail": "parent_email",
    "parent": "parent_email",
    "parent_name": "parent_name",
    "guardian_name": "parent_name",
    "guardian": "parent_name",
    "stream": "stream",
    "section": "stream",
}

MAX_ROWS = 2000
MAX_FILE_BYTES = 5 * 1024 * 1024


def _norm_header(val: Any) -> str:
    s = str(val or "").strip().lower()
    s = re.sub(r"\s+", "_", s)
    return s


def _norm_class(code: str) -> str | None:
    if not code:
        return None
    c = str(code).strip().upper()
    if c in UG_CLASS_CODES:
        return c
    return None


def build_learner_import_template() -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Learners"
    headers = ["Name", "Class", "Stream", "RFID", "Parent_Name", "Parent_Email"]
    ws.append(headers)
    ws.append(["Jane Mukasa", "P3", "East", "", "Mary Mukasa", "mary.mukasa@example.com"])
    ws.append(["John Okello", "S2", "", "RFID-1002", "", ""])
    bold = Font(bold=True)
    for c in range(1, len(headers) + 1):
        ws.cell(row=1, column=c).font = bold
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def parse_learner_rows(file_bytes: bytes) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows_ok: list[dict[str, Any]] = []

    if len(file_bytes) > MAX_FILE_BYTES:
        errors.append("File is too large (max 5 MB).")
        return rows_ok, errors

    try:
        wb = load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except (InvalidFileException, OSError, ValueError, KeyError) as e:
        errors.append(f"Could not read Excel file: {e}")
        return rows_ok, errors

    try:
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        try:
            header_row = next(it)
        except StopIteration:
            errors.append("The spreadsheet is empty.")
            return rows_ok, errors

        col_map: dict[int, str] = {}
        for idx, cell in enumerate(header_row):
            key = HEADER_TO_FIELD.get(_norm_header(cell))
            if key:
                col_map[idx] = key

        if "name" not in col_map.values() or "class_level" not in col_map.values():
            errors.append(
                "Missing required columns. The first row must include **Name** and **Class** "
                "(e.g. Name, Class, RFID, Parent_Name, Parent_Email)."
            )
            return rows_ok, errors

        row_num = 1
        for data in it:
            row_num += 1
            if row_num > MAX_ROWS + 1:
                errors.append(f"Import stopped after {MAX_ROWS} data rows.")
                break

            if data is None or all(v is None or str(v).strip() == "" for v in data):
                continue

            row: dict[str, str] = {}
            for col_idx, field in col_map.items():
                if col_idx < len(data):
                    val = data[col_idx]
                    row[field] = "" if val is None else str(val).strip()

            name = row.get("name", "").strip()
            class_raw = row.get("class_level", "").strip()
            stream = row.get("stream", "").strip()
            rfid = row.get("rfid_tag", "").strip()
            parent_email = row.get("parent_email", "").strip().lower()
            parent_name = row.get("parent_name", "").strip()

            if not name and not class_raw and not rfid and not parent_email:
                continue

            if not name:
                errors.append(f"Row {row_num}: missing name, skipped.")
                continue

            class_level = _norm_class(class_raw)
            if not class_level:
                errors.append(
                    f"Row {row_num} ({name!r}): invalid class {class_raw!r} — use P1–P7 or S1–S6."
                )
                continue

            rows_ok.append(
                {
                    "name": name[:100],
                    "class_level": class_level,
                    "stream": stream[:50] if stream else "",
                    "rfid_tag": rfid[:100] if rfid else "",
                    "parent_email": parent_email,
                    "parent_name": parent_name[:100] if parent_name else "",
                    "_row": row_num,
                }
            )
    finally:
        wb.close()

    return rows_ok, errors


def filter_duplicate_rfids_in_file(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    errs: list[str] = []
    for r in rows:
        tag = (r.get("rfid_tag") or "").strip()
        if not tag:
            out.append(r)
            continue
        if tag in seen:
            errs.append(
                f"Row {r['_row']}: RFID {tag!r} duplicates an earlier row in this file, skipped."
            )
            continue
        seen.add(tag)
        out.append(r)
    return out, errs
