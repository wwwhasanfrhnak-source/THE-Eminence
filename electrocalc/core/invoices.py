"""منطق فاکتور — فروش کالا و خدمات."""

import os
from datetime import datetime
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display

from electrocalc.data.database import get_connection


# ========================================================
# تبدیل متن فارسی برای reportlab (RTL)
# ========================================================
def _fa(text):
    """تبدیل متن فارسی برای reportlab — چسبیده و راست‌چین."""
    if text is None:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)


# ========================================================
# شماره فاکتور خودکار
# ========================================================
def generate_invoice_number():
    """INV-2025-0001"""
    year = datetime.now().strftime("%Y")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT number FROM invoices
            WHERE number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f"INV-{year}-%",))
        row = cur.fetchone()

        if row:
            last_num = int(row["number"].split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"INV-{year}-{new_num:04d}"
    finally:
        conn.close()


# ========================================================
# CRUD
# ========================================================
def create_invoice(customer_id, project_id, issue_date, due_date,
                    items, discount=0, tax=0, notes="",
                    created_by="", status="پیش‌نویس"):
    """ساخت فاکتور جدید + آیتم‌ها."""
    subtotal = sum(it["quantity"] * it["unit_price"] for it in items)
    discount_amount = subtotal * (discount / 100) if discount else 0
    tax_amount = (subtotal - discount_amount) * (tax / 100) if tax else 0
    total = subtotal - discount_amount + tax_amount

    number = generate_invoice_number()

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO invoices
                (number, customer_id, project_id, issue_date, due_date,
                 subtotal, discount, tax, total, status, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (number, customer_id, project_id, issue_date, due_date,
              subtotal, discount, tax, total, status, notes, created_by))

        invoice_id = cur.lastrowid

        for it in items:
            item_total = it["quantity"] * it["unit_price"]
            cur.execute("""
                INSERT INTO invoice_items
                    (invoice_id, description, quantity, unit_price,
                     total, item_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_id, it["description"], it["quantity"],
                  it["unit_price"], item_total,
                  it.get("item_type", "کالا")))

        conn.commit()
        return invoice_id, number
    finally:
        conn.close()


def update_invoice(invoice_id, customer_id, project_id, issue_date,
                    due_date, items, discount=0, tax=0, notes="",
                    status="پیش‌نویس"):
    """ویرایش فاکتور."""
    subtotal = sum(it["quantity"] * it["unit_price"] for it in items)
    discount_amount = subtotal * (discount / 100) if discount else 0
    tax_amount = (subtotal - discount_amount) * (tax / 100) if tax else 0
    total = subtotal - discount_amount + tax_amount

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE invoices SET
                customer_id=?, project_id=?, issue_date=?, due_date=?,
                subtotal=?, discount=?, tax=?, total=?, status=?, notes=?
            WHERE id=?
        """, (customer_id, project_id, issue_date, due_date,
              subtotal, discount, tax, total, status, notes, invoice_id))

        cur.execute("DELETE FROM invoice_items WHERE invoice_id=?",
                     (invoice_id,))

        for it in items:
            item_total = it["quantity"] * it["unit_price"]
            cur.execute("""
                INSERT INTO invoice_items
                    (invoice_id, description, quantity, unit_price,
                     total, item_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_id, it["description"], it["quantity"],
                  it["unit_price"], item_total,
                  it.get("item_type", "کالا")))

        conn.commit()
    finally:
        conn.close()


def delete_invoice(invoice_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM invoice_items WHERE invoice_id=?",
                     (invoice_id,))
        cur.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
        conn.commit()
    finally:
        conn.close()


def get_invoice(invoice_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT i.*, c.name AS customer_name,
                   p.name AS project_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN projects p ON i.project_id = p.id
            WHERE i.id=?
        """, (invoice_id,))
        inv = cur.fetchone()

        if not inv:
            return None, []

        inv = dict(inv)

        cur.execute("""
            SELECT * FROM invoice_items WHERE invoice_id=?
        """, (invoice_id,))
        items = [dict(r) for r in cur.fetchall()]

        return inv, items
    finally:
        conn.close()


def list_invoices(search="", status=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        where = []
        params = []

        if search:
            where.append("(i.number LIKE ? OR c.name LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if status:
            where.append("i.status = ?")
            params.append(status)

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        cur.execute(f"""
            SELECT i.*, c.name AS customer_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            {where_sql}
            ORDER BY i.id DESC
        """, params)

        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ========================================================
# PDF فاکتور
# ========================================================
def build_invoice_pdf(invoice_id, path=None):
    """ساخت PDF فاکتور با لوگو."""
    from electrocalc.core import report_builder as rb
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                      Table, TableStyle,
                                      Image as RLImage)
    from reportlab.platypus.flowables import HRFlowable

    inv, items = get_invoice(invoice_id)
    if not inv:
        raise ValueError("فاکتور پیدا نشد")

    # اطلاعات شرکت
    company = {}
    try:
        from electrocalc.core import company as comp
        row = comp.get_company()
        if row:
            company = dict(row)
    except Exception as e:
        print(f"خطا در لود اطلاعات شرکت: {e}")
        company = {}

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
        path = rb.EXPORTS_DIR / f"invoice_{inv['number']}.pdf"

    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title=f"فاکتور {inv['number']}",
    )

    title_style = ParagraphStyle(
        "T", fontName=font_name, fontSize=20, alignment=2,
        spaceAfter=3, textColor=colors.HexColor(rb.COLORS["dark"]),
    )
    sub_style = ParagraphStyle(
        "S", fontName=font_name, fontSize=9, alignment=2,
        textColor=colors.HexColor(rb.COLORS["muted"]),
    )
    normal = ParagraphStyle(
        "N", fontName=font_name, fontSize=10, alignment=2,
        textColor=colors.HexColor(rb.COLORS["dark"]),
    )
    cell = ParagraphStyle(
        "C", fontName=font_name, fontSize=10, alignment=1,
        textColor=colors.HexColor(rb.COLORS["dark"]),
    )

    elements = []

    # ========== هدر با لوگو ==========
    logo_cell = None
    logo_path = company.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        try:
            logo_cell = RLImage(logo_path, width=22 * mm, height=22 * mm)
        except Exception as e:
            print(f"خطا در لود لوگو: {e}")

    # متن شرکت
    company_name = company.get("name") or "فاکتور فروش"
    company_info_lines = []
    if company.get("phone"):
        company_info_lines.append(_fa(f"تلفن: {company['phone']}"))
    if company.get("email"):
        company_info_lines.append(_fa(f"ایمیل: {company['email']}"))
    if company.get("address"):
        company_info_lines.append(_fa(f"آدرس: {company['address']}"))

    name_para = Paragraph(_fa(company_name), title_style)
    info_para = Paragraph("<br/>".join(company_info_lines),
                            sub_style) if company_info_lines else None

    if logo_cell:
        # ساخت سلول متن
        text_data = [[name_para]]
        if info_para:
            text_data.append([info_para])

        text_cell = Table(text_data, colWidths=[doc.width - 30 * mm])
        text_cell.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        header_table = Table(
            [[text_cell, logo_cell]],
            colWidths=[doc.width - 28 * mm, 28 * mm],
        )
        header_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, 0), "RIGHT"),
            ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
    else:
        elements.append(name_para)
        if info_para:
            elements.append(info_para)

    elements.append(HRFlowable(width="100%", thickness=2,
                                 color=colors.HexColor(rb.COLORS["purple"]),
                                 spaceBefore=8, spaceAfter=10))

    # عنوان فاکتور
    elements.append(Paragraph(
        _fa(f"فاکتور فروش شماره {inv['number']}"),
        ParagraphStyle("IT", fontName=font_name, fontSize=15,
                        alignment=1, spaceAfter=10,
                        textColor=colors.HexColor(rb.COLORS["purple"]))))

    # اطلاعات مشتری
    info_data = [
        [Paragraph(_fa(f"مشتری: {inv.get('customer_name') or '—'}"), normal),
         Paragraph(_fa(f"تاریخ: {inv['issue_date']}"), normal)],
        [Paragraph(_fa(f"پروژه: {inv.get('project_name') or '—'}"), normal),
         Paragraph(_fa(f"وضعیت: {inv['status']}"), normal)],
    ]
    info_table = Table(info_data, colWidths=[doc.width / 2] * 2)
    info_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5 * mm))

    # جدول آیتم‌ها
    headers = ["#", "شرح", "تعداد", "قیمت واحد", "جمع"]
    rows = [[Paragraph(_fa(h) if h != "#" else h, cell) for h in headers]]

    for i, it in enumerate(items, 1):
        rows.append([
            Paragraph(str(i), cell),
            Paragraph(_fa(it["description"]), cell),
            Paragraph(_fa(f"{it['quantity']:,.2f}"), cell),
            Paragraph(_fa(f"{it['unit_price']:,.0f}"), cell),
            Paragraph(_fa(f"{it['total']:,.0f}"), cell),
        ])

    items_table = Table(rows, colWidths=[
        doc.width * 0.06, doc.width * 0.44,
        doc.width * 0.12, doc.width * 0.19, doc.width * 0.19,
    ])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor(rb.COLORS["purple"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5,
         colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f9fafb")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5 * mm))

    # جمع‌بندی
    subtotal = inv["subtotal"]
    discount_amount = subtotal * (inv["discount"] / 100) if inv["discount"] else 0
    tax_amount = (subtotal - discount_amount) * (inv["tax"] / 100) if inv["tax"] else 0
    total = inv["total"]

    totals_data = [
        [Paragraph(_fa("جمع کل:"), normal),
         Paragraph(_fa(f"{subtotal:,.0f} تومان"), normal)],
    ]
    if inv["discount"]:
        totals_data.append([
            Paragraph(_fa(f"تخفیف ({inv['discount']}%):"), normal),
            Paragraph(_fa(f"-{discount_amount:,.0f} تومان"), normal)])
    if inv["tax"]:
        totals_data.append([
            Paragraph(_fa(f"مالیات ({inv['tax']}%):"), normal),
            Paragraph(_fa(f"+{tax_amount:,.0f} تومان"), normal)])

    totals_data.append([
        Paragraph(_fa("قابل پرداخت:"), ParagraphStyle(
            "TT", fontName=font_name, fontSize=12,
            textColor=colors.HexColor(rb.COLORS["purple"]), alignment=2)),
        Paragraph(_fa(f"{total:,.0f} تومان"), ParagraphStyle(
            "TT2", fontName=font_name, fontSize=12,
            textColor=colors.HexColor(rb.COLORS["purple"]), alignment=2)),
    ])

    totals_table = Table(totals_data,
                          colWidths=[doc.width * 0.3, doc.width * 0.3],
                          hAlign="LEFT")
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)

    # یادداشت
    if inv.get("notes"):
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(_fa(f"یادداشت: {inv['notes']}"), normal))

    doc.build(elements)
    return str(path)