"""ساخت گزارش PDF — با فونت Vazirmatn فارسی."""

import io
import os
import glob
from datetime import datetime
from pathlib import Path


EXPORTS_DIR = Path(__file__).resolve().parents[2] / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


COLORS = {
    "purple": "#7c3aed", "cyan": "#06b6d4", "green": "#10b981",
    "orange": "#f59e0b", "red": "#ef4444", "pink": "#ec4899",
    "blue": "#3b82f6", "teal": "#14b8a6", "dark": "#1f2937",
    "muted": "#6b7280", "bg": "#ffffff", "card": "#f9fafb",
}


_FA_FONT_PATH = None


def _find_fa_font():
    global _FA_FONT_PATH
    if _FA_FONT_PATH is not None:
        return _FA_FONT_PATH

    patterns = [
        r"C:\Windows\Fonts\Vazir*.ttf",
        r"C:\Users\H.R\AppData\Local\Microsoft\Windows\Fonts\Vazir*.ttf",
        r"C:\Windows\Fonts\Shabnam*.ttf",
        r"C:\Users\H.R\AppData\Local\Microsoft\Windows\Fonts\Shabnam*.ttf",
        r"C:\Windows\Fonts\Sahel*.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
    ]
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            _FA_FONT_PATH = files[0]
            return _FA_FONT_PATH

    _FA_FONT_PATH = ""
    return ""


def _get_fa_font():
    """FontProperties برای matplotlib — بدون arabic_reshaper."""
    from matplotlib import font_manager

    path = _find_fa_font()
    if path:
        try:
            font_manager.fontManager.addfont(path)
            return font_manager.FontProperties(fname=path)
        except Exception:
            pass
    return font_manager.FontProperties()


def _setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 150
    return plt


def _save_buf(plt, fig):
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight",
                facecolor=COLORS["bg"], edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# ========================================================
# گیج
# ========================================================
def build_gauge_chart(value, max_value, label, color, unit=""):
    plt = _setup_matplotlib()
    import matplotlib.patches as patches

    fp = _get_fa_font()

    fig, ax = plt.subplots(figsize=(2.5, 1.8), facecolor=COLORS["bg"])
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.35, 1.2)
    ax.axis("off")

    ax.add_patch(patches.Wedge((0, 0), 1.0, 0, 180, width=0.3,
                                facecolor="#e5e7eb", edgecolor="none"))
    percent = min(value / max_value, 1.0) if max_value > 0 else 0
    if percent > 0:
        ax.add_patch(patches.Wedge((0, 0), 1.0, 0, 180 * percent, width=0.3,
                                    facecolor=color, edgecolor="none"))

    ax.text(0, 0.15, f"{value:,.0f}", ha="center", va="center",
            fontsize=16, fontweight="bold", color=COLORS["dark"],
            fontproperties=fp)
    if unit:
        ax.text(0, -0.05, unit, ha="center", va="center",
                fontsize=9, color=COLORS["muted"], fontproperties=fp)
    ax.text(0, -0.25, label, ha="center", va="center",
            fontsize=10, color=COLORS["dark"], fontweight="bold",
            fontproperties=fp)

    return _save_buf(plt, fig)


# ========================================================
# پای‌چارت
# ========================================================
def build_pie_chart(data, title=""):
    plt = _setup_matplotlib()
    if not data:
        return None

    fp = _get_fa_font()
    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    fig, ax = plt.subplots(figsize=(4, 3.5), facecolor=COLORS["bg"])
    palette = [COLORS["purple"], COLORS["cyan"], COLORS["green"],
               COLORS["orange"], COLORS["red"], COLORS["pink"]]

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=palette[:len(values)],
        autopct="%1.1f%%", startangle=90,
        textprops={"fontsize": 10, "color": COLORS["dark"],
                   "fontproperties": fp},
        wedgeprops={"edgecolor": "white", "linewidth": 2},
        labeldistance=1.1, pctdistance=0.75,
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
        at.set_fontsize(9)
        at.set_fontproperties(fp)

    ax.add_artist(plt.Circle((0, 0), 0.55, fc=COLORS["bg"]))
    ax.text(0, 0.1, str(sum(values)), ha="center", va="center",
            fontsize=16, fontweight="bold", color=COLORS["dark"],
            fontproperties=fp)
    ax.text(0, -0.12, "پروژه", ha="center", va="center",
            fontsize=9, color=COLORS["muted"], fontproperties=fp)
    ax.axis("equal")
    if title:
        ax.set_title(title, fontsize=12, fontweight="bold",
                      color=COLORS["dark"], pad=10, fontproperties=fp)

    return _save_buf(plt, fig)


