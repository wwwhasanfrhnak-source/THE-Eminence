"""تب داشبورد — با نمودارهای زنده و خروجی PDF حرفه‌ای."""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

from electrocalc.core import dashboard as db_stats
from electrocalc.core.income_trends import get_income_trends
from electrocalc.config import themes as themes_module
from electrocalc.ui.scrollable_frame import ScrollableFrame


CHART_COLORS = ["#7c3aed", "#06b6d4", "#10b981", "#f59e0b",
                "#ef4444", "#ec4899", "#8b5cf6", "#14b8a6"]


def _get_colors():
    try:
        from electrocalc.core import settings as st
        theme = st.get_setting("app_theme", "light")
    except Exception:
        theme = "light"
    p = themes_module.get_palette(theme)
    return {
        "bg": p["bg"], "card": p["card"], "border": p["border"],
        "text": p["text"], "muted": p["muted"], "accent": p["accent"],
        "danger": p["danger"], "success": p["success"],
    }


class DarkCard(tk.Frame):
    def __init__(self, parent, title="", icon="", pad=14, colors=None, **kw):
        self.colors = colors or _get_colors()
        super().__init__(parent, bg=self.colors["card"],
                         highlightbackground=self.colors["border"],
                         highlightthickness=1, **kw)
        if title:
            head = tk.Frame(self, bg=self.colors["card"])
            head.pack(fill="x", padx=pad, pady=(pad, 8))
            tk.Label(head, text=f"{icon}  {title}",
                     font=("Segoe UI", 12, "bold"),
                     bg=self.colors["card"], fg=self.colors["text"],
                     anchor="e").pack(side="right")
        self.body = tk.Frame(self, bg=self.colors["card"])
        self.body.pack(fill="both", expand=True, padx=pad, pady=(0, pad))


class KpiCard(tk.Frame):
    def __init__(self, parent, icon, title, value, color, subtitle="", colors=None):
        self.colors = colors or _get_colors()
        super().__init__(parent, bg=self.colors["card"],
                         highlightbackground=self.colors["border"],
                         highlightthickness=1)
        self.pack_propagate(False)
        self.configure(height=105)

        tk.Frame(self, bg=color, width=5).pack(side="right", fill="y")
        body = tk.Frame(self, bg=self.colors["card"])
        body.pack(side="right", fill="both", expand=True, padx=14, pady=12)
        tk.Label(body, text=icon, font=("Segoe UI Emoji", 22),
                 bg=self.colors["card"], fg=color).pack(side="right", padx=(0, 10))
        tf = tk.Frame(body, bg=self.colors["card"])
        tf.pack(side="right", fill="both", expand=True)
        tk.Label(tf, text=title, font=("Segoe UI", 9),
                 bg=self.colors["card"], fg=self.colors["muted"],
                 anchor="e").pack(anchor="e")
        tk.Label(tf, text=str(value), font=("Segoe UI", 17, "bold"),
                 bg=self.colors["card"], fg=self.colors["text"],
                 anchor="e").pack(anchor="e")
        if subtitle:
            tk.Label(tf, text=subtitle, font=("Segoe UI", 8),
                     bg=self.colors["card"], fg=color,
                     anchor="e").pack(anchor="e")


class DashboardTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.colors = _get_colors()
        self._income_refresh_job = None
        self._destroyed = False
        self.build_ui()
        self.bind("<Destroy>", self._on_destroy, add="+")
        self.after(200, self.refresh)
        self._schedule_income_refresh()

    def build_ui(self):
        p = self.inner
        c = self.colors

        header = tk.Frame(p, bg=c["bg"])
        header.pack(fill="x", pady=(0, 15))
        right_h = tk.Frame(header, bg=c["bg"])
        right_h.pack(side="right")
        tk.Label(right_h, text="📊  داشبورد مدیریتی",
                 font=("Segoe UI", 20, "bold"), bg=c["bg"], fg=c["text"],
                 anchor="e").pack(anchor="e")
        tk.Label(right_h, text="نگاه کلی به وضعیت کارگاه و پروژه‌ها",
                 font=("Segoe UI", 10), bg=c["bg"], fg=c["muted"],
                 anchor="e").pack(anchor="e")

        btn_box = tk.Frame(header, bg=c["bg"])
        btn_box.pack(side="left", pady=8)
        for text, cmd, color in [
            ("🔄 بروزرسانی", self.refresh, c["accent"]),
            ("📊 Excel", self.export_excel, "#16a34a"),
            ("📄 PDF حرفه‌ای", self.export_pdf_pro, c["danger"]),
        ]:
            b = tk.Label(btn_box, text=text, font=("Segoe UI", 10, "bold"),
                         bg=color, fg="white", padx=14, pady=8, cursor="hand2")
            b.pack(side="right", padx=3)
            b.bind("<Button-1>", lambda e, c2=cmd: c2())

        self.kpi_row = tk.Frame(p, bg=c["bg"])
        self.kpi_row.pack(fill="x", pady=(0, 14))

        mid = tk.Frame(p, bg=c["bg"])
        mid.pack(fill="x", pady=(0, 14))
        self.gauges_card = DarkCard(mid, "درصد پیشرفت کلی", "🎯", colors=c)
        self.gauges_card.pack(side="right", fill="both", expand=True, padx=(0, 7))
        self.gauges_canvas = tk.Canvas(self.gauges_card.body, height=210,
                                       bg=c["card"], highlightthickness=0)
        self.gauges_canvas.pack(fill="both", expand=True)

        self.line_card = DarkCard(mid, "روند کاری هفتگی", "📈", colors=c)
        self.line_card.pack(side="right", fill="both", expand=True, padx=7)
        self.line_canvas = tk.Canvas(self.line_card.body, height=210,
                                     bg=c["card"], highlightthickness=0)
        self.line_canvas.pack(fill="both", expand=True)

        self.pie_card = DarkCard(mid, "وضعیت پروژه‌ها", "🥧", colors=c)
        self.pie_card.pack(side="right", fill="both", expand=True, padx=(7, 0))
        self.pie_canvas = tk.Canvas(self.pie_card.body, height=210,
                                    bg=c["card"], highlightthickness=0)
        self.pie_canvas.pack(fill="both", expand=True)

        # درآمدهای فاکتوری، جدا از نمودار ساعات کاری فعلی.
        income_row = tk.Frame(p, bg=c["bg"])
        income_row.pack(fill="x", pady=(0, 14))
        self.weekly_income_card = DarkCard(
            income_row, "درآمد روزانه — هفت روز اخیر", "💵", colors=c)
        self.weekly_income_card.pack(side="right", fill="both", expand=True,
                                     padx=(0, 7))
        self.weekly_income_canvas = tk.Canvas(
            self.weekly_income_card.body, height=220,
            bg=c["card"], highlightthickness=0)
        self.weekly_income_canvas.pack(fill="both", expand=True)

        self.monthly_income_card = DarkCard(
            income_row, "درآمد ماهانه — شش ماه اخیر", "📊", colors=c)
        self.monthly_income_card.pack(side="right", fill="both", expand=True,
                                      padx=(7, 0))
        self.monthly_income_canvas = tk.Canvas(
            self.monthly_income_card.body, height=220,
            bg=c["card"], highlightthickness=0)
        self.monthly_income_canvas.pack(fill="both", expand=True)

        bottom = tk.Frame(p, bg=c["bg"])
        bottom.pack(fill="x", pady=(0, 20))
        self.hbars_card = DarkCard(bottom, "ساعات کار مهندسان", "👷", colors=c)
        self.hbars_card.pack(side="right", fill="both", expand=True, padx=(0, 7))
        self.hbars_canvas = tk.Canvas(self.hbars_card.body, height=260,
                                      bg=c["card"], highlightthickness=0)
        self.hbars_canvas.pack(fill="both", expand=True)
        self.vbars_card = DarkCard(bottom, "هزینه پروژه‌ها", "💰", colors=c)
        self.vbars_card.pack(side="right", fill="both", expand=True, padx=(7, 0))
        self.vbars_canvas = tk.Canvas(self.vbars_card.body, height=260,
                                      bg=c["card"], highlightthickness=0)
        self.vbars_canvas.pack(fill="both", expand=True)

    def refresh(self):
        stats = db_stats.get_summary()
        c = self.colors
        for w in self.kpi_row.winfo_children():
            w.destroy()
        kpis = [
            ("📁", "پروژه‌ها", stats["projects"], "#7c3aed", "پروژه فعال"),
            ("👥", "کاربران", stats["users"], "#06b6d4", "کاربر فعال"),
            ("⏰", "ساعت کار", f"{stats['total_hours']:,.0f}", "#10b981", "ساعت کل"),
            ("💰", "هزینه‌ها", f"{stats['total_expenses']:,.0f}", "#ef4444", "تومان"),
            ("🏭", "ارزش انبار", f"{stats['total_materials']:,.0f}", "#f59e0b", "تومان"),
            ("⏳", "در انتظار", stats["pending_reports"] + stats["pending_expenses"], "#ec4899", "نیاز تأیید"),
        ]
        for icon, title, value, color, sub in kpis:
            KpiCard(self.kpi_row, icon, title, value, color, sub, c).pack(
                side="right", fill="both", expand=True, padx=4)
        self._draw_gauges(stats)
        self._draw_line_chart()
        self._draw_pie_chart()
        self._draw_hbars()
        self._draw_vbars()
        self._refresh_income_charts()

    # ============ به‌روزرسانی نمودارهای درآمد ============
    def _schedule_income_refresh(self):
        """Maintain exactly one recurring Tk after callback per dashboard."""
        if self._destroyed or self._income_refresh_job is not None:
            return
        try:
            self._income_refresh_job = self.after(5000, self._on_income_refresh_timer)
        except tk.TclError:
            self._income_refresh_job = None

    def _on_income_refresh_timer(self):
        self._income_refresh_job = None
        if self._destroyed:
            return
        self._refresh_income_charts()
        self._schedule_income_refresh()

    def _on_destroy(self, event):
        if event.widget is not self:
            return
        self._destroyed = True
        if self._income_refresh_job is not None:
            try:
                self.after_cancel(self._income_refresh_job)
            except tk.TclError:
                pass
            self._income_refresh_job = None

    def _refresh_income_charts(self):
        try:
            trends = get_income_trends()
        except Exception as exc:
            # Leave the rest of the dashboard usable if the invoice query fails.
            print(f"خطا در بروزرسانی نمودار درآمد: {exc}")
            self._empty(self.weekly_income_canvas,
                        self.weekly_income_canvas.winfo_width() or 400,
                        self.weekly_income_canvas.winfo_height() or 220,
                        "خواندن درآمد ممکن نشد")
            self._empty(self.monthly_income_canvas,
                        self.monthly_income_canvas.winfo_width() or 400,
                        self.monthly_income_canvas.winfo_height() or 220,
                        "خواندن درآمد ممکن نشد")
            return
        self._draw_income_line(trends["weekly"]["labels"],
                               trends["weekly"]["values"])
        self._draw_income_months(trends["monthly"]["labels"],
                                 trends["monthly"]["values"])

    def _draw_income_line(self, labels, values):
        c = self.weekly_income_canvas
        c.delete("all")
        c.update_idletasks()
        w, h, cl = c.winfo_width() or 400, c.winfo_height() or 220, self.colors
        if not values:
            self._empty(c, w, h, "هنوز درآمدی ثبت نشده")
            return
        pad_l, pad_r, pad_t, pad_b = 45, 18, 18, 34
        chart_w, chart_h = max(1, w - pad_l - pad_r), max(1, h - pad_t - pad_b)
        max_v = max(values) or 1
        for i in range(4):
            y = pad_t + chart_h * i / 3
            c.create_line(pad_l, y, w - pad_r, y, fill=cl["border"], dash=(2, 4))
        points = []
        for i, value in enumerate(values):
            x = pad_l + chart_w * i / max(1, len(values) - 1)
            y = pad_t + chart_h - (value / max_v) * chart_h
            points.append((x, y))
        if len(points) > 1:
            c.create_line([coord for point in points for coord in point],
                          fill="#06b6d4", width=3, smooth=True)
        for i, (x, y) in enumerate(points):
            c.create_oval(x - 4, y - 4, x + 4, y + 4,
                          fill=cl["card"], outline="#06b6d4", width=2)
            c.create_text(x, y - 12, text=f"{values[i]:,.0f}",
                          fill="#06b6d4", font=("Segoe UI", 8, "bold"))
            c.create_text(x, h - 12, text=labels[i], fill=cl["muted"],
                          font=("Segoe UI", 8))

    def _draw_income_months(self, labels, values):
        c = self.monthly_income_canvas
        c.delete("all")
        c.update_idletasks()
        w, h, cl = c.winfo_width() or 400, c.winfo_height() or 220, self.colors
        if not values:
            self._empty(c, w, h, "هنوز درآمدی ثبت نشده")
            return
        pad_l, pad_r, pad_t, pad_b = 42, 15, 20, 42
        chart_w, chart_h = max(1, w - pad_l - pad_r), max(1, h - pad_t - pad_b)
        max_v = max(values) or 1
        for i in range(4):
            y = pad_t + chart_h * i / 3
            c.create_line(pad_l, y, w - pad_r, y, fill=cl["border"], dash=(2, 4))
        slot = chart_w / max(1, len(values))
        bar_w = slot * 0.56
        base_y = pad_t + chart_h
        for i, value in enumerate(values):
            center = pad_l + slot * (i + 0.5)
            bar_h = (value / max_v) * chart_h
            c.create_rectangle(center - bar_w / 2, base_y - bar_h,
                               center + bar_w / 2, base_y,
                               fill=CHART_COLORS[i % len(CHART_COLORS)], outline="")
            c.create_text(center, max(pad_t + 8, base_y - bar_h - 10),
                          text=f"{value:,.0f}", fill=cl["text"],
                          font=("Segoe UI", 8, "bold"))
            c.create_text(center, base_y + 17, text=labels[i],
                          fill=cl["muted"], font=("Segoe UI", 8))

    # ============ نمودارهای زنده فعلی ============
    def _draw_gauges(self, stats):
        c = self.gauges_canvas
        c.delete("all")
        c.update_idletasks()
        h = 210
        self._gauge_at(c, 75, h / 2, 55, 72, "#06b6d4", "پروژه‌ها",
                       f"{stats['projects']} عدد")
        self._gauge_at(c, 200, h / 2, 55, 58, "#10b981", "کاربران",
                       f"{stats['users']} نفر")
        hours = stats["total_hours"]
        p3 = min((hours / 100) * 100, 100) if hours else 0
        self._gauge_at(c, 325, h / 2, 55, p3, "#f59e0b", "ساعات", f"{hours:,.0f}")

    def _gauge_at(self, c, cx, cy, r, percent, color, label, value_text):
        cl = self.colors
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=90, extent=-359,
                     outline=cl["border"], width=10, style="arc")
        if percent > 0:
            c.create_arc(cx-r, cy-r, cx+r, cy+r, start=90,
                         extent=-(percent / 100) * 360, outline=color,
                         width=10, style="arc")
        c.create_text(cx, cy-4, text=f"{percent:.0f}%", fill=cl["text"],
                      font=("Segoe UI", 13, "bold"))
        c.create_text(cx, cy+12, text=value_text, fill=cl["muted"],
                      font=("Segoe UI", 8))
        c.create_text(cx, cy+r+14, text=label, fill=cl["text"],
                      font=("Segoe UI", 9, "bold"))

    def _draw_line_chart(self):
        c = self.line_canvas
        c.delete("all")
        c.update_idletasks()
        w, h, cl = c.winfo_width() or 400, c.winfo_height() or 210, self.colors
        values = self._get_weekly_hours()
        if not values or all(v == 0 for v in values):
            self._empty(c, w, h, "هنوز داده‌ای برای نمایش")
            return
        labels = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
        pad_l, pad_r, pad_t, pad_b = 30, 15, 20, 35
        chart_w, chart_h = w-pad_l-pad_r, h-pad_t-pad_b
        max_v = max(values) or 1
        for i in range(4):
            y = pad_t + chart_h * i / 3
            c.create_line(pad_l, y, w-pad_r, y, fill=cl["border"], dash=(2, 4))
        pts = []
        for i, value in enumerate(values):
            x = pad_l + chart_w * i / max(1, len(values)-1)
            y = pad_t + chart_h - (value / max_v) * chart_h
            pts.append((x, y))
        poly = [(pad_l, pad_t+chart_h)] + pts + [(w-pad_r, pad_t+chart_h)]
        c.create_polygon([coord for pt in poly for coord in pt],
                         fill=cl["border"], outline="", smooth=True)
        c.create_line([coord for pt in pts for coord in pt],
                      fill="#06b6d4", width=2, smooth=True)
        for i, (x, y) in enumerate(pts):
            c.create_oval(x-4, y-4, x+4, y+4, fill=cl["card"],
                          outline="#06b6d4", width=2)
            c.create_text(x, y-12, text=f"{values[i]:.0f}", fill="#06b6d4",
                          font=("Segoe UI", 8, "bold"))
            c.create_text(x, pad_t+chart_h+15, text=labels[i],
                          fill=cl["muted"], font=("Segoe UI", 8))

    def _get_weekly_hours(self):
        try:
            from electrocalc.data.database import get_connection
            from datetime import timedelta
            conn = get_connection()
            try:
                cur = conn.cursor()
                today = datetime.now().date()
                values = []
                for i in range(6, -1, -1):
                    d = today - timedelta(days=i)
                    cur.execute("""SELECT COALESCE(SUM(hours),0) AS s
                                   FROM timesheets WHERE work_date = ?""",
                                (d.strftime("%Y-%m-%d"),))
                    values.append(cur.fetchone()["s"])
                return values
            finally:
                conn.close()
        except Exception:
            return [0] * 7

    def _draw_pie_chart(self):
        c = self.pie_canvas
        c.delete("all")
        c.update_idletasks()
        w, h, cl = c.winfo_width() or 400, c.winfo_height() or 210, self.colors
        data = db_stats.project_status_counts()
        if not data:
            self._empty(c, w, h, "هنوز پروژه‌ای ثبت نشده")
            return
        cx, cy, r = 90, h/2, 70
        total, start = sum(v for _, v in data) or 1, 90
        for i, (label, value) in enumerate(data):
            extent = (value / total) * 360
            c.create_arc(cx-r, cy-r, cx+r, cy+r, start=start-1,
                         extent=-(extent-2), fill=CHART_COLORS[i % len(CHART_COLORS)],
                         outline=cl["card"], width=2)
            start -= extent
        inner = r * 0.58
        c.create_oval(cx-inner, cy-inner, cx+inner, cy+inner,
                      fill=cl["card"], outline="")
        c.create_text(cx, cy-8, text=str(total), fill=cl["text"],
                      font=("Segoe UI", 18, "bold"))
        c.create_text(cx, cy+12, text="پروژه", fill=cl["muted"], font=("Segoe UI", 8))
        lx, ly = cx+r+15, cy-(len(data)*14)
        for i, (label, value) in enumerate(data):
            color = CHART_COLORS[i % len(CHART_COLORS)]
            c.create_oval(lx, ly+2, lx+10, ly+12, fill=color, outline="")
            c.create_text(lx+16, ly+7, text=f"{label} ({value})",
                          fill=cl["text"], font=("Segoe UI", 9), anchor="w")
            ly += 22

    def _draw_hbars(self):
        c = self.hbars_canvas
        c.delete("all")
        c.update_idletasks()
        w, h, cl = c.winfo_width() or 400, c.winfo_height() or 260, self.colors
        data = db_stats.hours_per_engineer()
        if not data:
            self._empty(c, w, h, "هنوز ساعت کاری ثبت نشده")
            return
        max_v = max(v for _, v in data) or 1
        name_w, val_w, pad, row_h, bar_h = 90, 55, 12, 30, 14
        bar_left, bar_right = pad+val_w, w-name_w-pad
        bar_max = bar_right-bar_left
        for i, (name, value) in enumerate(data[:8]):
            y = pad+i*row_h
            c.create_text(w-pad, y+bar_h/2, text=name, anchor="e",
                          fill=cl["text"], font=("Segoe UI", 10, "bold"))
            c.create_rectangle(bar_left, y+2, bar_right, y+2+bar_h,
                               fill=cl["bg"], outline="")
            bar_w = (value/max_v)*bar_max
            color = CHART_COLORS[i % len(CHART_COLORS)]
            c.create_rectangle(bar_right-bar_w, y+2, bar_right, y+2+bar_h,
                               fill=color, outline="")
            c.create_text(pad+val_w-8, y+bar_h/2+2, text=f"{value:,.0f}h",
                          anchor="e", fill=color, font=("Segoe UI", 9, "bold"))

    def _draw_vbars(self):
        c = self.vbars_canvas
        c.delete("all")
        c.update_idletasks()
        w, h, cl = c.winfo_width() or 400, c.winfo_height() or 260, self.colors
        data = db_stats.expenses_per_project()
        if not data:
            self._empty(c, w, h, "هنوز هزینه‌ای ثبت نشده")
            return
        data = data[:6]
        max_v = max(v for _, v in data) or 1
        pad_l, pad_r, pad_t, pad_b = 40, 15, 25, 50
        chart_h, chart_w = h-pad_t-pad_b, w-pad_l-pad_r
        base_y, n = h-pad_b, len(data)
        slot_w, bar_w = chart_w/n, chart_w/n*0.5
        for i in range(4):
            y = pad_t+chart_h*i/3
            c.create_line(pad_l, y, w-pad_r, y, fill=cl["border"], dash=(2, 4))
        for i, (label, value) in enumerate(data):
            x_center = pad_l+slot_w*(i+0.5)
            bar_h = (value/max_v)*chart_h
            color = CHART_COLORS[i % len(CHART_COLORS)]
            c.create_rectangle(x_center-bar_w/2, base_y-bar_h,
                               x_center+bar_w/2, base_y, fill=color, outline="")
            c.create_text(x_center, base_y-bar_h-8, text=f"{value:,.0f}",
                          fill=color, font=("Segoe UI", 8, "bold"))
            short = label[:10]+"…" if len(label)>10 else label
            c.create_text(x_center, base_y+14, text=short,
                          fill=cl["muted"], font=("Segoe UI", 8))

    def _empty(self, canvas, w, h, text):
        canvas.create_text(w/2, h/2, text=f"📭  {text}",
                           fill=self.colors["muted"], font=("Segoe UI", 10))

    # ============ خروجی Excel ==========
    def export_excel(self):
        try:
            from electrocalc.core import export
            stats = db_stats.get_summary()
            hours_data = db_stats.hours_per_engineer()
            status_data = db_stats.project_status_counts()
            expenses_data = db_stats.expenses_per_project()
            headers = ["شاخص", "مقدار"]
            rows = [
                ("تعداد پروژه‌ها", stats["projects"]),
                ("تعداد کاربران", stats["users"]),
                ("مجموع ساعات کار", f"{stats['total_hours']:,.2f}"),
                ("مجموع هزینه‌ها (تومان)", f"{stats['total_expenses']:,.0f}"),
                ("مجموع مصالح (تومان)", f"{stats['total_materials']:,.0f}"),
                ("در انتظار تأیید", stats["pending_reports"]+stats["pending_expenses"]),
                ("—", "—"), ("ساعات کار مهندسان", "—"),
            ]
            for name, val in hours_data:
                rows.append((f"  {name}", f"{val:,.2f} ساعت"))
            rows.extend([("—", "—"), ("وضعیت پروژه‌ها", "—")])
            for name, val in status_data:
                rows.append((f"  {name}", val))
            rows.extend([("—", "—"), ("هزینه هر پروژه (تومان)", "—")])
            for name, val in expenses_data:
                rows.append((f"  {name}", f"{val:,.0f}"))
            path = export.export_to_excel(headers, rows, title="داشبورد مدیریتی")
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(str(Path(path).parent))
            except Exception:
                pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))

    # ============ خروجی PDF حرفه‌ای ============
    def export_pdf_pro(self):
        """PDF حرفه‌ای با نمودارهای رنگی matplotlib."""
        try:
            from electrocalc.core import report_builder
            path = report_builder.build_dashboard_pdf()
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(path)
            except Exception:
                pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))
