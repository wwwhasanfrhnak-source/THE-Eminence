"""تب تقویم کارگاه — تقویم شمسی با رویدادها."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import jdatetime

from electrocalc.core import calendar_logic as cal


class CalendarTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#f8fafc")
        self.app = app
        self.current_user = dict(app.current_user) if app.current_user else {}

        # ماه و سال جاری
        today = cal.get_today_jalali()
        self.jy = today.year
        self.jm = today.month

        self.events = {}
        self.day_buttons = {}  # {(jy,jm,jd): button}

        self._build_ui()
        self._refresh()

    # ====================================================
    # UI
    # ====================================================
    def _build_ui(self):
        # هدر
        header = tk.Frame(self, bg="#7c3aed", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="📅  تقویم کارگاه",
            bg="#7c3aed", fg="white",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="right", padx=20, pady=15)

        # نوار ناوبری ماه
        nav = tk.Frame(self, bg="#f8fafc")
        nav.pack(fill="x", padx=15, pady=10)

        tk.Button(
            nav, text="◀  ماه بعد", bg="#06b6d4", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=15, pady=6, cursor="hand2",
            command=self._next_month,
        ).pack(side="left", padx=5)

        self.month_lbl = tk.Label(
            nav, text="", bg="#f8fafc", fg="#7c3aed",
            font=("Segoe UI", 15, "bold"))
        self.month_lbl.pack(side="left", padx=20)

        tk.Button(
            nav, text="ماه قبل  ▶", bg="#06b6d4", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=15, pady=6, cursor="hand2",
            command=self._prev_month,
        ).pack(side="left", padx=5)

        tk.Button(
            nav, text="📅 امروز", bg="#10b981", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=15, pady=6, cursor="hand2",
            command=self._goto_today,
        ).pack(side="left", padx=(20, 5))

        # بدنه: تقویم + جزئیات
        body = tk.Frame(self, bg="#f8fafc")
        body.pack(fill="both", expand=True, padx=15, pady=10)

        # تقویم (راست)
        cal_frame = tk.LabelFrame(
            body, text=" 📅 تقویم ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#7c3aed", padx=10, pady=10,
        )
        cal_frame.pack(side="right", fill="both", expand=True, padx=(0, 5))

        # جدول روزهای هفته
        self.weekdays_frame = tk.Frame(cal_frame, bg="#f8fafc")
        self.weekdays_frame.pack(fill="x")

        # گرید روزها
        self.grid_frame = tk.Frame(cal_frame, bg="#f8fafc")
        self.grid_frame.pack(fill="both", expand=True, pady=5)

        # پنل جزئیات (چپ)
        detail_frame = tk.LabelFrame(
            body, text=" 📋 رویدادهای روز ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#7c3aed", padx=10, pady=10,
        )
        detail_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.detail_date_lbl = tk.Label(
            detail_frame, text="یه روز انتخاب کن",
            bg="#f8fafc", fg="#7c3aed",
            font=("Segoe UI", 12, "bold"))
        self.detail_date_lbl.pack(pady=5)

        # لیست رویدادها
        list_container = tk.Frame(detail_frame, bg="#f8fafc")
        list_container.pack(fill="both", expand=True)

        self.detail_canvas = tk.Canvas(
            list_container, bg="#f8fafc", highlightthickness=0)
        detail_sb = ttk.Scrollbar(list_container, orient="vertical",
                                    command=self.detail_canvas.yview)
        self.detail_canvas.configure(yscrollcommand=detail_sb.set)

        detail_sb.pack(side="left", fill="y")
        self.detail_canvas.pack(side="right", fill="both", expand=True)

        self.detail_inner = tk.Frame(self.detail_canvas, bg="#f8fafc")
        self.detail_canvas.create_window(
            (0, 0), window=self.detail_inner, anchor="nw")

        self.detail_inner.bind(
            "<Configure>",
            lambda e: self.detail_canvas.configure(
                scrollregion=self.detail_canvas.bbox("all")))

    # ====================================================
    # ناوبری ماه
    # ====================================================
    def _prev_month(self):
        if self.jm == 1:
            self.jm = 12
            self.jy -= 1
        else:
            self.jm -= 1
        self._refresh()

    def _next_month(self):
        if self.jm == 12:
            self.jm = 1
            self.jy += 1
        else:
            self.jm += 1
        self._refresh()

    def _goto_today(self):
        today = cal.get_today_jalali()
        self.jy = today.year
        self.jm = today.month
        self._refresh()

    # ====================================================
    # بازسازی
    # ====================================================
    def _refresh(self):
        month_name = cal.get_month_name(self.jm)
        self.month_lbl.config(text=f"{month_name}  {self.jy}")

        # رویدادهای ماه
        self.events = cal.get_month_events(self.jy, self.jm)

        self._build_weekdays()
        self._build_grid()

    def _build_weekdays(self):
        for w in self.weekdays_frame.winfo_children():
            w.destroy()

        names = cal.get_weekday_names()
        for i, name in enumerate(names):
            color = "#ef4444" if i == 6 else "#7c3aed"  # جمعه قرمز
            tk.Label(
                self.weekdays_frame, text=name,
                bg="#f8fafc", fg=color,
                font=("Segoe UI", 10, "bold"),
                width=10,
            ).grid(row=0, column=i, padx=1, pady=5)

    def _build_grid(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.day_buttons = {}

        days, first_weekday = cal.get_month_days(self.jy, self.jm)
        today = cal.get_today_jalali()

        # ۶ سطر × ۷ ستون
        for i in range(6):
            self.grid_frame.rowconfigure(i, weight=1)
        for j in range(7):
            self.grid_frame.columnconfigure(j, weight=1)

        row = 0
        col = first_weekday

        # خونه‌های خالی اول
        for _ in range(first_weekday):
            tk.Label(self.grid_frame, text="", bg="#f8fafc").grid(
                row=0, column=_, padx=1, pady=1, sticky="nsew")

        for day in range(1, days + 1):
            # تبدیل به میلادی برای چک رویداد
            j_date = jdatetime.date(self.jy, self.jm, day)
            g_date = j_date.togregorian().strftime("%Y-%m-%d")

            has_events = g_date in self.events
            is_today = (day == today.day
                         and self.jm == today.month
                         and self.jy == today.year)
            is_friday = (col == 6)

            # رنگ
            if is_today:
                bg_color = "#7c3aed"
                fg_color = "white"
            elif has_events:
                bg_color = "#fef3c7"
                fg_color = "#92400e"
            else:
                bg_color = "white"
                fg_color = "#ef4444" if is_friday else "#1f2937"

            # متن دکمه
            text = str(day)
            if has_events:
                event_count = len(self.events[g_date])
                text = f"{day}\n●{event_count}"

            btn = tk.Button(
                self.grid_frame, text=text,
                bg=bg_color, fg=fg_color,
                font=("Segoe UI", 10, "bold" if is_today else "normal"),
                relief="solid", bd=1, cursor="hand2",
                command=lambda d=day, g=g_date: self._select_day(d, g),
            )
            btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            self.day_buttons[(self.jy, self.jm, day)] = btn

            col += 1
            if col > 6:
                col = 0
                row += 1

    # ====================================================
    # انتخاب روز
    # ====================================================
    def _select_day(self, day, g_date):
        # نمایش جزئیات
        j_date = jdatetime.date(self.jy, self.jm, day)
        weekday_names = cal.get_weekday_names()
        weekday = weekday_names[j_date.weekday()]
        self.detail_date_lbl.config(
            text=f"{weekday}  {day}  {cal.get_month_name(self.jm)}  {self.jy}")

        # پاک کردن قبلی
        for w in self.detail_inner.winfo_children():
            w.destroy()

        # رویدادهای این روز
        events = cal.get_day_events(g_date)

        if not events:
            tk.Label(
                self.detail_inner, text="🎉 هیچ رویدادی نیست",
                bg="#f8fafc", fg="#6b7280",
                font=("Segoe UI", 11), pady=20,
            ).pack()
            return

        for ev in events:
            card = tk.Frame(self.detail_inner, bg="white",
                             relief="solid", bd=1)
            card.pack(fill="x", pady=3, padx=3)

            # نوار رنگی
            color_bar = tk.Frame(card, bg=ev["color"], width=5)
            color_bar.pack(side="right", fill="y")

            content = tk.Frame(card, bg="white")
            content.pack(side="right", fill="both", expand=True,
                          padx=8, pady=6)

            # نوع
            tk.Label(content, text=ev["type"],
                     bg="white", fg=ev["color"],
                     font=("Segoe UI", 9, "bold"),
                     anchor="e").pack(anchor="e")

            # عنوان
            tk.Label(content, text=ev["title"],
                     bg="white", fg="#1f2937",
                     font=("Segoe UI", 11, "bold"),
                     anchor="e").pack(anchor="e")

            # توضیحات
            if ev.get("desc"):
                tk.Label(content, text=ev["desc"],
                         bg="white", fg="#6b7280",
                         font=("Segoe UI", 9),
                         anchor="e", wraplength=280,
                         justify="right").pack(anchor="e")

            # اضافه
            if ev.get("extra"):
                tk.Label(content, text=ev["extra"],
                         bg="white", fg="#6b7280",
                         font=("Segoe UI", 9, "italic"),
                         anchor="e").pack(anchor="e")