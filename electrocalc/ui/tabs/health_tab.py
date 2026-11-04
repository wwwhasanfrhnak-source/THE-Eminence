"""تب بررسی سلامت پایگاه داده — فقط مدیر."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import health as health_module
from electrocalc.ui.scrollable_frame import ScrollableFrame


TABLE_FA = {
    "users": "کاربران",
    "projects": "پروژه‌ها",
    "project_members": "اعضای پروژه",
    "reports": "گزارش‌ها",
    "timesheets": "ساعات کار",
    "materials": "مصالح",
    "expenses": "هزینه‌ها",
    "files": "فایل‌ها",
    "messages": "پیام‌ها",
    "company": "اطلاعات شرکت",
    "active_sessions": "جلسه‌های فعال",
    "audit_log": "ثبت فعالیت‌ها",
}


class HealthTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()
        self.after(100, self.refresh)

    def build_ui(self):
        p = self.inner

        ttk.Label(p, text="🛡️  بررسی سلامت پایگاه داده",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p, text="بررسی کامل، فشرده‌سازی و مشکلات اطلاعات",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # دکمه‌ها
        btns = ttk.Frame(p)
        btns.pack(fill="x", pady=(0, 15))
        ttk.Button(btns, text="🔄 بررسی مجدد",
                   command=self.refresh).pack(side="left")
        ttk.Button(btns, text="🗜️ فشرده‌سازی (VACUUM)",
                   command=self._vacuum).pack(side="left", padx=8)

        # ===== کارت‌های خلاصه =====
        self.cards_frame = tk.Frame(p, bg=C.COLOR_BG)
        self.cards_frame.pack(fill="x", pady=(0, 15))

        # ===== وضعیت کلی =====
        status_box = ttk.LabelFrame(p, text="وضعیت کلی", padding=15)
        status_box.pack(fill="x", pady=(0, 15))

        self.status_var = StringVar(value="در حال بررسی...")
        self.status_label = tk.Label(status_box,
                                       textvariable=self.status_var,
                                       font=("Segoe UI", 12, "bold"),
                                       bg=C.COLOR_BG,
                                       fg=C.COLOR_MUTED, anchor="e")
        self.status_label.pack(fill="x", pady=5)

        # ===== هشدارها =====
        warn_box = ttk.LabelFrame(p, text="⚠️ هشدارها", padding=15)
        warn_box.pack(fill="x", pady=(0, 15))
        self.warn_var = StringVar(value="-")
        tk.Label(warn_box, textvariable=self.warn_var,
                 font=C.FONT_BODY, bg=C.COLOR_BG,
                 fg=C.COLOR_DANGER, anchor="e",
                 justify="right", wraplength=800).pack(fill="x")

        # ===== جدول رکوردها =====
        records_box = ttk.LabelFrame(p, text="📊 تعداد رکوردهای هر جدول",
                                      padding=10)
        records_box.pack(fill="both", expand=True)

        cols = ("table", "name", "count")
        self.tree = ttk.Treeview(records_box, columns=cols,
                                  show="headings", height=14)
        self.tree.heading("table", text="نام جدول")
        self.tree.heading("name", text="نام فارسی")
        self.tree.heading("count", text="تعداد رکورد")
        self.tree.column("table", width=180)
        self.tree.column("name", width=200)
        self.tree.column("count", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        # پاک کارت‌ها
        for w in self.cards_frame.winfo_children():
            w.destroy()

        try:
            r = health_module.check_all()
        except Exception as e:
            self.status_var.set(f"❌ خطا: {e}")
            return

        # کارت‌ها
        cards = [
            ("💾", "حجم دیتابیس", r["db_size_str"], C.COLOR_HEADER_BG),
            ("📊", "کل رکوردها", f"{r['total_records']:,}", C.COLOR_SUCCESS),
            ("📋", "تعداد جدول", f"{len(r['tables'])}", C.COLOR_ACCENT),
            ("⚠️", "هشدارها", f"{len(r['warnings'])}",
             C.COLOR_DANGER if r["warnings"] else C.COLOR_SUCCESS),
        ]

        for icon, title, value, color in cards:
            card = tk.Frame(self.cards_frame, bg=C.COLOR_TAB_BG,
                            highlightbackground=color,
                            highlightthickness=2)
            card.pack(side="right", fill="both", expand=True, padx=4)

            tk.Label(card, text=icon, font=("Segoe UI", 18),
                     bg=C.COLOR_TAB_BG, fg=color).pack(pady=(10, 2))
            tk.Label(card, text=str(value), font=("Segoe UI", 14, "bold"),
                     bg=C.COLOR_TAB_BG, fg=C.COLOR_TEXT).pack()
            tk.Label(card, text=title, font=C.FONT_SMALL,
                     bg=C.COLOR_TAB_BG, fg=C.COLOR_MUTED).pack(pady=(0, 10))

        # وضعیت
        if not r["db_exists"]:
            self.status_var.set("❌ فایل پایگاه داده پیدا نشد")
            self.status_label.config(fg=C.COLOR_DANGER)
        elif r["integrity_ok"]:
            self.status_var.set("✅  پایگاه داده سالم است")
            self.status_label.config(fg=C.COLOR_SUCCESS)
        else:
            self.status_var.set(f"❌  مشکل یکپارچگی: {r['integrity_msg']}")
            self.status_label.config(fg=C.COLOR_DANGER)

        # هشدارها
        if r["warnings"]:
            self.warn_var.set("\n".join(r["warnings"]))
        else:
            self.warn_var.set("✅ هیچ هشداری وجود ندارد")
            self.warn_var.set("✅ هیچ هشداری وجود ندارد")

        # جدول
        for i in self.tree.get_children():
            self.tree.delete(i)

        for t in sorted(r["row_counts"].keys()):
            n = r["row_counts"][t]
            count_str = f"{n:,}" if n >= 0 else "خطا"
            self.tree.insert("", "end",
                              values=(t, TABLE_FA.get(t, t), count_str))

        # رکوردهای یتیم
        if r["orphan_count"] > 0:
            self.tree.insert("", "end",
                              values=("orphans", "⚠️ رکوردهای یتیم",
                                       r["orphan_count"]),
                              tags=("warn",))
            self.tree.tag_configure("warn", foreground=C.COLOR_DANGER)

    def _vacuum(self):
        if not messagebox.askyesno(
            "🗜️ فشرده‌سازی",
            "پایگاه داده فشرده شود؟\n\n"
            "این کار حجم فایل رو کم می‌کنه. ممکنه چند ثانیه طول بکشه."
        ):
            return
        try:
            health_module.vacuum_db()
            self.refresh()
            messagebox.showinfo("موفق", "فشرده‌سازی انجام شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))