# utils/pdf_export.py
"""Small table-based PDF export utility."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


def export_rows_to_pdf(rows: list[dict], path: str, title: str) -> None:
    headers = list(rows[0]) if rows else ["Report"]
    data = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    document = SimpleDocTemplate(path, pagesize=landscape(letter))
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ]
        )
    )
    document.build([Paragraph(title, getSampleStyleSheet()["Title"]), Spacer(1, 12), table])
