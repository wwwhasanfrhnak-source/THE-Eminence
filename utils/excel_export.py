# utils/excel_export.py
"""Workbook export utility."""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def export_rows_to_excel(rows: list[dict], path: str, sheet_name: str) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name[:31]
    headers = list(rows[0]) if rows else ["No data"]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = PatternFill("solid", fgColor="111827")
    for row in rows:
        sheet.append([row.get(header) for header in headers])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column in sheet.columns:
        width = min(max(len(str(cell.value or "")) for cell in column) + 2, 48)
        sheet.column_dimensions[column[0].column_letter].width = width
    workbook.save(path)
