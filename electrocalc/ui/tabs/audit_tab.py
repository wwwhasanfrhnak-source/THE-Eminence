"""تب ثبت فعالیت‌ها — فقط مدیر."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import audit as audit_module
from electrocalc.ui.scrollable_frame import ScrollableFrame


class AuditTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()
        self.refresh()

    def build_ui(self):
        p = self.inner

        ttk.Label(p, text="📝  ثبت فعالیت‌ها",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p, text="تاریخچه همه کارهای انجام‌شده در برنامه",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # ===== فیلترها =====
        filters = ttk.LabelFrame(p, text="🔍 فیلترها", padding=12)
        filters.pack(fill="x", pady=(0, 12))

        row1 = ttk.Frame(filters)
        row1.pack(fill="x", pady=4)

        ttk.Label(row1, text="جستجو:", font=C.FONT_BODY).pack(side="right", padx=(0, 6))
        self.search_var = StringVar()
        e = ttk.Entry(row1, textvariable=self.search_var, width=25)
        e.pack(side="right", padx=(0, 15))
        e.bind("<KeyRelease>", lambda ev: self.refresh())

        ttk.Label(row1, text="کاربر:", font=C.FONT_BODY).pack(side="right", padx=(0, 6))
        self.user_var = StringVar(value="همه")
        self.user_combo = ttk.Combobox(row1, textvariable=self.user_var,
                                         state="readonly", width=15)
        self.user_combo.pack(side="right", padx=(0, 15))
        self.user_combo.bind("<<ComboboxSelected>>", lambda ev: self.refresh())

        ttk.Label(row1, text="نوع کار:", font=C.FONT_BODY).pack(side="right", padx=(0, 6))
        self.action_var = StringVar(value="همه")
        self.action_combo = ttk.Combobox(row1, textvariable=self.action_var,
                                          state="readonly", width=18)
        self.action_combo.pack(side="right")
        self.action_combo.bind("<<ComboboxSelected>>", lambda ev: self.refresh())

        # ===== خلاصه =====
        self.summary_var = StringVar(value="")
        ttk.Label(p, textvariable=self.summary_var,
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_SUCCESS).pack(anchor="w", pady=(0, 10))

        # ===== دکمه‌ها =====
        btns = ttk.Frame(p)
        btns.pack(fill="x", pady=(0, 10))

        ttk.Button(btns, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")
        ttk.Button(btns, text="🗑 پاک کردن همه لاگ‌ها",
                   command=self._clear_all).pack(side="left", padx=8)
        ttk.Button(btns, text="🧹 حذف قدیمی‌تر از ۳۰ روز",
                   command=self._cleanup).pack(side="left")

        # ===== جدول =====
        cols = ("id", "time", "user", "action", "obj", "desc")
        self.tree = ttk.Treeview(p, columns=cols, show="headings", height=15)
        self.tree.heading("id", text="#")
        self.tree.heading("time", text="زمان")
        self.tree.heading("user", text="کاربر")
        self.tree.heading("action", text="کار")
        self.tree.heading("obj", text="روی")
        self.tree.heading("desc", text="توضیحات")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("time", width=140, anchor="center")
        self.tree.column("user", width=110, anchor="center")
        self.tree.column("action", width=130, anchor="center")
        self.tree.column("obj", width=100, anchor="center")
        self.tree.column("desc", width=350)

        self.tree.pack(fill="both", expand=True)

        # دابل‌کلیک → نمایش جزئیات
        self.tree.bind("<Double-1>", lambda e: self._show_detail())

    def refresh(self):
        # به‌روزرسانی combobox کاربران
        user_list = ["همه"] + audit_module.get_users_list()
        self.user_combo["values"] = user_list
        if self.user_var.get() not in user_list:
            self.user_var.set("همه")

        # به‌روزرسانی combobox اکشن‌ها
        action_list = ["همه"] + list(audit_module.ACTIONS.values())
        self.action_combo["values"] = action_list
        if self.action_var.get() not in action_list:
            self.action_var.set("همه")

        # فیلترها
        search = self.search_var.get().strip()
        username = None if self.user_var.get() == "همه" else self.user_var.get()

        action = None
        if self.action_var.get() != "همه":
            for k, v in audit_module.ACTIONS.items():
                if v == self.action_var.get():
                    action = k
                    break

        logs = audit_module.list_logs(search, username, action)

        # پاک کردن جدول
        for i in self.tree.get_children():
            self.tree.delete(i)

        # پر کردن
        for log in logs:
            try:
                dt = datetime.fromisoformat(log["created_at"])
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                time_str = log["created_at"] or "-"

            action_fa = audit_module.ACTIONS.get(log["action"], log["action"])
            obj = log["object_type"] or "-"

            self.tree.insert("", "end",
                              iid=str(log["id"]),
                              values=(log["id"], time_str,
                                       log["username"] or "-",
                                       action_fa, obj,
                                       log["description"] or "-"))

        # خلاصه
        total = audit_module.count_logs()
        self.summary_var.set(
            f"📊  نمایش: {len(logs)} رکورد   |   مجموع کل: {total}")

    def _clear_all(self):
        if not messagebox.askyesno(
            "⚠️ تأیید",
            "همه لاگ‌ها پاک شوند؟\n\nاین عمل قابل بازگشت نیست!"
        ):
            return
        if not messagebox.askyesno("⚠️ تأیید نهایی",
                                    "واقعاً مطمئنی؟"):
            return
        audit_module.clear_all()
        self.refresh()
        messagebox.showinfo("موفق", "همه لاگ‌ها پاک شدند.")

    def _cleanup(self):
        if not messagebox.askyesno(
            "🧹 حذف قدیمی‌ها",
            "لاگ‌های قدیمی‌تر از ۳۰ روز حذف شوند؟"
        ):
            return
        n = audit_module.delete_older_than(30)
        self.refresh()
        messagebox.showinfo("موفق", f"{n} رکورد قدیمی حذف شد.")

    def _show_detail(self):
        sel = self.tree.selection()
        if not sel:
            return
        log_id = int(sel[0])

        from electrocalc.data.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_log WHERE id = ?", (log_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            return

        msg = (
            f"🆔 شناسه: {row['id']}\n"
            f"⏰ زمان: {row['created_at']}\n"
            f"👤 کاربر: {row['username'] or '-'}\n"
            f"🎯 کار: {audit_module.ACTIONS.get(row['action'], row['action'])}\n"
            f"📦 روی: {row['object_type'] or '-'}\n"
            f"🆔 شناسه شیء: {row['object_id'] or '-'}\n\n"
            f"📝 توضیحات:\n{row['description'] or '-'}"
        )

        if row["old_value"]:
            msg += f"\n\n📋 مقدار قبلی:\n{row['old_value']}"
        if row["new_value"]:
            msg += f"\n\n🆕 مقدار جدید:\n{row['new_value']}"

        messagebox.showinfo("جزئیات لاگ", msg)