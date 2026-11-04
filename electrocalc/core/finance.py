"""منطق مالی پروژه — درآمد، هزینه، سود."""

from datetime import datetime, timedelta

from electrocalc.data.database import get_connection


# ========================================================
# بازه تاریخ
# ========================================================
def _date_range(period="all", start_date=None, end_date=None):
    today = datetime.now().date()

    if start_date and end_date:
        return start_date, end_date

    if period == "today":
        return today, today
    elif period == "week":
        return today - timedelta(days=6), today
    elif period == "month":
        return today - timedelta(days=29), today
    elif period == "year":
        return today - timedelta(days=364), today
    else:  # all
        return None, None


# ========================================================
# درآمد یک پروژه
# ========================================================
def _project_income(cur, project_id, start=None, end=None):
    """جمع درآمد پروژه از فاکتورهای ارسال/پرداخت‌شده."""
    where = ["project_id = ?", "status IN ('ارسال‌شده', 'پرداخت‌شده')"]
    params = [project_id]

    if start and end:
        where.append("issue_date BETWEEN ? AND ?")
        params.extend([start.strftime("%Y-%m-%d"),
                       end.strftime("%Y-%m-%d")])

    cur.execute(f"""
        SELECT COALESCE(SUM(total), 0) AS s
        FROM invoices
        WHERE {" AND ".join(where)}
    """, params)
    return cur.fetchone()["s"] or 0


# ========================================================
# هزینه یک پروژه
# ========================================================
def _project_expenses(cur, project_id, start=None, end=None):
    """جمع هزینه پروژه از expenses + خروجی انبار."""
    total = 0

    # ۱) هزینه‌های مستقیم
    where = ["project_id = ?", "status = 'approved'"]
    params = [project_id]
    if start and end:
        where.append("expense_date BETWEEN ? AND ?")
        params.extend([start.strftime("%Y-%m-%d"),
                       end.strftime("%Y-%m-%d")])

    cur.execute(f"""
        SELECT COALESCE(SUM(amount), 0) AS s
        FROM expenses
        WHERE {" AND ".join(where)}
    """, params)
    total += cur.fetchone()["s"] or 0

    # ۲) خروجی انبار
    where = ["project_id = ?", "type = 'خروج'"]
    params = [project_id]
    if start and end:
        where.append("trans_date BETWEEN ? AND ?")
        params.extend([start.strftime("%Y-%m-%d"),
                       end.strftime("%Y-%m-%d")])

    cur.execute(f"""
        SELECT COALESCE(SUM(total_price), 0) AS s
        FROM warehouse_transactions
        WHERE {" AND ".join(where)}
    """, params)
    total += cur.fetchone()["s"] or 0

    return total


# ========================================================
# KPI کلی
# ========================================================
def get_kpi(period="all", start_date=None, end_date=None):
    """۴ کارت KPI: درآمد، هزینه، سود، حاشیه سود."""
    s, e = _date_range(period, start_date, end_date)

    conn = get_connection()
    cur = conn.cursor()

    try:
        # درآمد کل
        where = ["status IN ('ارسال‌شده', 'پرداخت‌شده')"]
        params = []
        if s and e:
            where.append("issue_date BETWEEN ? AND ?")
            params.extend([s.strftime("%Y-%m-%d"),
                           e.strftime("%Y-%m-%d")])

        cur.execute(f"""
            SELECT COALESCE(SUM(total), 0) AS s
            FROM invoices
            WHERE {" AND ".join(where)}
        """, params)
        income = cur.fetchone()["s"] or 0

        # هزینه کل — expenses
        where = ["status = 'approved'"]
        params = []
        if s and e:
            where.append("expense_date BETWEEN ? AND ?")
            params.extend([s.strftime("%Y-%m-%d"),
                           e.strftime("%Y-%m-%d")])

        cur.execute(f"""
            SELECT COALESCE(SUM(amount), 0) AS s
            FROM expenses
            WHERE {" AND ".join(where)}
        """, params)
        exp1 = cur.fetchone()["s"] or 0

        # هزینه کل — انبار
        where = ["type = 'خروج'"]
        params = []
        if s and e:
            where.append("trans_date BETWEEN ? AND ?")
            params.extend([s.strftime("%Y-%m-%d"),
                           e.strftime("%Y-%m-%d")])

        cur.execute(f"""
            SELECT COALESCE(SUM(total_price), 0) AS s
            FROM warehouse_transactions
            WHERE {" AND ".join(where)}
        """, params)
        exp2 = cur.fetchone()["s"] or 0

        total_expense = exp1 + exp2
        profit = income - total_expense
        margin = (profit / income * 100) if income > 0 else 0

        return {
            "income": income,
            "expense": total_expense,
            "profit": profit,
            "margin": margin,
        }
    finally:
        conn.close()


