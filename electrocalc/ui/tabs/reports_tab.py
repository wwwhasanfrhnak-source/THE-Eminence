"""تب گزارش‌ها — با خروجی Excel و PDF."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from pathlib import Path
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import reports as rp
from electrocalc.core import projects as proj
from electrocalc.ui.scrollable_frame import ScrollableFrame


class ReportsTab(ScrollableFrame):
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

        ttk.Label(parent, text="📝  گزارش‌ها", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="ثبت و مدیریت گزارش‌های کار روزانه",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 15))

        ttk.Button(toolbar, text="+ گزارش جدید",
                   command=self._new).pack(side="left")
        ttk.Button(toolbar, text="✏️ ویرایش",
                   command=self._edit).pack(side="left", padx=5)
        ttk.Button(toolbar, text="🗑 حذف",
                   command=self._delete).pack(side="left")

        if self._is_admin():
            ttk.Button(toolbar, text="✅ تأیید",
                       command=self._approve).pack(side="left", padx=5)
            ttk.Button(toolbar, text="❌ رد",
                       command=self._reject).pack(side="left")

        ttk.Button(toolbar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=5)

        # ⭐ دکمه‌های خروجی
        ttk.Button(toolbar, text="📊 Excel",
                   command=self.export_excel).pack(side="left", padx=5)
        ttk.Button(toolbar, text="📄 PDF",
                   command=self.export_pdf).pack(side="left")

        # جستجو + فیلتر وضعیت
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(search_frame, text="🔍 جستجو:",
                  font=C.FONT_BODY).pack(side="left", padx=(0, 8))
        self.search_var = StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", lambda e: self.refresh())

        ttk.Label(search_frame, text="وضعیت:",
                  font=C.FONT_BODY).pack(side="left", padx=(15, 8))
        self.status_var = StringVar(value="همه")
        status_combo = ttk.Combobox(search_frame, textvariable=self.status_var,
                                     values=["همه", "در انتظار تأیید",
                                             "تأیید شده", "رد شده"],
                                     state="readonly", width=15)
        status_combo.pack(side="left")
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # جدول
        cols = ("id", "project", "author", "date", "title", "hours", "status")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("project", text="پروژه")
        self.tree.heading("author", text="مهندس")
        self.tree.heading("date", text="تاریخ")
        self.tree.heading("title", text="عنوان")
        self.tree.heading("hours", text="ساعت")
        self.tree.heading("status", text="وضعیت")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("project", width=140)
        self.tree.column("author", width=100)
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("title", width=220)
        self.tree.column("hours", width=60, anchor="center")
        self.tree.column("status", width=110, anchor="center")

        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        search = self.search_var.get().strip()

        status_filter = None
        sel_status = self.status_var.get()
        for k, v in rp.STATUS_FA.items():
            if v == sel_status:
                status_filter = k
                break

        author_filter = None
        if not self._is_admin() and self.app.current_user:
            author_filter = self.app.current_user["username"]

        for r in rp.list_reports(search, author_filter, status_filter):
            status_fa = rp.STATUS_FA.get(r["status"], r["status"])
            self.tree.insert("", "end", values=(
                r["id"], r["project_name"] or "-", r["author"],
                r["report_date"] or "-", r["title"],
                f"{r['hours']:.1f}", status_fa))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("هشدار", "اول یک گزارش را انتخاب کنید.")
            return None
        return int(self.tree.item(sel[0], "values")[0])

    def _new(self):
        if not proj.list_projects():
            messagebox.showwarning("هشدار",
                                   "اول باید حداقل یک پروژه بسازید.")
            return
        ReportDialog(self.winfo_toplevel(), on_done=self.refresh,
                     author=(self.app.current_user["username"]
                             if self.app.current_user else ""))

    def _edit(self):
        rid = self._selected_id()
        if not rid:
            return
        r = rp.get_report(rid)
        if r and not self._is_admin() and r["author"] != (self.app.current_user or {}).get("username"):
            messagebox.showerror("خطا", "فقط می‌توانید گزارش‌های خودتان را ویرایش کنید.")
            return
        ReportDialog(self.winfo_toplevel(), on_done=self.refresh, report_id=rid)

    def _delete(self):
        rid = self._selected_id()
        if not rid:
            return
        if not self._is_admin():
            messagebox.showerror("خطا", "فقط مدیر می‌تواند حذف کند.")
            return
        if not messagebox.askyesno("تأیید", "این گزارش حذف شود؟"):
            return
        rp.delete_report(rid)
        self.refresh()

    def _approve(self):
        rid = self._selected_id()
        if not rid:
            return
        username = (self.app.current_user["username"]
                    if self.app.current_user else "admin")
        rp.approve_report(rid, username)
        self.refresh()

    def _reject(self):
        rid = self._selected_id()
        if not rid:
            return
        username = (self.app.current_user["username"]
                    if self.app.current_user else "admin")
        rp.reject_report(rid, username)
        self.refresh()

    # ========================================================
    # خروجی Excel
    # ========================================================
    def _get_export_data(self):
        """داده‌های جدول برای خروجی."""
        headers = ["پروژه", "مهندس", "تاریخ", "عنوان", "ساعت", "وضعیت"]

        rows = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            # vals: (id, project, author, date, title, hours, status)
            rows.append((
                vals[1],  # project
                vals[2],  # author
                vals[3],  # date
                vals[4],  # title
                vals[5],  # hours
                vals[6],  # status
            ))
        return headers, rows

    def export_excel(self):
        try:
            from electrocalc.core import export

            headers, rows = self._get_export_data()
            if not rows:
                messagebox.showwarning("هشدار", "چیزی برای خروجی نیست.")
                return

            path = export.export_to_excel(
                headers, rows,
                title="گزارش‌ها",
                filename=f"reports_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            )

            if messagebox.askyesno("موفق",
                                     f"فایل ذخیره شد:\n{path}\n\n"
                                     "پوشه باز شود؟"):
                os.startfile(str(Path(path).parent))
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    # ========================================================
    # خروجی PDF
    # ========================================================
    def export_pdf(self):
        try:
            from electrocalc.core import export

            headers, rows = self._get_export_data()
            if not rows:
                messagebox.showwarning("هشدار", "چیزی برای خروجی نیست.")
                return

            path = export.export_to_pdf(
                headers, rows,
                title="گزارش‌ها",
                filename=f"reports_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            )

            if messagebox.askyesno("موفق",
                                     f"فایل ذخیره شد:\n{path}\n\n"
                                     "فایل باز شود؟"):
                os.startfile(path)
        except Exception as e:
            messagebox.showerror("خطا", str(e))


# ========================================================
# پنجره ثبت/ویرایش گزارش
# ========================================================
class ReportDialog:
    def __init__(self, parent, on_done=None, report_id=None, author=""):
        self.on_done = on_done
        self.report_id = report_id
        self.author = author

        self.win = tk.Toplevel(parent)
        self.win.title("گزارش جدید" if not report_id else "ویرایش گزارش")
        self.win.geometry("520x600")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui()
        if report_id:
            self._load()

    def _build_ui(self):
        tk.Label(self.win,
                 text="➕ گزارش جدید" if not self.report_id else "✏️ ویرایش گزارش",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="x")

        self.project_var = StringVar()
        self.date_var = StringVar()
        self.title_var = StringVar()
        self.hours_var = StringVar(value="0")

        # پروژه
        tk.Label(f, text="پروژه *:", font=C.FONT_BODY, bg=C.COLOR_BG).grid(
            row=0, column=0, sticky="w", pady=6)
        projects = proj.list_projects()
        self.project_map = {}
        project_display = []
        for p in projects:
            display = f"{p['id']} - {p['name']}"
            project_display.append(display)
            self.project_map[display] = p["id"]
        project_combo = ttk.Combobox(f, textvariable=self.project_var,
                                      values=project_display,
                                      state="readonly", width=30)
        project_combo.grid(row=0, column=1, pady=6, sticky="ew")
        if project_display:
            project_combo.current(0)

        # تاریخ
        tk.Label(f, text="تاریخ *:", font=C.FONT_BODY, bg=C.COLOR_BG).grid(
            row=1, column=0, sticky="w", pady=6)
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(f, textvariable=self.date_var, width=30).grid(
            row=1, column=1, pady=6, sticky="ew")

        # عنوان
        tk.Label(f, text="عنوان *:", font=C.FONT_BODY, bg=C.COLOR_BG).grid(
            row=2, column=0, sticky="w", pady=6)
        ttk.Entry(f, textvariable=self.title_var, width=30).grid(
            row=2, column=1, pady=6, sticky="ew")

        # ساعت
        tk.Label(f, text="ساعت کار:", font=C.FONT_BODY, bg=C.COLOR_BG).grid(
            row=3, column=0, sticky="w", pady=6)
        ttk.Entry(f, textvariable=self.hours_var, width=30).grid(
            row=3, column=1, pady=6, sticky="ew")

        # توضیحات
        tk.Label(f, text="توضیحات:", font=C.FONT_BODY, bg=C.COLOR_BG).grid(
            row=4, column=0, sticky="nw", pady=6)
        self.desc_text = tk.Text(f, width=30, height=10, font=C.FONT_BODY)
        self.desc_text.grid(row=4, column=1, pady=6, sticky="ew")

        f.columnconfigure(1, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="ذخیره", command=self._save).pack(
            side="left", padx=5, ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف", command=self.win.destroy).pack(
            side="left", padx=5, ipadx=20, ipady=4)

    def _load(self):
        r = rp.get_report(self.report_id)
        if not r:
            return
        display = f"{r['project_id']} - {r['project_name']}"
        self.project_var.set(display)
        self.date_var.set(r["report_date"] or "")
        self.title_var.set(r["title"] or "")
        self.hours_var.set(str(r["hours"] or 0))
        self.desc_text.insert("1.0", r["description"] or "")

    def _save(self):
        try:
            project_id = self.project_map.get(self.project_var.get())
            if not project_id:
                raise ValueError("پروژه را انتخاب کنید.")

            try:
                hours = float(self.hours_var.get().strip() or "0")
            except ValueError:
                raise ValueError("ساعت کار باید عدد باشد.")

            desc = self.desc_text.get("1.0", "end").strip()

            if self.report_id:
                rp.update_report(self.report_id, project_id,
                                  self.date_var.get(), self.title_var.get(),
                                  desc, hours)
            else:
                rp.create_report(project_id, self.author,
                                  self.date_var.get(), self.title_var.get(),
                                  desc, hours)
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)