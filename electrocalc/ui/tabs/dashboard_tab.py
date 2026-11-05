"""تب داشبورد — آمار زنده، نمودارها و خروجی PDF/Excel."""

import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime

from electrocalc.core import dashboard as db_stats
from electrocalc.core.income_trends import get_financial_dashboard
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
    return {key: p[key] for key in
            ("bg", "card", "border", "text", "muted", "accent", "danger", "success")}


class DarkCard(tk.Frame):
    def __init__(self, parent, title="", icon="", pad=14, colors=None, **kw):
        self.colors = colors or _get_colors()
        super().__init__(parent, bg=self.colors["card"],
                         highlightbackground=self.colors["border"],
                         highlightthickness=1, **kw)
        if title:
            head = tk.Frame(self, bg=self.colors["card"])
            head.pack(fill="x", padx=pad, pady=(pad, 8))
            tk.Label(head, text=f"{icon}  {title}", font=("Segoe UI", 12, "bold"),
                     bg=self.colors["card"], fg=self.colors["text"], anchor="e").pack(side="right")
        self.body = tk.Frame(self, bg=self.colors["card"])
        self.body.pack(fill="both", expand=True, padx=pad, pady=(0, pad))


class KpiCard(tk.Frame):
    def __init__(self, parent, icon, title, value, color, subtitle="", colors=None):
        self.colors = colors or _get_colors()
        super().__init__(parent, bg=self.colors["card"],
                         highlightbackground=self.colors["border"], highlightthickness=1)
        self.pack_propagate(False)
        self.configure(height=105)
        tk.Frame(self, bg=color, width=5).pack(side="right", fill="y")
        body = tk.Frame(self, bg=self.colors["card"])
        body.pack(side="right", fill="both", expand=True, padx=14, pady=12)
        tk.Label(body, text=icon, font=("Segoe UI Emoji", 22), bg=self.colors["card"],
                 fg=color).pack(side="right", padx=(0, 10))
        text_frame = tk.Frame(body, bg=self.colors["card"])
        text_frame.pack(side="right", fill="both", expand=True)
        tk.Label(text_frame, text=title, font=("Segoe UI", 9), bg=self.colors["card"],
                 fg=self.colors["muted"], anchor="e").pack(anchor="e")
        tk.Label(text_frame, text=str(value), font=("Segoe UI", 16, "bold"),
                 bg=self.colors["card"], fg=self.colors["text"], anchor="e").pack(anchor="e")
        if subtitle:
            tk.Label(text_frame, text=subtitle, font=("Segoe UI", 8), bg=self.colors["card"],
                     fg=color, anchor="e").pack(anchor="e")


class RevenueCard(DarkCard):
    """KPI card showing invoiced and cash-received totals separately."""
    def __init__(self, parent, title, icon, color, colors):
        super().__init__(parent, title, icon, pad=12, colors=colors)
        self.billed_value = tk.Label(self.body, text="—", bg=colors["card"], fg=colors["text"],
                                     font=("Segoe UI", 18, "bold"), anchor="e")
        self.billed_value.pack(fill="x", anchor="e")
        tk.Label(self.body, text="فاکتورشده", bg=colors["card"], fg=colors["muted"],
                 font=("Segoe UI", 8), anchor="e").pack(fill="x", anchor="e")
        self.received_value = tk.Label(self.body, text="وصول‌شده: —", bg=colors["card"],
                                       fg=color, font=("Segoe UI", 9, "bold"), anchor="e")
        self.received_value.pack(fill="x", anchor="e", pady=(4, 0))

    def set_values(self, billed, received):
        self.billed_value.config(text=f"{billed:,.0f} تومان")
        self.received_value.config(text=f"وصول‌شده: {received:,.0f} تومان")


