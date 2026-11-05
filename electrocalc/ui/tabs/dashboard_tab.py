"""Modern, theme-aware Tk dashboard with operational and financial summaries."""

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from datetime import datetime

from electrocalc.config import themes as themes_module
from electrocalc.core import dashboard as db_stats
from electrocalc.core.income_trends import get_financial_dashboard
from electrocalc.ui.design_system import TOKENS
from electrocalc.ui.scrollable_frame import ScrollableFrame


CHART_COLORS = ["#3867E8", "#16A6C7", "#168A65", "#E59A26",
                "#D84C5B", "#9B5DE5", "#14A8A0", "#E45D9A"]
REVENUE_COLORS = {"invoiced": "#3867E8", "received": "#168A65"}


def _get_colors():
    try:
        from electrocalc.core import settings as settings_module
        theme_name = settings_module.get_setting("app_theme", "light")
    except Exception:
        theme_name = "light"
    palette = themes_module.get_palette(theme_name)
    return {key: palette[key] for key in
            ("bg", "card", "border", "text", "muted", "accent", "danger", "success")}


class Surface(tk.Frame):
    """A reusable bordered surface; native Tk keeps it dependency-free."""
    def __init__(self, parent, palette, padding=16, **kwargs):
        super().__init__(parent, bg=palette["card"], highlightbackground=palette["border"],
                         highlightthickness=1, **kwargs)
        self.palette = palette
        self.body = tk.Frame(self, bg=palette["card"])
        self.body.pack(fill="both", expand=True, padx=padding, pady=padding)


