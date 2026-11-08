"""تب مالی پروژه — درآمد، هزینه، سود."""

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from electrocalc.core import finance as fin
from electrocalc.core import report_builder as rb


class FinanceTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#f8fafc")
        self.app = app
        self.current_user = dict(app.current_user) if app.current_user else {}

        self.period = "all"
        self.start_date = None
        self.end_date = None

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
            header, text="💰  مالی پروژه‌ها",
            bg="#7c3aed", fg="white",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="right", padx=20, pady=15)

        # نوار فیلتر
        filter_bar = tk.Frame(self, bg="#f8fafc")
        filter_bar.pack(fill="x", padx=15, pady=10)

        tk.Label(filter_bar, text="بازه:", bg="#f8fafc",
                 font=("Segoe UI", 10)).pack(side="right", padx=5)

        self.period_var = tk.StringVar(value="all")
        for label, val in [("همه", "all"), ("امسال", "year"),
                            ("ماه", "month"), ("هفته", "week"),
                            ("امروز", "today")]:
            tk.Radiobutton(
                filter_bar, text=label, variable=self.period_var,
                value=val, bg="#f8fafc", font=("Segoe UI", 10),
                command=self._on_period_change,
            ).pack(side="right", padx=3)

        tk.Button(
            filter_bar, text="📄 PDF", bg="#ef4444", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=15, pady=5, cursor="hand2",
            command=self._export_pdf,
        ).pack(side="left", padx=5)

        tk.Button(
            filter_bar, text="📊 Excel", bg="#10b981", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            padx=15, pady=5, cursor="hand2",
            command=self._export_excel,
        ).pack(side="left", padx=5)

        # KPI
        self.kpi_frame = tk.Frame(self, bg="#f8fafc")
        self.kpi_frame.pack(fill="x", padx=15, pady=5)

        # جدول
        table_frame = tk.LabelFrame(
            self, text=" 📋 مالی هر پروژه ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#7c3aed", padx=10, pady=10,
        )
        table_frame.pack(fill="x", padx=15, pady=10)

        cols = ("name", "status", "income", "expense", "profit", "margin")
        self.tree = ttk.Treeview(table_frame, columns=cols,
                                  show="headings", height=8)

        headers = {
            "name": "پروژه",
            "status": "وضعیت",
            "income": "درآمد",
            "expense": "هزینه",
            "profit": "سود",
            "margin": "حاشیه",
        }
        for col, txt in headers.items():
            self.tree.heading(col, text=txt)
            self.tree.column(col, anchor="center",
                              width=200 if col == "name" else 110)

        self.tree.pack(fill="x", side="right")
        sb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.tree.yview)
        sb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # نمودارها
        chart_frame = tk.Frame(self, bg="#f8fafc")
        chart_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.chart_right = tk.Frame(chart_frame, bg="white",
                                      relief="solid", bd=1)
        self.chart_right.pack(side="right", fill="both",
                               expand=True, padx=5)

        self.chart_left = tk.Frame(chart_frame, bg="white",
                                     relief="solid", bd=1)
        self.chart_left.pack(side="left", fill="both",
                              expand=True, padx=5)

    # ====================================================
    def refresh(self):
        self._refresh()

    def _on_period_change(self):
        self.period = self.period_var.get()
        self.start_date = None
        self.end_date = None
        self._refresh()

    # ====================================================
    def _refresh(self):
        self._refresh_kpi()
        self._refresh_table()
        self._refresh_charts()

    def _refresh_kpi(self):
        for w in self.kpi_frame.winfo_children():
            w.destroy()

        kpi = fin.get_kpi(self.period, self.start_date, self.end_date)

        cards = [
            ("💰", "درآمد کل", f"{kpi['income']:,.0f}", "#10b981"),
            ("💸", "هزینه کل", f"{kpi['expense']:,.0f}", "#ef4444"),
            ("📈", "سود", f"{kpi['profit']:,.0f}", "#7c3aed"),
            ("📊", "حاشیه سود", f"{kpi['margin']:.1f}%", "#06b6d4"),
        ]

        for icon, title, value, color in cards:
            card = tk.Frame(self.kpi_frame, bg="white",
                             relief="solid", bd=1)
            card.pack(side="right", fill="both", expand=True,
                       padx=5, pady=5)

            tk.Label(card, text=icon, bg="white",
                     font=("Segoe UI", 22)).pack(pady=(10, 0))
            tk.Label(card, text=value, bg="white", fg=color,
                     font=("Segoe UI", 14, "bold")).pack()
            tk.Label(card, text=title, bg="white", fg="#6b7280",
                     font=("Segoe UI", 10)).pack(pady=(0, 10))

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        projects = fin.get_projects_finance(
            self.period, self.start_date, self.end_date)

        for p in projects:
            status_fa = {
                "in_progress": "در جریان",
                "completed": "تمام‌شده",
                "cancelled": "لغو‌شده",
            }.get(p["status"], p["status"])

            self.tree.insert("", "end", values=(
                p["name"],
                status_fa,
                f"{p['income']:,.0f}",
                f"{p['expense']:,.0f}",
                f"{p['profit']:,.0f}",
                f"{p['margin']:.1f}%",
            ))

    def _refresh_charts(self):
        for w in self.chart_left.winfo_children():
            w.destroy()
        for w in self.chart_right.winfo_children():
            w.destroy()

        fp = rb._get_fa_font()

        projects = fin.get_projects_finance(
            self.period, self.start_date, self.end_date)

        # چپ: میلهای — درآمد vs هزینه
        if projects:
            fig1, ax1 = plt.subplots(figsize=(4.5, 3), facecolor="white")
            names = [p["name"][:12] for p in projects[:6]]
            incomes = [p["income"] for p in projects[:6]]
            expenses = [p["expense"] for p in projects[:6]]

            x = list(range(len(names)))
            w = 0.35
            ax1.bar([i - w/2 for i in x], incomes, w,
                     label="درآمد", color="#10b981", edgecolor="white")
            ax1.bar([i + w/2 for i in x], expenses, w,
                     label="هزینه", color="#ef4444", edgecolor="white")
            ax1.set_xticks(x)
            ax1.set_xticklabels(names, fontsize=8)
            for lbl in ax1.get_xticklabels():
                lbl.set_fontproperties(fp)
            ax1.set_yticks([])
            for s in ["top", "right", "left"]:
                ax1.spines[s].set_visible(False)
            leg = ax1.legend(prop=fp, fontsize=8)
            ax1.set_title("درآمد vs هزینه", fontsize=10, fontproperties=fp)
            fig1.tight_layout()

            canvas1 = FigureCanvasTkAgg(fig1, master=self.chart_left)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill="both", expand=True)

        # راست: پای — سهم سود
        pie_data = [(p["name"][:12], p["profit"]) for p in projects[:6]
                    if p["profit"] > 0]
        if pie_data:
            fig2, ax2 = plt.subplots(figsize=(4.5, 3), facecolor="white")
            labels = [d[0] for d in pie_data]
            values = [d[1] for d in pie_data]
            palette = ["#7c3aed", "#06b6d4", "#10b981",
                       "#f59e0b", "#ef4444", "#ec4899"]

            wedges, texts, autotexts = ax2.pie(
                values, labels=labels, colors=palette[:len(values)],
                autopct="%1.1f%%", startangle=90,
                textprops={"fontsize": 8, "fontproperties": fp},
                wedgeprops={"edgecolor": "white", "linewidth": 2},
            )
            for at in autotexts:
                at.set_color("white")
                at.set_fontweight("bold")
                at.set_fontproperties(fp)
            ax2.set_title("سهم سود پروژه‌ها", fontsize=10, fontproperties=fp)
            fig2.tight_layout()

            canvas2 = FigureCanvasTkAgg(fig2, master=self.chart_right)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill="both", expand=True)

    # ====================================================
    def _export_pdf(self):
        try:
            path = fin.build_finance_pdf(
                period=self.period,
                start_date=self.start_date, end_date=self.end_date,
            )
            messagebox.showinfo("موفق", f"PDF ساخته شد:\n{path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))

    def _export_excel(self):
        try:
            path = fin.build_finance_excel(
                period=self.period,
                start_date=self.start_date, end_date=self.end_date,
            )
            messagebox.showinfo("موفق", f"Excel ساخته شد:\n{path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))