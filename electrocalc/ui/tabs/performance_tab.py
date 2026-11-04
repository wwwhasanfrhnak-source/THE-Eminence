"""تب عملکرد مهندسین."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from datetime import datetime
from pathlib import Path

from electrocalc.config import constants as C
from electrocalc.core import performance as perf
from electrocalc.ui.scrollable_frame import ScrollableFrame


CHART_COLORS = ["#7c3aed", "#06b6d4", "#10b981", "#f59e0b",
                "#ef4444", "#ec4899", "#8b5cf6", "#14b8a6"]


class PerformanceTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.period_var = StringVar(master=self, value="month")
        self.build_ui()
        self.refresh()

    def _is_admin(self):
        return (self.app.current_user
                and self.app.current_user["role"] == "admin")

    def build_ui(self):
        p = self.inner

        # ---------- هدر ----------
        header = ttk.Frame(p)
        header.pack(fill="x", pady=(0, 15))

        ttk.Label(header, text="👷  عملکرد مهندسین",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(side="right")

        # فیلتر بازه
        fbox = ttk.Frame(header)
        fbox.pack(side="left")

        ttk.Label(fbox, text="بازه:",
                  font=C.FONT_BODY).pack(side="right", padx=(0, 5))

        for val, label in [("week", "این هفته"),
                            ("month", "این ماه"),
                            ("all", "کل")]:
            ttk.Radiobutton(fbox, text=label, value=val,
                            variable=self.period_var,
                            command=self.refresh).pack(side="right", padx=5)

        ttk.Button(fbox, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=10)

        ttk.Label(p,
                  text="آمار و نمودار عملکرد هر مهندس",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # ---------- KPI برای مدیر ----------
        if self._is_admin():
            self.kpi_frame = tk.Frame(p, bg=C.COLOR_BG)
            self.kpi_frame.pack(fill="x", pady=(0, 15))

        # ---------- نمودارها ----------
        # نمودار ۱: میله‌ای افقی — ساعات مهندسین
        self.hours_box = ttk.LabelFrame(p, text="📊  ساعات کار مهندسان",
                                          padding=10)
        self.hours_box.pack(fill="x", pady=(0, 12))

        self.hours_canvas = tk.Canvas(self.hours_box, height=250,
                                        bg=C.COLOR_BG, highlightthickness=0)
        self.hours_canvas.pack(fill="x")

        # نمودار ۲: خطی — فعالیت گزارش‌دهی هفتگی
        self.line_box = ttk.LabelFrame(p, text="📈  فعالیت گزارش‌دهی (۷ روز اخیر)",
                                         padding=10)
        self.line_box.pack(fill="x", pady=(0, 12))

        self.line_canvas = tk.Canvas(self.line_box, height=220,
                                       bg=C.COLOR_BG, highlightthickness=0)
        self.line_canvas.pack(fill="x")

        # نمودار ۳: پای‌چارت — توزیع پروژه‌ها
        self.pie_box = ttk.LabelFrame(p, text="🥧  توزیع پروژه‌ها بین مهندسین",
                                        padding=10)
        self.pie_box.pack(fill="x", pady=(0, 12))

        self.pie_canvas = tk.Canvas(self.pie_box, height=240,
                                      bg=C.COLOR_BG, highlightthickness=0)
        self.pie_canvas.pack(fill="x")

        # ---------- جدول کامل عملکرد ----------
        self.table_box = ttk.LabelFrame(p, text="📋  جدول عملکرد", padding=10)
        self.table_box.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("username", "full_name", "hours", "reports",
                "approved", "rejected", "projects", "expenses")
        self.tree = ttk.Treeview(self.table_box, columns=cols,
                                   show="headings", height=12)

        headers = {
            "username": "نام کاربری", "full_name": "نام کامل",
            "hours": "ساعت کار", "reports": "گزارش",
            "approved": "تأییدشده", "rejected": "رد‌شده",
            "projects": "پروژه", "expenses": "هزینه",
        }
        widths = {
            "username": 100, "full_name": 150,
            "hours": 90, "reports": 80, "approved": 90,
            "rejected": 80, "projects": 80, "expenses": 120,
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                              anchor="center" if c != "full_name" else "w")

        self.tree.pack(fill="both", expand=True)

    # ========================================================
    def refresh(self):
        period = self.period_var.get()
        data = perf.get_summary_period(period)

        # اگه مهندسه → فقط خودش
        if not self._is_admin() and self.app.current_user:
            username = self.app.current_user["username"]
            data["hours"] = [(u, h) for u, h in data["hours"] if u == username]
            data["expenses"] = [(u, e) for u, e in data["expenses"]
                                  if u == username]

        self._draw_kpi(data)
        self._draw_hours_chart(data["hours"])
        self._draw_line_chart()
        self._draw_pie_chart(data["projects"])
        self._fill_table(data)

    # ============ KPI ============
    def _draw_kpi(self, data):
        if not self._is_admin():
            return

        for w in self.kpi_frame.winfo_children():
            w.destroy()

        total_hours = sum(h for _, h in data["hours"])
        total_reports = sum(r["total"] for r in data["reports"].values())
        total_approved = sum(r["approved"] for r in data["reports"].values())
        total_engineers = len(data["hours"])

        cards = [
            ("👷", "مهندسین فعال", total_engineers, C.COLOR_HEADER_BG),
            ("⏰", "ساعت کل", f"{total_hours:,.0f}", C.COLOR_SUCCESS),
            ("📝", "گزارش کل", total_reports, C.COLOR_ACCENT),
            ("✅", "تأییدشده", total_approved, C.COLOR_SUCCESS),
        ]

        for icon, title, value, color in cards:
            card = tk.Frame(self.kpi_frame, bg=C.COLOR_TAB_BG,
                             highlightbackground=color, highlightthickness=2)
            card.pack(side="right", fill="both", expand=True, padx=4)

            tk.Label(card, text=icon, font=("Segoe UI Emoji", 18),
                     bg=C.COLOR_TAB_BG, fg=color).pack(pady=(10, 2))
            tk.Label(card, text=str(value), font=("Segoe UI", 14, "bold"),
                     bg=C.COLOR_TAB_BG, fg=C.COLOR_TEXT).pack()
            tk.Label(card, text=title, font=C.FONT_SMALL,
                     bg=C.COLOR_TAB_BG, fg=C.COLOR_MUTED).pack(pady=(0, 10))

    # ============ نمودار میله‌ای افقی ============
    def _draw_hours_chart(self, hours_data):
        c = self.hours_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 800
        h = c.winfo_height() or 250

        if not hours_data:
            c.create_text(w / 2, h / 2, text="📭  داده‌ای برای نمایش نیست",
                          fill=C.COLOR_MUTED, font=C.FONT_BODY)
            return

        max_v = max(v for _, v in hours_data) or 1

        name_w = 100
        val_w = 80
        pad = 12
        row_h = 32
        bar_h = 18

        bar_left = pad + val_w
        bar_right = w - name_w - pad
        bar_max = bar_right - bar_left

        for i, (name, value) in enumerate(hours_data[:10]):
            y = pad + i * row_h

            # نام
            c.create_text(w - pad, y + bar_h / 2,
                          text=name, anchor="e",
                          fill=C.COLOR_TEXT,
                          font=("Segoe UI", 10, "bold"))

            # پس‌زمینه
            c.create_rectangle(bar_left, y + 2, bar_right, y + 2 + bar_h,
                                fill="#f1f5f9", outline="")

            # مقدار
            bar_w = (value / max_v) * bar_max
            color = CHART_COLORS[i % len(CHART_COLORS)]
            c.create_rectangle(bar_right - bar_w, y + 2,
                                bar_right, y + 2 + bar_h,
                                fill=color, outline="")

            # عدد
            c.create_text(pad + val_w - 8, y + bar_h / 2 + 2,
                          text=f"{value:,.1f}h", anchor="e",
                          fill=color, font=("Segoe UI", 9, "bold"))

    # ============ نمودار خطی ============
    def _draw_line_chart(self):
        c = self.line_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 800
        h = c.winfo_height() or 220

        data = perf.get_weekly_report_activity()
        if not data or all(v == 0 for _, v in data):
            c.create_text(w / 2, h / 2,
                          text="📭  هیچ گزارشی در ۷ روز اخیر ثبت نشده",
                          fill=C.COLOR_MUTED, font=C.FONT_BODY)
            return

        values = [v for _, v in data]
        labels = ["ش", "ی", "د", "س", "چ", "پ", "ج"]

        pad_l, pad_r = 40, 20
        pad_t, pad_b = 20, 35

        chart_w = w - pad_l - pad_r
        chart_h = h - pad_t - pad_b
        max_v = max(values) or 1

        # خطوط راهنما
        for i in range(4):
            y = pad_t + (chart_h * i / 3)
            c.create_line(pad_l, y, w - pad_r, y,
                          fill="#e2e8f0", dash=(2, 4))

        # نقاط
        pts = []
        n = len(values)
        for i, v in enumerate(values):
            x = pad_l + (chart_w * i / (n - 1) if n > 1 else chart_w / 2)
            y = pad_t + chart_h - (v / max_v) * chart_h
            pts.append((x, y))

        # پرشدن
        poly = [(pad_l, pad_t + chart_h)] + pts + [(w - pad_r, pad_t + chart_h)]
        flat = [coord for pt in poly for coord in pt]
        c.create_polygon(flat, fill="#e0f2fe", outline="", smooth=True)

        # خط
        line_pts = [coord for pt in pts for coord in pt]
        c.create_line(line_pts, fill="#06b6d4", width=2.5, smooth=True)

        # نقاط
        for i, (x, y) in enumerate(pts):
            c.create_oval(x - 5, y - 5, x + 5, y + 5,
                          fill=C.COLOR_BG, outline="#06b6d4", width=2)
            if values[i] > 0:
                c.create_text(x, y - 14, text=f"{values[i]:,.0f}",
                              fill="#06b6d4",
                              font=("Segoe UI", 9, "bold"))

        # برچسب‌ها
        for i, lab in enumerate(labels[:n]):
            x = pad_l + (chart_w * i / (n - 1) if n > 1 else chart_w / 2)
            c.create_text(x, pad_t + chart_h + 15,
                          text=lab, fill=C.COLOR_MUTED,
                          font=("Segoe UI", 9))

    # ============ پای‌چارت ============
    def _draw_pie_chart(self, projects_data):
        c = self.pie_canvas
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or 800
        h = c.winfo_height() or 240

        if not projects_data:
            c.create_text(w / 2, h / 2,
                          text="📭  هنوز پروژه‌ای به مهندسی تخصیص داده نشده",
                          fill=C.COLOR_MUTED, font=C.FONT_BODY)
            return

        data = projects_data[:8]

        cx = 140
        cy = h / 2
        r = 85

        total = sum(v for _, v in data) or 1
        start = 90

        for i, (label, value) in enumerate(data):
            extent = (value / total) * 360
            color = CHART_COLORS[i % len(CHART_COLORS)]
            c.create_arc(cx - r, cy - r, cx + r, cy + r,
                         start=start - 1, extent=-(extent - 2),
                         fill=color, outline=C.COLOR_BG, width=3)
            start -= extent

        # دایره وسط
        inner = r * 0.55
        c.create_oval(cx - inner, cy - inner,
                      cx + inner, cy + inner,
                      fill=C.COLOR_BG, outline="")

        c.create_text(cx, cy - 8, text=str(total),
                      fill=C.COLOR_TEXT,
                      font=("Segoe UI", 20, "bold"))
        c.create_text(cx, cy + 14, text="پروژه",
                      fill=C.COLOR_MUTED,
                      font=("Segoe UI", 9))

        # راهنما سمت چپ
        lx = cx + r + 30
        ly = cy - (len(data) * 14)
        for i, (label, value) in enumerate(data):
            color = CHART_COLORS[i % len(CHART_COLORS)]
            c.create_oval(lx, ly + 2, lx + 12, ly + 14,
                          fill=color, outline="")
            c.create_text(lx + 20, ly + 8,
                          text=f"{label}  ({value})",
                          fill=C.COLOR_TEXT,
                          font=("Segoe UI", 10), anchor="w")
            ly += 24

    # ============ جدول ============
    def _fill_table(self, data):
        for i in self.tree.get_children():
            self.tree.delete(i)

        # همه مهندسین رو جمع کن
        usernames = set()
        for u, _ in data["hours"]:
            usernames.add(u)
        for u in data["reports"].keys():
            usernames.add(u)
        for u, _ in data["expenses"]:
            usernames.add(u)
        for u, _ in data["projects"]:
            usernames.add(u)

        # اگه مهندسه → فقط خودش
        if not self._is_admin() and self.app.current_user:
            usernames = {self.app.current_user["username"]}

        if not usernames:
            self.tree.insert("", "end", values=(
                "-", "هنوز داده‌ای نیست", "-", "-", "-", "-", "-", "-"))
            return

        hours_map = dict(data["hours"])
        expenses_map = dict(data["expenses"])
        projects_map = dict(data["projects"])

        # اطلاعات کامل کاربران
        from electrocalc.auth import users as users_module

        for u in sorted(usernames):
            user_row = users_module.get_user(u)
            full_name = (user_row["full_name"] if user_row
                          and user_row["full_name"] else u)

            h = hours_map.get(u, 0)
            r = data["reports"].get(u, {"total": 0, "approved": 0,
                                          "rejected": 0, "pending": 0})
            p = projects_map.get(u, 0)
            e = expenses_map.get(u, 0)

            self.tree.insert("", "end", values=(
                u, full_name,
                f"{h:,.1f}",
                r["total"],
                r["approved"],
                r["rejected"],
                p,
                f"{e:,.0f}",
            ))