class SectionCard(Surface):
    def __init__(self, parent, title, icon, palette, height=None):
        super().__init__(parent, palette, padding=14)
        if height:
            self.configure(height=height)
            self.pack_propagate(False)
        header = tk.Frame(self.body, bg=palette["card"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text=title, bg=palette["card"], fg=palette["text"],
                 font=(TOKENS["font_family"], TOKENS["font_section"], "bold"),
                 anchor="e").pack(side="right")
        tk.Label(header, text=icon, bg=palette["card"], fg=palette["accent"],
                 font=("Segoe UI Emoji", 15)).pack(side="right", padx=(0, 7))
        self.content = tk.Frame(self.body, bg=palette["card"])
        self.content.pack(fill="both", expand=True)


class StatCard(Surface):
    def __init__(self, parent, icon, title, value, note, accent, palette):
        super().__init__(parent, palette, padding=13)
        self.configure(height=108)
        self.pack_propagate(False)
        stripe = tk.Frame(self, bg=accent, height=3)
        stripe.pack(fill="x", side="top")
        body = tk.Frame(self, bg=palette["card"])
        body.pack(fill="both", expand=True, padx=13, pady=10)
        title_row = tk.Frame(body, bg=palette["card"])
        title_row.pack(fill="x")
        tk.Label(title_row, text=title, bg=palette["card"], fg=palette["muted"],
                 font=(TOKENS["font_family"], 9, "bold"), anchor="e").pack(side="right")
        tk.Label(title_row, text=icon, bg=palette["card"], fg=accent,
                 font=("Segoe UI Emoji", 14)).pack(side="right", padx=(0, 6))
        tk.Label(body, text=str(value), bg=palette["card"], fg=palette["text"],
                 font=(TOKENS["font_family"], 17, "bold"), anchor="e").pack(anchor="e", pady=(7, 0))
        tk.Label(body, text=note, bg=palette["card"], fg=accent,
                 font=(TOKENS["font_family"], 8), anchor="e").pack(anchor="e")


class RevenueCard(Surface):
    def __init__(self, parent, title, icon, accent, palette):
        super().__init__(parent, palette, padding=12)
        self.configure(height=112)
        self.pack_propagate(False)
        header = tk.Frame(self.body, bg=palette["card"])
        header.pack(fill="x")
        tk.Label(header, text=title, bg=palette["card"], fg=palette["muted"],
                 font=(TOKENS["font_family"], 9, "bold"), anchor="e").pack(side="right")
        tk.Label(header, text=icon, bg=palette["card"], fg=accent,
                 font=("Segoe UI Emoji", 14)).pack(side="right", padx=(0, 5))
        self.invoiced = tk.Label(self.body, text="—", bg=palette["card"], fg=palette["text"],
                                 font=(TOKENS["font_family"], 15, "bold"), anchor="e")
        self.invoiced.pack(fill="x", anchor="e", pady=(7, 0))
        self.received = tk.Label(self.body, text="وصول‌شده: —", bg=palette["card"], fg=accent,
                                 font=(TOKENS["font_family"], 8, "bold"), anchor="e")
        self.received.pack(fill="x", anchor="e")

    def set_values(self, invoiced, received):
        self.invoiced.configure(text=f"{invoiced:,.0f} تومان")
        self.received.configure(text=f"وصول‌شده: {received:,.0f} تومان")


class RevenueChart(tk.Canvas):
    """Responsive native canvas chart with billed/received series and legend."""
    def __init__(self, parent, palette, chart_type="line", **kwargs):
        super().__init__(parent, height=220, bg=palette["card"], highlightthickness=0,
                         borderwidth=0, **kwargs)
        self.palette = palette
        self.chart_type = chart_type
        self.series = {"labels": [], "invoiced": [], "received": []}
        self.bind("<Configure>", self._redraw)

    def set_series(self, series):
        self.series = series or {"labels": [], "invoiced": [], "received": []}
        self._redraw()

    def _redraw(self, event=None):
        self.delete("all")
        width, height = max(self.winfo_width(), 240), max(self.winfo_height(), 170)
        p = self.palette
        labels = self.series.get("labels", [])
        invoiced = self.series.get("invoiced", [])
        received = self.series.get("received", [])
        if not labels:
            self.create_text(width/2, height/2, text="داده‌ای برای نمایش نیست",
                             fill=p["muted"], font=(TOKENS["font_family"], 10))
            return

        legend_y = 8
        self.create_oval(width-108, legend_y, width-98, legend_y+10,
                         fill=REVENUE_COLORS["invoiced"], outline="")
        self.create_text(width-92, legend_y+5, text="فاکتورشده", anchor="w",
                         fill=p["muted"], font=(TOKENS["font_family"], 8))
        self.create_oval(width-205, legend_y, width-195, legend_y+10,
                         fill=REVENUE_COLORS["received"], outline="")
        self.create_text(width-189, legend_y+5, text="وصول‌شده", anchor="w",
                         fill=p["muted"], font=(TOKENS["font_family"], 8))

        left, right, top, bottom = 42, 12, 27, 31
        graph_w, graph_h = max(1, width-left-right), max(1, height-top-bottom)
        max_value = max([0.0] + invoiced + received) or 1.0
        for index in range(4):
            y = top + graph_h*index/3
            self.create_line(left, y, width-right, y, fill=p["border"], dash=(2, 4))

        if self.chart_type == "bar":
            slot = graph_w/max(1, len(labels))
            bar_width = min(18, slot*.30)
            for i, (bill, cash) in enumerate(zip(invoiced, received)):
                center = left+slot*(i+.5)
                for offset, value, color in ((-bar_width/2, bill, REVENUE_COLORS["invoiced"]),
                                             (bar_width/2, cash, REVENUE_COLORS["received"])):
                    bar_height = value/max_value*graph_h
                    self.create_rectangle(center+offset-bar_width/2, top+graph_h-bar_height,
                                          center+offset+bar_width/2, top+graph_h,
                                          fill=color, outline="")
                self._label(i, center, height-bottom+13, labels, len(labels))
            return

        self._draw_line(invoiced, labels, left, top, graph_w, graph_h, max_value,
                        REVENUE_COLORS["invoiced"])
        self._draw_line(received, labels, left, top, graph_w, graph_h, max_value,
                        REVENUE_COLORS["received"])
        count = len(labels)
        step = max(1, count//6)
        for index in range(0, count, step):
            x = left+graph_w*index/max(1, count-1)
            self._label(index, x, height-bottom+13, labels, count)

    def _draw_line(self, values, labels, left, top, graph_w, graph_h, maximum, color):
        points = [(left+graph_w*i/max(1, len(labels)-1),
                   top+graph_h-value/maximum*graph_h) for i, value in enumerate(values)]
        if len(points) > 1:
            self.create_line([coord for point in points for coord in point],
                             fill=color, width=2, smooth=True, splinesteps=12)
        for x, y in points:
            self.create_oval(x-2.5, y-2.5, x+2.5, y+2.5, fill=color, outline=color)

    def _label(self, index, x, y, labels, count):
        if index < count:
            self.create_text(x, y, text=str(labels[index]), fill=self.palette["muted"],
                             font=(TOKENS["font_family"], 7))


class DashboardTab(ScrollableFrame):
    REFRESH_MS = 5000

    def __init__(self, parent, app):
        super().__init__(parent, padding=TOKENS["space_lg"], bg=_get_colors()["bg"])
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
        header.pack(fill="x", pady=(0, TOKENS["space_lg"]))
        title_block = tk.Frame(header, bg=c["bg"])
        title_block.pack(side="right")
        tk.Label(title_block, text="داشبورد مدیریتی", bg=c["bg"], fg=c["text"],
                 font=(TOKENS["font_family"], TOKENS["font_title"], "bold"), anchor="e").pack(anchor="e")
        tk.Label(title_block, text="نمای کلی از عملکرد پروژه‌ها و امور مالی", bg=c["bg"],
                 fg=c["muted"], font=(TOKENS["font_family"], TOKENS["font_body"])).pack(anchor="e", pady=(3, 0))
        actions = tk.Frame(header, bg=c["bg"])
        actions.pack(side="left", pady=5)
        self._action_button(actions, "بروزرسانی", self.refresh, c["accent"])
        self._action_button(actions, "Excel", self.export_excel, c["success"])
        self._action_button(actions, "PDF", self.export_pdf_pro, c["danger"])

        self.kpi_row = tk.Frame(p, bg=c["bg"])
        self.kpi_row.pack(fill="x", pady=(0, TOKENS["space_md"]))
        revenue_row = tk.Frame(p, bg=c["bg"])
        revenue_row.pack(fill="x", pady=(0, TOKENS["space_md"]))
        self.revenue_cards = {}
        for key, title, icon, accent in (
                ("all", "کل درآمد", "💰", c["accent"]),
                ("today", "امروز", "☀️", "#168A65"),
                ("week", "این هفته", "📈", "#168A65"),
                ("month", "این ماه", "🗓", "#E59A26")):
            card = RevenueCard(revenue_row, title, icon, accent, c)
            card.pack(side="right", fill="both", expand=True, padx=4)
            self.revenue_cards[key] = card

        work_row = tk.Frame(p, bg=c["bg"])
        work_row.pack(fill="x", pady=(0, TOKENS["space_md"]))
        self.gauges_card = SectionCard(work_row, "شاخص‌های عملیاتی", "🎯", c, height=265)
        self.gauges_card.pack(side="right", fill="both", expand=True, padx=(0, 6))
        self.gauges_canvas = tk.Canvas(self.gauges_card.content, height=210, bg=c["card"], highlightthickness=0)
        self.gauges_canvas.pack(fill="both", expand=True)
        self.line_card = SectionCard(work_row, "ساعات کار هفتگی", "⏱", c, height=265)
        self.line_card.pack(side="right", fill="both", expand=True, padx=6)
        self.line_canvas = tk.Canvas(self.line_card.content, height=210, bg=c["card"], highlightthickness=0)
        self.line_canvas.pack(fill="both", expand=True)
        self.pie_card = SectionCard(work_row, "وضعیت پروژه‌ها", "◒", c, height=265)
        self.pie_card.pack(side="right", fill="both", expand=True, padx=(6, 0))
        self.pie_canvas = tk.Canvas(self.pie_card.content, height=210, bg=c["card"], highlightthickness=0)
        self.pie_canvas.pack(fill="both", expand=True)

        self.income_charts = {}
        specs = [("daily", "روند درآمد روزانه · ۳۰ روز", "line"),
                 ("weekly", "روند درآمد هفتگی · ۱۲ هفته", "line"),
                 ("monthly", "روند درآمد ماهانه · ۱۲ ماه", "line"),
                 ("yearly", "مقایسه درآمد سالانه", "bar")]
        for row_spec in (specs[:2], specs[2:]):
            row = tk.Frame(p, bg=c["bg"])
            row.pack(fill="x", pady=(0, TOKENS["space_md"]))
            for index, (key, title, kind) in enumerate(row_spec):
                card = SectionCard(row, title, "↗", c, height=285)
                card.pack(side="right", fill="both", expand=True,
                          padx=(0, 6) if index == 0 else (6, 0))
                chart = RevenueChart(card.content, c, chart_type=kind)
                chart.pack(fill="both", expand=True)
                self.income_charts[key] = chart

        lower = tk.Frame(p, bg=c["bg"])
        lower.pack(fill="x", pady=(0, TOKENS["space_lg"]))
        self.hbars_card = SectionCard(lower, "ساعات کار تیم", "👷", c, height=285)
        self.hbars_card.pack(side="right", fill="both", expand=True, padx=(0, 6))
        self.hbars_canvas = tk.Canvas(self.hbars_card.content, height=235, bg=c["card"], highlightthickness=0)
        self.hbars_canvas.pack(fill="both", expand=True)
        self.vbars_card = SectionCard(lower, "هزینه به تفکیک پروژه", "◈", c, height=285)
        self.vbars_card.pack(side="right", fill="both", expand=True, padx=(6, 0))
        self.vbars_canvas = tk.Canvas(self.vbars_card.content, height=235, bg=c["card"], highlightthickness=0)
        self.vbars_canvas.pack(fill="both", expand=True)

    def _action_button(self, parent, text, command, color):
        button = tk.Label(parent, text=text, bg=color, fg="#FFFFFF", cursor="hand2",
                          padx=13, pady=8, font=(TOKENS["font_family"], 9, "bold"))
        button.pack(side="right", padx=4)
        button.bind("<Button-1>", lambda event: command())
        button.bind("<Enter>", lambda event: button.configure(relief="raised"))
        button.bind("<Leave>", lambda event: button.configure(relief="flat"))

    def refresh(self):
        try:
            stats = db_stats.get_summary()
            self._render_operational_stats(stats)
        except Exception as exc:
            print(f"Dashboard refresh error: {exc}")
        self._start_income_refresh()

    def _render_operational_stats(self, stats):
        for widget in self.kpi_row.winfo_children():
            widget.destroy()

        entries = [("📁", "پروژه‌ها", stats["projects"], "پروژه ثبت‌شده", "#3867E8"),
                   ("👥", "کاربران", stats["users"], "کاربر فعال", "#168CCB"),
                   ("⏰", "ساعت کار", f"{stats['total_hours']:,.0f}", "ساعت ثبت‌شده", "#168A65"),
                   ("💳", "هزینه‌ها", f"{stats['total_expenses']:,.0f}", "تومان", "#D84C5B"),
                   ("📦", "ارزش مصالح", f"{stats['total_materials']:,.0f}", "تومان", "#E59A26"),
                   ("⌛", "در انتظار", stats["pending_reports"]+stats["pending_expenses"], "مورد نیاز پیگیری", "#9B5DE5")]

        for args in entries:
            StatCard(self.kpi_row, *args, self.colors).pack(side="right", fill="both", expand=True, padx=4)

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
            print(f"Income chart refresh failed: {result}")
            for chart in self.income_charts.values():
                chart.set_series({"labels": [], "invoiced": [], "received": []})
            return
        for key, card in self.revenue_cards.items():
            summary = result["summary"][key]
            card.set_values(summary["invoiced"], summary["received"])
        for key, chart in self.income_charts.items():
            chart.set_series(result[key])

    def _on_destroy(self, event):
        if event.widget is not self:
            return
        self._destroyed = True
        for attr in ("_income_refresh_job", "_income_poll_job"):
            job = getattr(self, attr, None)
            if job:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, attr, None)

    def _draw_gauges(self, stats):
        canvas = self.gauges_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        height = 210
        self._gauge_at(canvas, 75, height/2, 55, 72, "#168CCB", "پروژه‌ها", f"{stats['projects']} عدد")
        self._gauge_at(canvas, 200, height/2, 55, 58, "#168A65", "کاربران", f"{stats['users']} نفر")
        hours = stats["total_hours"]
        self._gauge_at(canvas, 325, height/2, 55, min(hours, 100) if hours else 0,
                       "#E59A26", "ساعات", f"{hours:,.0f}")

    def _gauge_at(self, canvas, cx, cy, radius, percent, color, label, value_text):
        p = self.colors
        canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=90, extent=-359,
                          outline=p["border"], width=10, style="arc")
        if percent > 0:
            canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=90,
                              extent=-(percent/100)*360, outline=color, width=10, style="arc")
        canvas.create_text(cx, cy-4, text=f"{percent:.0f}%", fill=p["text"], font=(TOKENS["font_family"], 13, "bold"))
        canvas.create_text(cx, cy+12, text=value_text, fill=p["muted"], font=(TOKENS["font_family"], 8))
        canvas.create_text(cx, cy+radius+14, text=label, fill=p["text"], font=(TOKENS["font_family"], 9, "bold"))

    def _draw_line_chart(self):
        canvas = self.line_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        width, height = canvas.winfo_width() or 400, canvas.winfo_height() or 210
        p = self.colors
        values = self._get_weekly_hours()
        if not values or all(value == 0 for value in values):
            self._empty(canvas, width, height, "هنوز داده‌ای برای نمایش")
            return
        left, right, top, bottom = 30, 15, 20, 35
        graph_w, graph_h = width-left-right, height-top-bottom
        maximum = max(values) or 1
        for index in range(4):
            y = top+graph_h*index/3
            canvas.create_line(left, y, width-right, y, fill=p["border"], dash=(2, 4))
        points = [(left+graph_w*i/max(1, len(values)-1), top+graph_h-value/maximum*graph_h)
                  for i, value in enumerate(values)]
        canvas.create_line([coord for point in points for coord in point], fill="#168CCB", width=2, smooth=True)
        for x, y in points:
            canvas.create_oval(x-3, y-3, x+3, y+3, fill=p["card"], outline="#168CCB", width=2)
        for index, label in enumerate(("ش", "ی", "د", "س", "چ", "پ", "ج")):
            x = left+graph_w*index/max(1, len(values)-1)
            canvas.create_text(x, height-12, text=label, fill=p["muted"], font=(TOKENS["font_family"], 8))

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
                    cursor.execute("SELECT COALESCE(SUM(hours),0) AS s FROM timesheets WHERE work_date=?", (day.isoformat(),))
                    values.append(cursor.fetchone()["s"])
                return values
            finally:
                connection.close()
        except Exception:
            return [0]*7

    def _draw_pie_chart(self):
        canvas = self.pie_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        width, height, p = canvas.winfo_width() or 400, canvas.winfo_height() or 210, self.colors
        data = db_stats.project_status_counts()
        if not data:
            self._empty(canvas, width, height, "هنوز پروژه‌ای ثبت نشده")
            return
        cx, cy, radius = 90, height/2, 70
        total, start = sum(value for _, value in data) or 1, 90
        for index, (label, value) in enumerate(data):
            extent = value/total*360
            canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, start=start-1,
                              extent=-(extent-2), fill=CHART_COLORS[index%len(CHART_COLORS)],
                              outline=p["card"], width=2)
            start -= extent
        inner = radius*.58
        canvas.create_oval(cx-inner, cy-inner, cx+inner, cy+inner, fill=p["card"], outline="")
        canvas.create_text(cx, cy-8, text=str(total), fill=p["text"], font=(TOKENS["font_family"], 18, "bold"))
        canvas.create_text(cx, cy+12, text="پروژه", fill=p["muted"], font=(TOKENS["font_family"], 8))
        lx, ly = cx+radius+15, cy-len(data)*14
        for index, (label, value) in enumerate(data):
            color = CHART_COLORS[index%len(CHART_COLORS)]
            canvas.create_oval(lx, ly+2, lx+10, ly+12, fill=color, outline="")
            canvas.create_text(lx+16, ly+7, text=f"{label} ({value})", fill=p["text"],
                               font=(TOKENS["font_family"], 9), anchor="w")
            ly += 22

    def _draw_hbars(self):
        canvas = self.hbars_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        width, p = canvas.winfo_width() or 400, self.colors
        data = db_stats.hours_per_engineer()
        if not data:
            self._empty(canvas, width, canvas.winfo_height() or 260, "هنوز ساعت کاری ثبت نشده")
            return
        maximum = max((value for _, value in data), default=0) or 1
        pad, name_width, value_width, row_height, bar_height = 12, 90, 55, 30, 14
        left, right = pad+value_width, width-name_width-pad
        for index, (name, value) in enumerate(data[:8]):
            y = pad+index*row_height
            canvas.create_text(width-pad, y+bar_height/2, text=name, anchor="e", fill=p["text"],
                               font=(TOKENS["font_family"], 9, "bold"))
            canvas.create_rectangle(left, y+2, right, y+2+bar_height, fill=p["bg"], outline="")
            bar_width = value/maximum*(right-left)
            color = CHART_COLORS[index%len(CHART_COLORS)]
            canvas.create_rectangle(right-bar_width, y+2, right, y+2+bar_height, fill=color, outline="")
            canvas.create_text(pad+value_width-8, y+bar_height/2+2, text=f"{value:,.0f}h", anchor="e",
                               fill=color, font=(TOKENS["font_family"], 9, "bold"))

    def _draw_vbars(self):
        canvas = self.vbars_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        width, height, p = canvas.winfo_width() or 400, canvas.winfo_height() or 260, self.colors
        data = db_stats.expenses_per_project()[:6]
        if not data:
            self._empty(canvas, width, height, "هنوز هزینه‌ای ثبت نشده")
            return
        maximum = max((value for _, value in data), default=0) or 1
        left, right, top, bottom = 40, 15, 25, 50
        graph_h, graph_w, baseline = height-top-bottom, width-left-right, height-bottom
        slot, bar_width = graph_w/len(data), graph_w/len(data)*.5
        for index in range(4):
            y = top+graph_h*index/3
            canvas.create_line(left, y, width-right, y, fill=p["border"], dash=(2, 4))
        for index, (label, value) in enumerate(data):
            center = left+slot*(index+.5)
            bar_height = value/maximum*graph_h
            color = CHART_COLORS[index%len(CHART_COLORS)]
            canvas.create_rectangle(center-bar_width/2, baseline-bar_height, center+bar_width/2, baseline,
                                    fill=color, outline="")
            canvas.create_text(center, baseline-bar_height-8, text=f"{value:,.0f}", fill=color,
                               font=(TOKENS["font_family"], 8, "bold"))
            short = label[:10]+"…" if len(label)>10 else label
            canvas.create_text(center, baseline+14, text=short, fill=p["muted"], font=(TOKENS["font_family"], 8))

    def _empty(self, canvas, width, height, text):
        canvas.create_text(width/2, height/2, text=f"📭  {text}", fill=self.colors["muted"],
                           font=(TOKENS["font_family"], 10))

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