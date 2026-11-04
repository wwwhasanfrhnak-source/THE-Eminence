"""خروجی PDF و Excel."""

import os
from datetime import datetime
from pathlib import Path

# مسیر خروجی
EXPORTS_DIR = Path(__file__).resolve().parents[2] / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


# ========================================================
# ابزارهای فارسی
# ========================================================
def _reshape_fa(text):
    """اصلاح متن فارسی برای PDF."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        if not text:
            return ""
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text) if text else ""


def _get_persian_font():
    """پیدا کردن یه فونت فارسی در ویندوز."""
    candidates = [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# ========================================================
# Excel
# ========================================================
def export_to_excel(headers, rows, title="خروجی", filename=None):
    """
    خروجی Excel.

    پارامترها:
        headers : لیست سرستون‌ها (فارسی)
        rows    : لیست ردیف‌ها (هر ردیف یه tuple/list)
        title   : عنوان فایل
        filename: نام دلخواه (اگه None باشه، خودکار)
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ValueError("کتابخانه openpyxl نصب نیست.\n"
                          "دستور: pip install openpyxl")

    wb = Workbook()
    ws = wb.active
    ws.title = "Data"

    # راست‌چین
    ws.sheet_view.rightToLeft = True

    # عنوان بالای جدول
    if title:
        ws.merge_cells(start_row=1, start_column=1,
                        end_row=1, end_column=len(headers))
        title_cell = ws.cell(row=1, column=1, value=title)
        title_cell.font = Font(size=14, bold=True, color="FFFFFF")
        title_cell.alignment = Alignment(horizontal="center",
                                          vertical="center")
        title_cell.fill = PatternFill(start_color="1F3A5F",
                                        end_color="1F3A5F",
                                        fill_type="solid")
        ws.row_dimensions[1].height = 30
        start_row = 3
    else:
        start_row = 1

    # سرستون‌ها
    header_fill = PatternFill(start_color="7C3AED",
                                end_color="7C3AED",
                                fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=start_row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center",
                                     vertical="center",
                                     wrap_text=True)
    ws.row_dimensions[start_row].height = 25

    # داده‌ها
    data_font = Font(size=10)
    for row_idx, row_data in enumerate(rows, start_row + 1):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = Alignment(horizontal="right",
                                         vertical="center",
                                         wrap_text=True)

    # عرض ستون‌ها
    for col_idx in range(1, len(headers) + 1):
        letter = get_column_letter(col_idx)
        max_width = len(str(headers[col_idx - 1]))
        for row in rows:
            if col_idx <= len(row):
                max_width = max(max_width, len(str(row[col_idx - 1])))
        ws.column_dimensions[letter].width = min(max_width + 4, 40)

    # ذخیره
    if not filename:
        filename = f"{title}_{_timestamp()}.xlsx"
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    path = EXPORTS_DIR / filename
    wb.save(str(path))
    return str(path)


# ========================================================
# PDF
# ========================================================
def export_to_pdf(headers, rows, title="خروجی", filename=None,
                   landscape=True):
    """
    خروجی PDF با پشتیبانی فارسی.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape as ls
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (SimpleDocTemplate, Table,
                                          TableStyle, Paragraph, Spacer)
    except ImportError:
        raise ValueError("کتابخانه reportlab نصب نیست.\n"
                          "دستور: pip install reportlab arabic-reshaper python-bidi")

    # فونت
    font_path = _get_persian_font()
    if not font_path:
        raise ValueError("هیچ فونت فارسی در ویندوز پیدا نشد.")

    font_name = "PersianFont"
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception:
        font_name = "Helvetica"

    # اندازه صفحه
    page_size = ls(A4) if landscape else A4

    # نام فایل
    if not filename:
        filename = f"{title}_{_timestamp()}.pdf"
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    path = EXPORTS_DIR / filename

    # ساخت سند
    doc = SimpleDocTemplate(
        str(path),
        pagesize=page_size,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=title,
    )

    # استایل
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=16,
        alignment=1,  # center
        spaceAfter=10,
        textColor=colors.HexColor("#1F3A5F"),
    )
    cell_style = ParagraphStyle(
        "CellStyle",
        fontName=font_name,
        fontSize=9,
        alignment=2,  # right
        leading=12,
    )
    header_style = ParagraphStyle(
        "HeaderStyle",
        fontName=font_name,
        fontSize=10,
        alignment=1,  # center
        textColor=colors.white,
        leading=14,
    )

    # محتوا
    elements = []

    if title:
        elements.append(Paragraph(_reshape_fa(title), title_style))
        elements.append(Spacer(1, 5 * mm))

    # ساخت جدول
    table_data = []

    # سرستون‌ها
    header_row = [Paragraph(_reshape_fa(h), header_style)
                   for h in headers]
    table_data.append(header_row)

    # داده‌ها
    for row in rows:
        data_row = []
        for val in row:
            text = str(val) if val is not None else ""
            data_row.append(Paragraph(_reshape_fa(text), cell_style))
        table_data.append(data_row)

    # تنظیم عرض ستون‌ها
    num_cols = len(headers)
    table_width = doc.width
    col_widths = [table_width / num_cols] * num_cols

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # استایل جدول
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4F6F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F9FAFB")]),
    ]))

    elements.append(table)

    # پانویس
    elements.append(Spacer(1, 10 * mm))
    footer_text = f"THE Eminence  |  تاریخ: {datetime.now().strftime('%Y-%m-%d  %H:%M')}"
    footer_style = ParagraphStyle(
        "Footer", fontName=font_name, fontSize=8,
        alignment=1, textColor=colors.HexColor("#6B7280"),
    )
    elements.append(Paragraph(_reshape_fa(footer_text), footer_style))

    doc.build(elements)
    return str(path)


# ========================================================
# Helper — خروجی از تب
# ========================================================
def get_exports_path():
    return str(EXPORTS_DIR)


def open_exports_folder():
    try:
        os.startfile(str(EXPORTS_DIR))
    except Exception:
        pass