class DashboardTab(ScrollableFrame):
    REFRESH_MS = 5000

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.colors = _get_colors()
        self._income_refresh_job = None
        self._income_poll_job = None
        self._income_thread = None
        self._income_results = queue.Queue()
        self._destroyed = False
        self.build_ui()
        self.bind("<Destroy>", self._on_destroy, add="+")
        self.after(200, self.refresh)
        self._schedule_income_refresh()

    def build_ui(self):
        p, c = self.inner, self.colors
        header = tk.Frame(p, bg=c["bg"])
        header.pack(fill="x", pady=(0, 15))
        title_frame = tk.Frame(header, bg=c["bg"])
        title_frame.pack(side="right")
        tk.Label(title_frame, text="📊  داشبورد مدیریتی", font=("Segoe UI", 20, "bold"),
                 bg=c["bg"], fg=c["text"], anchor="e").pack(anchor="e")
        tk.Label(title_frame, text="نگاه کلی به وضعیت کارگاه و پروژه‌ها",
                 font=("Segoe UI", 10), bg=c["bg"], fg=c["muted"], anchor="e").pack(anchor="e")
        buttons = tk.Frame(header, bg=c["bg"])
        buttons.pack(side="left", pady=8)
        for text, command, color in [("🔄 بروزرسانی", self.refresh, c["accent"]),
                                     ("📊 Excel", self.export_excel, "#16a34a"),
                                     ("📄 PDF حرفه‌ای", self.export_pdf_pro, c["danger"])]:
            button = tk.Label(buttons, text=text, font=("Segoe UI", 10, "bold"),
                              bg=color, fg="white", padx=14, pady=8, cursor="hand2")
            button.pack(side="right", padx=3)
            button.bind("<Button-1>", lambda event, cmd=command: cmd())

        self.kpi_row = tk.Frame(p, bg=c["bg"])
        self.kpi_row.pack(fill="x", pady=(0, 14))

        revenue_row = tk.Frame(p, bg=c["bg"])
        revenue_row.pack(fill="x", pady=(0, 14))
        self.revenue_cards = {}
        for key, title, icon, color in [
            ("all", "کل درآمد", "💰", "#7c3aed"),
            ("today", "درآمد امروز", "☀️", "#06b6d4"),
            ("week", "درآمد این هفته", "📈", "#10b981"),
            ("month", "درآمد این ماه", "🗓", "#f59e0b"),
        ]:
            card = RevenueCard(revenue_row, title, icon, color, c)
            card.pack(side="right", fill="both", expand=True, padx=4)
            self.revenue_cards[key] = card

        middle = tk.Frame(p, bg=c["bg"])
        middle.pack(fill="x", pady=(0, 14))
        self.gauges_card = DarkCard(middle, "درصد پیشرفت کلی", "🎯", colors=c)
        self.gauges_card.pack(side="right", fill="both", expand=True, padx=(0, 7))
        self.gauges_canvas = tk.Canvas(self.gauges_card.body, height=210, bg=c["card"], highlightthickness=0)
        self.gauges_canvas.pack(fill="both", expand=True)
        self.line_card = DarkCard(middle, "روند کاری هفتگی", "📈", colors=c)
        self.line_card.pack(side="right", fill="both", expand=True, padx=7)
        self.line_canvas = tk.Canvas(self.line_card.body, height=210, bg=c["card"], highlightthickness=0)
        self.line_canvas.pack(fill="both", expand=True)
        self.pie_card = DarkCard(middle, "وضعیت پروژه‌ها", "🥧", colors=c)
        self.pie_card.pack(side="right", fill="both", expand=True, padx=(7, 0))
        self.pie_canvas = tk.Canvas(self.pie_card.body, height=210, bg=c["card"], highlightthickness=0)
        self.pie_canvas.pack(fill="both", expand=True)

        self.income_charts = {}
        chart_specs = [("daily", "درآمد روزانه — ۳۰ روز اخیر", "خطی"),
                       ("weekly", "درآمد هفتگی — ۱۲ هفته اخیر", "خطی"),
                       ("monthly", "درآمد ماهانه — ۱۲ ماه اخیر", "خطی"),
                       ("yearly", "مقایسه درآمد سالانه", "میله‌ای")]
        for row_specs in (chart_specs[:2], chart_specs[2:]):
            row = tk.Frame(p, bg=c["bg"])
            row.pack(fill="x", pady=(0, 14))
            for key, title, chart_type in row_specs:
                card = DarkCard(row, title, "💹", colors=c)
                card.pack(side="right", fill="both", expand=True,
                          padx=(0, 7) if key in ("daily", "monthly") else (7, 0))
                canvas = tk.Canvas(card.body, height=225, bg=c["card"], highlightthickness=0)
                canvas.pack(fill="both", expand=True)
                self.income_charts[key] = (canvas, chart_type)

        bottom = tk.Frame(p, bg=c["bg"])
        bottom.pack(fill="x", pady=(0, 20))
        self.hbars_card = DarkCard(bottom, "ساعات کار مهندسان", "👷", colors=c)
        self.hbars_card.pack(side="right", fill="both", expand=True, padx=(0, 7))
        self.hbars_canvas = tk.Canvas(self.hbars_card.body, height=260, bg=c["card"], highlightthickness=0)
        self.hbars_canvas.pack(fill="both", expand=True)
        self.vbars_card = DarkCard(bottom, "هزینه پروژه‌ها", "💰", colors=c)
        self.vbars_card.pack(side="right", fill="both", expand=True, padx=(7, 0))
        self.vbars_canvas = tk.Canvas(self.vbars_card.body, height=260, bg=c["card"], highlightthickness=0)
        self.vbars_canvas.pack(fill="both", expand=True)

    def refresh(self):
        try:
            stats = db_stats.get_summary()
            self._render_existing_dashboard(stats)
        except Exception as exc:
            print(f"خطا در بروزرسانی داشبورد: {exc}")
        self._start_income_refresh()

    def _render_existing_dashboard(self, stats):
        c = self.colors
        for widget in self.kpi_row.winfo_children():
            widget.destroy()
        kpis = [("📁", "پروژه‌ها", stats["projects"], "#7c3aed", "پروژه فعال"),
                ("👥", "کاربران", stats["users"], "#06b6d4", "کاربر فعال"),
                ("⏰", "ساعت کار", f"{stats['total_hours']:,.0f}", "#10b981", "ساعت کل"),
                ("💰", "هزینه‌ها", f"{stats['total_expenses']:,.0f}", "#ef4444", "تومان"),
                ("🏭", "ارزش انبار", f"{stats['total_materials']:,.0f}", "#f59e0b", "تومان"),
                ("⏳", "در انتظار", stats["pending_reports"] + stats["pending_expenses"], "#ec4899", "نیاز تأیید")]
        for args in kpis:
            KpiCard(self.kpi_row, *args, colors=c).pack(side="right", fill="both", expand=True, padx=4)
        self._draw_gauges(stats)
        self._draw_line_chart()
        self._draw_pie_chart()
        self._draw_hbars()
        self._draw_vbars()

    def _schedule_income_refresh(self):
        if self._destroyed or self._income_refresh_job is not None:
            return
        try:
            self._income_refresh_job = self.after(self.REFRESH_MS, self._on_income_timer)
        except tk.TclError:
            self._income_refresh_job = None

    def _on_income_timer(self):
        self._income_refresh_job = None
        if not self._destroyed:
            self._start_income_refresh()
            self._schedule_income_refresh()

    def _start_income_refresh(self):
        if self._destroyed or (self._income_thread and self._income_thread.is_alive()):
            return
        def load():
            try:
                self._income_results.put((True, get_financial_dashboard()))
            except Exception as exc:
                self._income_results.put((False, str(exc)))
        self._income_thread = threading.Thread(target=load, name="income-dashboard", daemon=True)
        self._income_thread.start()
        self._poll_income_result()

    def _poll_income_result(self):
        self._income_poll_job = None
        if self._destroyed:
            return
        try:
            success, result = self._income_results.get_nowait()
        except queue.Empty:
            if self._income_thread and self._income_thread.is_alive():
                self._income_poll_job = self.after(100, self._poll_income_result)
            return
        self._income_thread = None
        if not success:
            print(f"خطا در خواندن اطلاعات درآمد: {result}")
            for canvas, _ in self.income_charts.values():
                self._empty(canvas, canvas.winfo_width() or 400,
                            canvas.winfo_height() or 220, "خواندن اطلاعات درآمد ممکن نشد")
            return
        self._render_income_dashboard(result)

    def _render_income_dashboard(self, data):
        for key, card in self.revenue_cards.items():
            values = data["summary"][key]
            card.set_values(values["invoiced"], values["received"])
        for key, (canvas, chart_type) in self.income_charts.items():
            self._draw_revenue_chart(canvas, data[key], chart_type)

    def _draw_revenue_chart(self, canvas, series, chart_type):
        canvas.delete("all")
        canvas.update_idletasks()
        width = canvas.winfo_width() or 420
        height = canvas.winfo_height() or 225
        labels = series["labels"]
        billed, received = series["invoiced"], series["received"]
        colors = self.colors
        if not labels:
            self._empty(canvas, width, height, "داده‌ای برای نمایش نیست")
            return
        left, right, top, bottom = 48, 16, 20, 38
        chart_w, chart_h = max(1, width-left-right), max(1, height-top-bottom)
        max_value = max([0.0] + billed + received) or 1.0
        for i in range(4):
            y = top + chart_h * i / 3
            canvas.create_line(left, y, width-right, y, fill=colors["border"], dash=(2, 4))
        if chart_type == "میله‌ای":
            slot = chart_w / max(1, len(labels))
            bar_w = slot * .32
            for i, (bill, paid) in enumerate(zip(billed, received)):
                center = left + slot*(i+.5)
                for offset, value, color in [(-bar_w/2, bill, "#7c3aed"),
                                              (bar_w/2, paid, "#10b981")]:
                    bar_h = value/max_value*chart_h
                    canvas.create_rectangle(center+offset-bar_w/2, top+chart_h-bar_h,
                                            center+offset+bar_w/2, top+chart_h,
                                            fill=color, outline="")
                canvas.create_text(center, height-14, text=labels[i],
                                   fill=colors["muted"], font=("Segoe UI", 8))
        else:
            count = len(labels)
            for values, color in [(billed, "#7c3aed"), (received, "#10b981")]:
                points = []
                for i, value in enumerate(values):
                    x = left + chart_w*i/max(1, count-1)
                    y = top + chart_h - value/max_value*chart_h
                    points.append((x, y))
                if len(points) > 1:
                    canvas.create_line([coord for point in points for coord in point],
                                       fill=color, width=2, smooth=True)
                for x, y in points:
                    canvas.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color)
            label_step = max(1, count // 6)
            for i in range(0, count, label_step):
                x = left + chart_w*i/max(1, count-1)
                canvas.create_text(x, height-14, text=labels[i], fill=colors["muted"],
                                   font=("Segoe UI", 8))
        canvas.create_rectangle(left, 5, left+10, 13, fill="#7c3aed", outline="")
        canvas.create_text(left+15, 9, text="فاکتورشده", anchor="w",
                           fill=colors["muted"], font=("Segoe UI", 8))
        canvas.create_rectangle(left+100, 5, left+110, 13, fill="#10b981", outline="")
        canvas.create_text(left+115, 9, text="وصول‌شده", anchor="w",
                           fill=colors["muted"], font=("Segoe UI", 8))

    def _on_destroy(self, event):
        if event.widget is not self:
            return
        self._destroyed = True
        for job_name in ("_income_refresh_job", "_income_poll_job"):
            job = getattr(self, job_name, None)
            if job:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, job_name, None)

    def _draw_gauges(self, stats):
        c = self.gauges_canvas
        c.delete("all")
        c.update_idletasks()
        h = 210
        self._gauge_at(c, 75, h/2, 55, 72, "#06b6d4", "پروژه‌ها", f"{stats['projects']} عدد")
        self._gauge_at(c, 200, h/2, 55, 58, "#10b981", "کاربران", f"{stats['users']} نفر")
        hours = stats["total_hours"]
        self._gauge_at(c, 325, h/2, 55, min(hours, 100) if hours else 0,
                       "#f59e0b", "ساعات", f"{hours:,.0f}")

    def _gauge_at(self, c, cx, cy, radius, percent, color, label, value_text):
        cl = self.colors
        c.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=90, extent=-359,
                     outline=cl["border"], width=10, style="arc")
        if percent > 0:
            c.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=90,
                         extent=-(percent/100)*360, outline=color, width=10, style="arc")
        c.create_text(cx, cy-4, text=f"{percent:.0f}%", fill=cl["text"], font=("Segoe UI", 13, "bold"))
        c.create_text(cx, cy+12, text=value_text, fill=cl["muted"], font=("Segoe UI", 8))
        c.create_text(cx, cy+radius+14, text=label, fill=cl["text"], font=("Segoe UI", 9, "bold"))

    def _draw_line_chart(self):
        c = self.line_canvas
        c.delete("all")
        c.update_idletasks()
        width, height, cl = c.winfo_width() or 400, c.winfo_height() or 210, self.colors
        values = self._get_weekly_hours()
        if not values or all(value == 0 for value in values):
            self._empty(c, width, height, "هنوز داده‌ای برای نمایش")
            return
        pad_l, pad_r, pad_t, pad_b = 30, 15, 20, 35
        chart_w, chart_h = width-pad_l-pad_r, height-pad_t-pad_b
        max_value = max(values) or 1
        for i in range(4):
            y = pad_t+chart_h*i/3
            c.create_line(pad_l, y, width-pad_r, y, fill=cl["border"], dash=(2, 4))
        points = [(pad_l+chart_w*i/max(1, len(values)-1),
                   pad_t+chart_h-value/max_value*chart_h) for i, value in enumerate(values)]
        polygon = [(pad_l, pad_t+chart_h)] + points + [(width-pad_r, pad_t+chart_h)]
        c.create_polygon([n for point in polygon for n in point], fill=cl["border"], outline="", smooth=True)
        c.create_line([n for point in points for n in point], fill="#06b6d4", width=2, smooth=True)
        labels = ["ش", "ی", "د", "س", "چ", "پ", "ج"]
        for i, (x, y) in enumerate(points):
            c.create_oval(x-4, y-4, x+4, y+4, fill=cl["card"], outline="#06b6d4", width=2)
            c.create_text(x, pad_t+chart_h+15, text=labels[i], fill=cl["muted"], font=("Segoe UI", 8))

    def _get_weekly_hours(self):
        try:
            from datetime import timedelta
            from electrocalc.data.database import get_connection
            connection = get_connection()
            try:
                cursor = connection.cursor()
                today = datetime.now().date()
                values = []
                for offset in range(6, -1, -1):
                    day = today-timedelta(days=offset)
                    cursor.execute("SELECT COALESCE(SUM(hours),0) AS s FROM timesheets WHERE work_date=?",
                                   (day.isoformat(),))
                    values.append(cursor.fetchone()["s"])
                return values
            finally:
                connection.close()
        except Exception:
            return [0]*7

    def _draw_pie_chart(self):
        c = self.pie_canvas
        c.delete("all")
        c.update_idletasks()
        width, height, cl = c.winfo_width() or 400, c.winfo_height() or 210, self.colors
        data = db_stats.project_status_counts()
        if not data:
            self._empty(c, width, height, "هنوز پروژه‌ای ثبت نشده")
            return
        cx, cy, radius = 90, height/2, 70
        total, start = sum(value for _, value in data) or 1, 90
        for i, (label, value) in enumerate(data):
            extent = value/total*360
            c.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=start-1,
                         extent=-(extent-2), fill=CHART_COLORS[i%len(CHART_COLORS)],
                         outline=cl["card"], width=2)
            start -= extent
        inner = radius*.58
        c.create_oval(cx-inner, cy-inner, cx+inner, cy+inner, fill=cl["card"], outline="")
        c.create_text(cx, cy-8, text=str(total), fill=cl["text"], font=("Segoe UI", 18, "bold"))
        c.create_text(cx, cy+12, text="پروژه", fill=cl["muted"], font=("Segoe UI", 8))
        lx, ly = cx+radius+15, cy-len(data)*14
        for i, (label, value) in enumerate(data):
            color = CHART_COLORS[i%len(CHART_COLORS)]
            c.create_oval(lx, ly+2, lx+10, ly+12, fill=color, outline="")
            c.create_text(lx+16, ly+7, text=f"{label} ({value})", fill=cl["text"], font=("Segoe UI", 9), anchor="w")
            ly += 22

    def _draw_hbars(self):
        c = self.hbars_canvas
        c.delete("all")
        c.update_idletasks()
        width, height, cl = c.winfo_width() or 400, c.winfo_height() or 260, self.colors
        data = db_stats.hours_per_engineer()
        if not data:
            self._empty(c, width, height, "هنوز ساعت کاری ثبت نشده")
            return
        max_value = max((value for _, value in data), default=0) or 1
        name_w, value_w, pad, row_h, bar_h = 90, 55, 12, 30, 14
        left, right = pad+value_w, width-name_w-pad
        for i, (name, value) in enumerate(data[:8]):
            y = pad+i*row_h
            c.create_text(width-pad, y+bar_h/2, text=name, anchor="e", fill=cl["text"], font=("Segoe UI", 10, "bold"))
            c.create_rectangle(left, y+2, right, y+2+bar_h, fill=cl["bg"], outline="")
            bar_width = value/max_value*(right-left)
            color = CHART_COLORS[i%len(CHART_COLORS)]
            c.create_rectangle(right-bar_width, y+2, right, y+2+bar_h, fill=color, outline="")
            c.create_text(pad+value_w-8, y+bar_h/2+2, text=f"{value:,.0f}h", anchor="e", fill=color, font=("Segoe UI", 9, "bold"))

    def _draw_vbars(self):
        c = self.vbars_canvas
        c.delete("all")
        c.update_idletasks()
        width, height, cl = c.winfo_width() or 400, c.winfo_height() or 260, self.colors
        data = db_stats.expenses_per_project()
        if not data:
            self._empty(c, width, height, "هنوز هزینه‌ای ثبت نشده")
            return
        data = data[:6]
        max_value = max((value for _, value in data), default=0) or 1
        left, right, top, bottom = 40, 15, 25, 50
        chart_h, chart_w, base = height-top-bottom, width-left-right, height-bottom
        slot, bar_w = chart_w/len(data), chart_w/len(data)*.5
        for i in range(4):
            y = top+chart_h*i/3
            c.create_line(left, y, width-right, y, fill=cl["border"], dash=(2, 4))
        for i, (label, value) in enumerate(data):
            center = left+slot*(i+.5)
            bar_h = value/max_value*chart_h
            color = CHART_COLORS[i%len(CHART_COLORS)]
            c.create_rectangle(center-bar_w/2, base-bar_h, center+bar_w/2, base, fill=color, outline="")
            c.create_text(center, base-bar_h-8, text=f"{value:,.0f}", fill=color, font=("Segoe UI", 8, "bold"))
            c.create_text(center, base+14, text=(label[:10]+"…") if len(label)>10 else label, fill=cl["muted"], font=("Segoe UI", 8))

    def _empty(self, canvas, width, height, text):
        canvas.create_text(width/2, height/2, text=f"📭  {text}", fill=self.colors["muted"], font=("Segoe UI", 10))

    def export_excel(self):
        try:
            from electrocalc.core import export
            stats = db_stats.get_summary()
            hours = db_stats.hours_per_engineer()
            statuses = db_stats.project_status_counts()
            expenses = db_stats.expenses_per_project()
            headers = ["شاخص", "مقدار"]
            rows = [("تعداد پروژه‌ها", stats["projects"]), ("تعداد کاربران", stats["users"]),
                    ("مجموع ساعات کار", f"{stats['total_hours']:,.2f}"),
                    ("مجموع هزینه‌ها (تومان)", f"{stats['total_expenses']:,.0f}"),
                    ("مجموع مصالح (تومان)", f"{stats['total_materials']:,.0f}"),
                    ("در انتظار تأیید", stats["pending_reports"]+stats["pending_expenses"]),
                    ("—", "—"), ("ساعات کار مهندسان", "—")]
            rows.extend((f"  {name}", f"{value:,.2f} ساعت") for name, value in hours)
            rows.extend([("—", "—"), ("وضعیت پروژه‌ها", "—")])
            rows.extend((f"  {name}", value) for name, value in statuses)
            rows.extend([("—", "—"), ("هزینه هر پروژه (تومان)", "—")])
            rows.extend((f"  {name}", f"{value:,.0f}") for name, value in expenses)
            path = export.export_to_excel(headers, rows, title="داشبورد مدیریتی")
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(str(Path(path).parent))
            except Exception:
                pass
        except Exception as exc:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(exc))

    def export_pdf_pro(self):
        try:
            from electrocalc.core import report_builder
            path = report_builder.build_dashboard_pdf()
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(path)
            except Exception:
                pass
        except Exception as exc:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(exc))