# ========================================================
# جدول پروژه‌ها
# ========================================================
def get_projects_finance(period="all", start_date=None, end_date=None):
    """لیست پروژه‌ها با درآمد، هزینه، سود."""
    s, e = _date_range(period, start_date, end_date)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id, name, status FROM projects ORDER BY id DESC")
        projects = cur.fetchall()

        result = []
        for p in projects:
            pid = p["id"]
            income = _project_income(cur, pid, s, e)
            expense = _project_expenses(cur, pid, s, e)
            profit = income - expense
            margin = (profit / income * 100) if income > 0 else 0

            result.append({
                "id": pid,
                "name": p["name"],
                "status": p["status"],
                "income": income,
                "expense": expense,
                "profit": profit,
                "margin": margin,
            })

        # مرتب‌سازی: سود بیشتر اول
        result.sort(key=lambda x: x["profit"], reverse=True)
        return result

    finally:
        conn.close()


# ========================================================
# PDF
# ========================================================
def _fa(text):
    """تبدیل متن فارسی برای reportlab."""
    import arabic_reshaper
    from bidi.algorithm import get_display
    if text is None:
        return ""
    try:
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def build_finance_pdf(path=None, period="all",
                       start_date=None, end_date=None):
    """PDF گزارش مالی پروژه‌ها."""
    from electrocalc.core import report_builder as rb
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                      Table, TableStyle,
                                      Image as RLImage)
    from reportlab.platypus.flowables import HRFlowable

    kpi = get_kpi(period, start_date, end_date)
    projects = get_projects_finance(period, start_date, end_date)

    # فونت
    fa_path = rb._find_fa_font()
    font_name = "Helvetica"
    if fa_path:
        try:
            pdfmetrics.registerFont(TTFont("Persian", fa_path))
            font_name = "Persian"
        except Exception:
            pass

    if not path:
        path = rb.EXPORTS_DIR / \
            f"finance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(path), pagesize=landscape(A4),
        rightMargin=10 * mm, leftMargin=10 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm,
        title="گزارش مالی",
    )

    title_style = ParagraphStyle(
        "T", fontName=font_name, fontSize=20, alignment=1,
        spaceAfter=5, textColor=colors.HexColor(rb.COLORS["dark"]),
    )
    sub_style = ParagraphStyle(
        "S", fontName=font_name, fontSize=10, alignment=1,
        spaceAfter=10, textColor=colors.HexColor(rb.COLORS["muted"]),
    )
    sec_style = ParagraphStyle(
        "Sec", fontName=font_name, fontSize=13, alignment=2,
        spaceBefore=8, spaceAfter=8,
        textColor=colors.HexColor(rb.COLORS["purple"]),
    )
    cell_style = ParagraphStyle(
        "C", fontName=font_name, fontSize=9, alignment=1,
        textColor=colors.HexColor(rb.COLORS["dark"]),
    )

    elements = []

    elements.append(Paragraph("گزارش مالی پروژه‌ها", title_style))
    elements.append(Paragraph(
        f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        sub_style))
    elements.append(HRFlowable(width="100%", thickness=2,
                                 color=colors.HexColor(rb.COLORS["purple"]),
                                 spaceAfter=10))

    # KPI
    kpi_data = [[
        rb._make_kpi_card("💰", "درآمد کل",
                           f"{kpi['income']:,.0f}",
                           rb.COLORS["green"], font_name),
        rb._make_kpi_card("💸", "هزینه کل",
                           f"{kpi['expense']:,.0f}",
                           rb.COLORS["red"], font_name),
        rb._make_kpi_card("📈", "سود",
                           f"{kpi['profit']:,.0f}",
                           rb.COLORS["purple"], font_name),
        rb._make_kpi_card("📊", "حاشیه سود",
                           f"{kpi['margin']:.1f}%",
                           rb.COLORS["cyan"], font_name),
    ]]
    kpi_table = Table(kpi_data, colWidths=[doc.width / 4] * 4)
    kpi_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 8 * mm))

    # جدول پروژه‌ها
    elements.append(Paragraph("مالی هر پروژه", sec_style))

    headers = ["#", "پروژه", "وضعیت", "درآمد", "هزینه", "سود", "حاشیه"]
    rows = [[Paragraph(h, cell_style) for h in headers]]

    for i, p in enumerate(projects, 1):
        status_fa = {
            "in_progress": "در جریان",
            "completed": "تمام‌شده",
            "cancelled": "لغو‌شده",
        }.get(p["status"], p["status"])

        rows.append([
            Paragraph(str(i), cell_style),
            Paragraph(p["name"], cell_style),
            Paragraph(status_fa, cell_style),
            Paragraph(f"{p['income']:,.0f}", cell_style),
            Paragraph(f"{p['expense']:,.0f}", cell_style),
            Paragraph(f"{p['profit']:,.0f}", cell_style),
            Paragraph(f"{p['margin']:.1f}%", cell_style),
        ])

    if len(rows) > 1:
        rank_table = Table(rows, colWidths=[
            doc.width * 0.05, doc.width * 0.25,
            doc.width * 0.12, doc.width * 0.14,
            doc.width * 0.14, doc.width * 0.14, doc.width * 0.10,
        ])
        rank_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor(rb.COLORS["purple"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), font_name),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5,
             colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f9fafb")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(rank_table)
    else:
        elements.append(Paragraph("داده‌ای موجود نیست", sub_style))

    elements.append(Spacer(1, 8 * mm))

    # نمودارها
    elements.append(Paragraph("نمودارها", sec_style))

    chart_row = []

    if projects:
        # میلهای افقی — درآمد vs هزینه
        bar_data = [
            (p["name"][:15], p["income"]) for p in projects[:8]
        ]
        if bar_data:
            buf = rb.build_bar_chart(bar_data, "درآمد هر پروژه",
                                       horizontal=True)
            if buf:
                chart_row.append(RLImage(buf,
                    width=doc.width * 0.48, height=doc.width * 0.35))

        # پای‌چارت سود
        pie_data = [
            (p["name"][:12], p["profit"]) for p in projects[:6]
            if p["profit"] > 0
        ]
        if pie_data:
            buf = rb.build_pie_chart(pie_data, "سهم سود پروژه‌ها")
            if buf:
                chart_row.append(RLImage(buf,
                    width=doc.width * 0.48, height=doc.width * 0.35))

    if chart_row:
        c_table = Table([chart_row],
                         colWidths=[doc.width / len(chart_row)] * len(chart_row))
        c_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(c_table)

    doc.build(elements)
    return str(path)


