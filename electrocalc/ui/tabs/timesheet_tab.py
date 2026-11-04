"""تب ساعات کار — با خروجی Excel و PDF."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from pathlib import Path
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import management as mgmt
from electrocalc.core import projects as proj
from electrocalc.core import timer as timer_module
from electrocalc.ui.scrollable_frame import ScrollableFrame


STATUS_FA = {"pending": "در انتظار", "approved": "تأیید شده",
             "rejected": "رد شده"}


class TimesheetTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()
        self.refresh()

    def _is_admin(self):
        return (self.app.current_user
                and self.app.current_user["role"] == "admin")

    def build_ui(self):
        parent = self.inner

        ttk.Label(parent, text="⏰  ساعات کار", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="سابقه ساعات کار همه کاربران",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 15))

        ttk.Button(bar, text="+ ثبت ساعت",
                   command=self._new).pack(side="left")

        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=8)
            ttk.Button(bar, text="✅ تأیید",
                       command=self._approve).pack(side="left")
            ttk.Button(bar, text="❌ رد",
                       command=self._reject).pack(side="left", padx=8)

        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=8)

        # ⭐ خروجی
        ttk.Button(bar, text="📊 Excel",
                   command=self.export_excel).pack(side="left", padx=8)
        ttk.Button(bar, text="📄 PDF",
                   command=self.export_pdf).pack(side="left")

        if self._is_admin():
            ttk.Label(bar, text="فیلتر کاربر:",
                      font=C.FONT_BODY).pack(side="left", padx=(15, 5))
            self.filter_user_var = StringVar(value="همه")
            users_list = ["همه"] + [u["username"]
                                     for u in proj.get_active_users()]
            combo = ttk.Combobox(bar, textvariable=self.filter_user_var,
                                  values=users_list, state="readonly", width=15)
            combo.pack(side="left")
            combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        else:
            self.filter_user_var = StringVar(value="")

        self.summary_var = StringVar(value="")
        ttk.Label(parent, textvariable=self.summary_var,
                  font=C.FONT_HEADER, foreground=C.COLOR_SUCCESS).pack(
            anchor="w", pady=(0, 10))

        if self._is_admin():
            cols = ("id", "username", "project", "date", "start",
                    "end", "hours", "status")
        else:
            cols = ("id", "project", "date", "start", "end",
                    "hours", "status")

        self.cols = cols
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)

        headers = {
            "id": "ID", "username": "مهندس", "project": "پروژه",
            "date": "تاریخ", "start": "ورود", "end": "خروج",
            "hours": "ساعت", "status": "وضعیت",
        }
        widths = {
            "id": 45, "username": 100, "project": 140, "date": 90,
            "start": 65, "end": 65, "hours": 65, "status": 90,
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                              anchor="w" if c in ("project", "username")
                              else "center")

        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        username = None
        if self._is_admin():
            fu = self.filter_user_var.get()
            if fu and fu != "همه":
                username = fu
        else:
            if self.app.current_user:
                username = self.app.current_user["username"]

        rows = mgmt.list_timesheets(username=username)

        total_hours = 0.0
        for t in rows:
            total_hours += t["hours"] or 0
            status_fa = STATUS_FA.get(t["status"], t["status"])

            if self._is_admin():
                values = (t["id"], t["username"], t["project_name"] or "-",
                          t["work_date"] or "-", t["start_time"] or "-",
                          t["end_time"] or "-", f"{t['hours']:.2f}",
                          status_fa)
            else:
                values = (t["id"], t["project_name"] or "-",
                          t["work_date"] or "-", t["start_time"] or "-",
                          t["end_time"] or "-", f"{t['hours']:.2f}",
                          status_fa)

            self.tree.insert("", "end", values=values)

        self.summary_var.set(
            f"📊  مجموع: {total_hours:,.2f} ساعت   |   تعداد ردیف: {len(rows)}")

    def _selected_id(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "یک ردیف انتخاب کن.")
            return None
        return int(self.tree.item(s[0], "values")[0])

    def _new(self):
        if not proj.list_projects():
            messagebox.showwarning("هشدار", "اول یک پروژه بساز.")
            return
        TimesheetDialog(self.winfo_toplevel(), on_done=self.refresh,
                        username=(self.app.current_user["username"]
                                  if self.app.current_user else ""))

    def _delete(self):
        tid = self._selected_id()
        if not tid:
            return
        if not messagebox.askyesno("تأیید", "این ردیف حذف شود؟"):
            return
        mgmt.delete_timesheet(tid)
        self.refresh()

    def _approve(self):
        tid = self._selected_id()
        if not tid:
            return
        u = (self.app.current_user["username"]
             if self.app.current_user else "admin")
        mgmt.approve_item("timesheets", tid, u)
        self.refresh()

    def _reject(self):
        tid = self._selected_id()
        if not tid:
            return
        u = (self.app.current_user["username"]
             if self.app.current_user else "admin")
        mgmt.reject_item("timesheets", tid, u)
        self.refresh()

    # ========================================================
    # خروجی
    # ========================================================
    def _get_export_data(self):
        if self._is_admin():
            headers = ["مهندس", "پروژه", "تاریخ", "ورود",
                       "خروج", "ساعت", "وضعیت"]
            start = 1
        else:
            headers = ["پروژه", "تاریخ", "ورود",
                       "خروج", "ساعت", "وضعیت"]
            start = 1

        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            rows.append(tuple(vals[start:]))
        return headers, rows

    def export_excel(self):
        try:
            from electrocalc.core import export
            headers, rows = self._get_export_data()
            if not rows:
                messagebox.showwarning("هشدار", "چیزی برای خروجی نیست.")
                return
            path = export.export_to_excel(
                headers, rows, title="ساعات کار",
                filename=f"timesheets_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            )
            if messagebox.askyesno("موفق",
                                     f"ذخیره شد:\n{path}\n\nباز شود؟"):
                os.startfile(str(Path(path).parent))
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def export_pdf(self):
        try:
            from electrocalc.core import export
            headers, rows = self._get_export_data()
            if not rows:
                messagebox.showwarning("هشدار", "چیزی برای خروجی نیست.")
                return
            path = export.export_to_pdf(
                headers, rows, title="ساعات کار",
                filename=f"timesheets_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            )
            if messagebox.askyesno("موفق",
                                     f"ذخیره شد:\n{path}\n\nباز شود؟"):
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("خطا", str(e))


# ========================================================
class TimesheetDialog:
    def __init__(self, parent, on_done=None, username=""):
        self.on_done = on_done
        self.username = username
        self.project_map = {}
        for p in proj.list_projects():
            self.project_map[f"{p['id']} - {p['name']}"] = p["id"]

        self.win = tk.Toplevel(parent)
        self.win.title("ثبت ساعت کار")
        self.win.geometry("460x420")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()

        tk.Label(self.win, text="➕ ثبت ساعت کار",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="x")

        self.project_var = StringVar()
        self.date_var = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.start_var = StringVar()
        self.end_var = StringVar()
        self.hours_var = StringVar(value="0")
        self.desc_var = StringVar()

        rows = [
            ("پروژه:", "combo", self.project_var, list(self.project_map.keys())),
            ("تاریخ:", "entry", self.date_var, None),
            ("ساعت ورود:", "entry", self.start_var, None),
            ("ساعت خروج:", "entry", self.end_var, None),
            ("مجموع ساعت:", "entry", self.hours_var, None),
            ("توضیحات:", "entry", self.desc_var, None),
        ]

        for i, (label, kind, var, values) in enumerate(rows):
            tk.Label(f, text=label, font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=i, column=0, sticky="w",
                                          pady=7, padx=(0, 8))
            if kind == "combo":
                cb = ttk.Combobox(f, textvariable=var, values=values,
                                   state="readonly", width=28)
                if values:
                    cb.current(0)
                cb.grid(row=i, column=1, pady=7, sticky="ew")
            else:
                ttk.Entry(f, textvariable=var, width=30).grid(
                    row=i, column=1, pady=7, sticky="ew")

        f.columnconfigure(1, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="ذخیره", command=self._save).pack(
            side="left", padx=5, ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف",
                   command=self.win.destroy).pack(
            side="left", padx=5, ipadx=20, ipady=4)

    def _save(self):
        try:
            pid = self.project_map.get(self.project_var.get())
            if not pid:
                raise ValueError("پروژه را انتخاب کن.")

            hours = float(self.hours_var.get().strip() or "0")
            if hours <= 0:
                raise ValueError("مجموع ساعت باید بزرگ‌تر از صفر باشد.")

            mgmt.create_timesheet(
                username=self.username,
                project_id=pid,
                work_date=self.date_var.get(),
                start_time=self.start_var.get(),
                end_time=self.end_var.get(),
                hours=hours,
                description=self.desc_var.get(),
            )
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)