# ========================================================
# میله‌ای
# ========================================================
def build_bar_chart(data, title="", horizontal=False):
    plt = _setup_matplotlib()
    if not data:
        return None

    fp = _get_fa_font()
    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    colors_list = [COLORS["purple"], COLORS["cyan"], COLORS["green"],
                   COLORS["orange"], COLORS["red"], COLORS["pink"],
                   COLORS["blue"], COLORS["teal"]][:len(values)]

    if horizontal:
        fig, ax = plt.subplots(figsize=(4.5, max(1.5, len(data) * 0.6)),
                                facecolor=COLORS["bg"])
        bars = ax.barh(labels, values, color=colors_list,
                       edgecolor="white", linewidth=1.5)
        ax.invert_yaxis()
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() * 1.02, bar.get_y() + bar.get_height() / 2,
                    f"{val:,.0f}", va="center", fontsize=9,
                    color=COLORS["dark"], fontweight="bold",
                    fontproperties=fp)
        ax.set_xticks([])
        for s in ["top", "right", "bottom"]:
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color("#e5e7eb")
        ax.tick_params(axis="y", labelsize=10, colors=COLORS["dark"])
        for tick in ax.get_yticklabels():
            tick.set_fontproperties(fp)
        ax.set_facecolor(COLORS["bg"])
        ax.set_xlim(0, max(values) * 1.15 if values else 1)
    else:
        fig, ax = plt.subplots(figsize=(4, 3.5), facecolor=COLORS["bg"])
        bars = ax.bar(labels, values, color=colors_list,
                       edgecolor="white", linewidth=1.5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
                    f"{val:,.0f}", ha="center", fontsize=9,
                    color=COLORS["dark"], fontweight="bold",
                    fontproperties=fp)
        ax.set_yticks([])
        for s in ["top", "right", "left"]:
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#e5e7eb")
        ax.tick_params(axis="x", labelsize=9, colors=COLORS["dark"])
        for tick in ax.get_xticklabels():
            tick.set_fontproperties(fp)
        ax.set_facecolor(COLORS["bg"])

    if title:
        ax.set_title(title, fontsize=12, fontweight="bold",
                      color=COLORS["dark"], pad=10, fontproperties=fp)

    return _save_buf(plt, fig)


# ========================================================
# خطی
# ========================================================
def build_line_chart(values, labels, title=""):
    plt = _setup_matplotlib()
    if not values:
        return None

    fp = _get_fa_font()
    fig, ax = plt.subplots(figsize=(4.5, 3.5), facecolor=COLORS["bg"])
    x = list(range(len(values)))
    ax.plot(x, values, color=COLORS["cyan"], linewidth=2.5,
            marker="o", markersize=7, markerfacecolor="white",
            markeredgewidth=2, markeredgecolor=COLORS["cyan"])
    ax.fill_between(x, values, alpha=0.15, color=COLORS["cyan"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, color=COLORS["dark"])
    for tick in ax.get_xticklabels():
        tick.set_fontproperties(fp)

    for i, v in enumerate(values):
        if v > 0:
            ax.text(i, v * 1.08, f"{v:,.1f}", ha="center",
                    fontsize=9, color=COLORS["dark"], fontweight="bold",
                    fontproperties=fp)

    ax.set_yticks([])
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.set_facecolor(COLORS["bg"])
    ax.set_ylim(0, max(values) * 1.25 if any(values) else 1)
    if title:
        ax.set_title(title, fontsize=12, fontweight="bold",
                      color=COLORS["dark"], pad=10, fontproperties=fp)

    return _save_buf(plt, fig)


# ========================================================
# کارت KPI
# ========================================================
def _make_kpi_card(icon, title, value, color, font_name):
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors

    data = [[icon], [str(value)], [title]]
    t = Table(data, colWidths=[99.2])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (0, 0), 18),
        ("FONTSIZE", (0, 1), (0, 1), 14),
        ("FONTSIZE", (0, 2), (0, 2), 10),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor(color)),
        ("TEXTCOLOR", (0, 1), (0, 1), colors.HexColor(COLORS["dark"])),
        ("TEXTCOLOR", (0, 2), (0, 2), colors.HexColor(COLORS["muted"])),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, -1),
         colors.HexColor(COLORS["card"])),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
    ]))
    return t