# ========================================================
# Excel
# ========================================================
def build_finance_excel(path=None, period="all",
                          start_date=None, end_date=None):
    """Excel گزارش مالی."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from electrocalc.core import report_builder as rb

    kpi = get_kpi(period, start_date, end_date)
    projects = get_projects_finance(period, start_date, end_date)

    if not path:
        path = rb.EXPORTS_DIR / \
            f"finance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "مالی پروژه"
    ws.sheet_view.rightToLeft = True

    header_fill = PatternFill("solid", fgColor="7C3AED")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    center = Alignment(horizontal="center", vertical="center")

    ws["A1"] = "گزارش مالی پروژه‌ها"
    ws["A1"].font = Font(bold=True, size=14)
    ws.merge_cells("A1:G1")
    ws["A1"].alignment = center

    ws["A2"] = f"تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws.merge_cells("A2:G2")
    ws["A2"].alignment = center

    # KPI
    ws["A4"] = "درآمد کل"
    ws["B4"] = kpi["income"]
    ws["C4"] = "هزینه کل"
    ws["D4"] = kpi["expense"]
    ws["E4"] = "سود"
    ws["F4"] = kpi["profit"]
    ws["G4"] = f"{kpi['margin']:.1f}%"

    # جدول
    headers = ["#", "پروژه", "وضعیت", "درآمد", "هزینه", "سود", "حاشیه"]
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=6, column=col, value=h)
        c.fill = header_fill
        c.font = header_font
        c.alignment = center

    for i, p in enumerate(projects, 1):
        row = i + 6
        status_fa = {
            "in_progress": "در جریان",
            "completed": "تمام‌شده",
            "cancelled": "لغو‌شده",
        }.get(p["status"], p["status"])

        ws.cell(row=row, column=1, value=i).alignment = center
        ws.cell(row=row, column=2, value=p["name"]).alignment = center
        ws.cell(row=row, column=3, value=status_fa).alignment = center
        ws.cell(row=row, column=4, value=p["income"]).alignment = center
        ws.cell(row=row, column=5, value=p["expense"]).alignment = center
        ws.cell(row=row, column=6, value=p["profit"]).alignment = center
        ws.cell(row=row, column=7,
                value=f"{p['margin']:.1f}%").alignment = center

    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 15
    ws.column_dimensions["G"].width = 10

    wb.save(str(path))
    return str(path)