# ========================================================
# PDF اصلی
# ========================================================
def build_dashboard_pdf(path=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                      Table, TableStyle, Image as RLImage,
                                      PageBreak)
    from reportlab.platypus.flowables import HRFlowable

    from electrocalc.core import dashboard as db_stats
    stats = db_stats.get_summary()
    hours_data = db_stats.hours_per_engineer()
    status_data = db_stats.project_status_counts()
    expenses_data = db_stats.expenses_per_project()

    try:
        from electrocalc.data.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        today = datetime.now().date()
        weekly = []
        for i in range(6, -1, -1):
            d = today - __import__("datetime").timedelta(days=i)
            cur.execute("""
                SELECT COALESCE(SUM(hours),0) AS s FROM timesheets
                WHERE work_date = ?
            """, (d.strftime("%Y-%m-%d"),))
            weekly.append(cur.fetchone()["s"])
        conn.close()
    except Exception:
        weekly = [0] * 7

    weekly_labels = ["شنبه", "یک", "دو", "سه", "چهار", "پنج", "جمعه"]

    # فونت
    fa_path = _find_fa_font()
    if not fa_path:
        for p in [r"C:\Windows\Fonts\tahoma.ttf",
                  r"C:\Windows\Fonts\arial.ttf"]:
            if os.path.exists(p):
                fa_path = p
                break

    font_name = "Helvetica"
    if fa_path:
        try:
            pdfmetrics.registerFont(TTFont("Persian", fa_path))
            font_name = "Persian"
        except Exception:
            pass

    if not path:
        path = EXPORTS_DIR / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        str(path), pagesize=landscape(A4),
        rightMargin=10 * mm, leftMargin=10 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm,
        title="داشبورد مدیریتی",
    )

    title_style = ParagraphStyle(
        "T", fontName=font_name, fontSize=22, alignment=1,
        spaceAfter=5, textColor=colors.HexColor(COLORS["dark"]),
    )
    subtitle_style = ParagraphStyle(
        "S", fontName=font_name, fontSize=10, alignment=1,
        spaceAfter=10, textColor=colors.HexColor(COLORS["muted"]),
    )
    section_style = ParagraphStyle(
        "Sec", fontName=font_name, fontSize=14, alignment=2,
        spaceBefore=8, spaceAfter=8,
        textColor=colors.HexColor(COLORS["purple"]),
    )

    elements = []

    # صفحه ۱
    elements.append(Paragraph("داشبورد مدیریتی", title_style))
    elements.append(Paragraph(
        f"تاریخ: {datetime.now().strftime('%Y-%m-%d  %H:%M')}",
        subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2,
                                 color=colors.HexColor(COLORS["purple"]),
                                 spaceAfter=10))

    kpi_data = [[
        _make_kpi_card("📁", "پروژه‌ها", stats["projects"],
                        COLORS["purple"], font_name),
        _make_kpi_card("👥", "کاربران", stats["users"],
                        COLORS["cyan"], font_name),
        _make_kpi_card("⏰", "ساعت کار",
                        f"{stats['total_hours']:,.0f}",
                        COLORS["green"], font_name),
        _make_kpi_card("💰", "هزینه‌ها",
                        f"{stats['total_expenses']:,.0f}",
                        COLORS["red"], font_name),
        _make_kpi_card("🏭", "ارزش انبار",
                        f"{stats['total_materials']:,.0f}",
                        COLORS["orange"], font_name),
        _make_kpi_card("⏳", "در انتظار",
                        stats["pending_reports"] + stats["pending_expenses"],
                        COLORS["pink"], font_name),
    ]]

    kpi_table = Table(kpi_data, colWidths=[doc.width / 6] * 6)
    kpi_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph("شاخص‌های پیشرفت", section_style))

    gauge_row = []
    gauge_specs = [
        ("پروژه‌ها", stats["projects"],
         max(stats["projects"] * 2, 10), COLORS["purple"], "عدد"),
        ("کاربران", stats["users"],
         max(stats["users"] * 2, 5), COLORS["cyan"], "نفر"),
        ("ساعت کار", stats["total_hours"], 100,
         COLORS["green"], "ساعت"),
        ("ارزش انبار", stats["total_materials"], 100,
         COLORS["orange"], "تومان"),
    ]

    for label, val, mx, color, unit in gauge_specs:
        buf = build_gauge_chart(val, mx, label, color, unit)
        if buf:
            gauge_row.append(RLImage(buf, width=doc.width / 4 - 10 * mm,
                                       height=45 * mm))

    if gauge_row:
        g_table = Table([gauge_row],
                         colWidths=[doc.width / len(gauge_row)] * len(gauge_row))
        g_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(g_table)

    elements.append(PageBreak())

    # صفحه ۲
    elements.append(Paragraph("نمودارهای مدیریتی", title_style))
    elements.append(HRFlowable(width="100%", thickness=2,
                                 color=colors.HexColor(COLORS["purple"]),
                                 spaceAfter=10))

    if any(weekly):
        buf = build_line_chart(weekly, weekly_labels, "روند کاری هفتگی")
        if buf:
            elements.append(RLImage(buf, width=doc.width * 0.5,
                                      height=doc.width * 0.4))
            elements.append(Spacer(1, 5 * mm))

    row2 = []

    if status_data:
        buf = build_pie_chart(status_data, "وضعیت پروژه‌ها")
        if buf:
            row2.append(RLImage(buf, width=doc.width * 0.48 - 5 * mm,
                                  height=doc.width * 0.42))

    if hours_data:
        buf = build_bar_chart(hours_data, "ساعات مهندسان", horizontal=True)
        if buf:
            row2.append(RLImage(buf, width=doc.width * 0.48 - 5 * mm,
                                  height=doc.width * 0.42))

    if row2:
        r_table = Table([row2], colWidths=[doc.width / 2] * len(row2))
        r_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(r_table)

    elements.append(Spacer(1, 5 * mm))

    if expenses_data:
        buf = build_bar_chart(expenses_data, "هزینه هر پروژه")
        if buf:
            elements.append(RLImage(buf, width=doc.width * 0.7,
                                      height=doc.width * 0.4))

    doc.build(elements)
    return str(path)