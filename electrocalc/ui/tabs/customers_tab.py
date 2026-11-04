"""تب مدیریت مشتریان."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import customers as customers_module
from electrocalc.ui.scrollable_frame import ScrollableFrame


class CustomersTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()
        self.refresh()

    def _is_admin(self):
        return (self.app.current_user
                and self.app.current_user["role"] == "admin")

    def build_ui(self):
        p = self.inner

        ttk.Label(p, text="👥  مدیریت مشتریان",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p, text="اطلاعات کامل مشتریان و سابقه پروژه‌هایشان",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # نوار دکمه‌ها
        bar = ttk.Frame(p)
        bar.pack(fill="x", pady=(0, 12))

        ttk.Button(bar, text="+ مشتری جدید",
                   command=self._new).pack(side="left")
        ttk.Button(bar, text="✏️ ویرایش",
                   command=self._edit).pack(side="left", padx=8)
        ttk.Button(bar, text="📁 پروژه‌های این مشتری",
                   command=self._show_projects).pack(side="left")
        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=8)
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")

        # جستجو
        s = ttk.Frame(p)
        s.pack(fill="x", pady=(0, 10))
        ttk.Label(s, text="🔍 جستجو:",
                  font=C.FONT_BODY).pack(side="left", padx=(0, 8))
        self.search_var = StringVar()
        e = ttk.Entry(s, textvariable=self.search_var, width=30)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda ev: self.refresh())

        # خلاصه
        self.summary_var = StringVar(value="")
        ttk.Label(p, textvariable=self.summary_var,
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_SUCCESS).pack(anchor="w", pady=(0, 10))

        # جدول
        cols = ("id", "name", "company", "mobile", "city", "projects")
        self.tree = ttk.Treeview(p, columns=cols, show="headings", height=15)

        headers = {"id": "ID", "name": "نام", "company": "شرکت",
                   "mobile": "موبایل", "city": "شهر", "projects": "پروژه‌ها"}
        widths = {"id": 40, "name": 180, "company": 180,
                  "mobile": 120, "city": 100, "projects": 80}

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                              anchor="center" if c in ("id", "projects")
                              else "w")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._show_projects())

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        search = self.search_var.get().strip()
        rows = customers_module.list_customers(search)

        for c in rows:
            stats = customers_module.customer_stats(c["name"])
            self.tree.insert("", "end", iid=str(c["id"]),
                              values=(c["id"], c["name"],
                                       c["company"] or "-",
                                       c["mobile"] or c["phone"] or "-",
                                       c["city"] or "-",
                                       stats["projects"]))

        self.summary_var.set(f"📊  مجموع: {len(rows)} مشتری")

    def _selected_id(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "اول یک مشتری انتخاب کن.")
            return None
        return int(s[0])

    def _new(self):
        CustomerDialog(self.winfo_toplevel(), on_done=self.refresh,
                        created_by=(self.app.current_user["username"]
                                    if self.app.current_user else ""))

    def _edit(self):
        cid = self._selected_id()
        if not cid:
            return
        CustomerDialog(self.winfo_toplevel(), on_done=self.refresh,
                        customer_id=cid)

    def _delete(self):
        cid = self._selected_id()
        if not cid:
            return
        if not messagebox.askyesno("تأیید", "این مشتری حذف شود؟"):
            return
        customers_module.delete_customer(cid)
        self.refresh()

    def _show_projects(self):
        cid = self._selected_id()
        if not cid:
            return
        c = customers_module.get_customer(cid)
        if not c:
            return
        projects = customers_module.get_customer_projects(c["name"])
        stats = customers_module.customer_stats(c["name"])

        win = tk.Toplevel(self.winfo_toplevel())
        win.title(f"پروژه‌های {c['name']}")
        win.geometry("700x500")
        win.configure(bg=C.COLOR_BG)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        tk.Label(win, text=f"📁  پروژه‌های {c['name']}",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 5))

        info = f"🏢 {c['company'] or '-'}   |   📱 {c['mobile'] or c['phone'] or '-'}   |   🏙️ {c['city'] or '-'}"
        tk.Label(win, text=info, font=C.FONT_BODY,
                 bg=C.COLOR_BG, fg=C.COLOR_MUTED).pack(pady=(0, 5))

        tk.Label(win,
                 text=f"📊 مجموع پروژه‌ها: {stats['projects']}   |   "
                      f"💰 مجموع هزینه‌ها: {stats['total_expenses']:,.0f} تومان",
                 font=C.FONT_HEADER, bg=C.COLOR_BG,
                 fg=C.COLOR_SUCCESS).pack(pady=(0, 15))

        if not projects:
            tk.Label(win, text="📭 هیچ پروژه‌ای برای این مشتری ثبت نشده",
                     font=C.FONT_BODY, bg=C.COLOR_BG,
                     fg=C.COLOR_MUTED).pack(pady=30)
        else:
            frame = tk.Frame(win, bg=C.COLOR_BG)
            frame.pack(fill="both", expand=True, padx=20, pady=10)

            cols = ("id", "name", "status", "start", "end")
            tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", height=12)
            tree.heading("id", text="ID")
            tree.heading("name", text="نام")
            tree.heading("status", text="وضعیت")
            tree.heading("start", text="شروع")
            tree.heading("end", text="پایان")
            tree.column("id", width=45, anchor="center")
            tree.column("name", width=250)
            tree.column("status", width=120, anchor="center")
            tree.column("start", width=100, anchor="center")
            tree.column("end", width=100, anchor="center")
            tree.pack(fill="both", expand=True)

            from electrocalc.core.projects import STATUS_FA
            for p in projects:
                status_fa = STATUS_FA.get(p["status"], p["status"])
                tree.insert("", "end", values=(
                    p["id"], p["name"], status_fa,
                    p["start_date"] or "-", p["end_date"] or "-"))

        ttk.Button(win, text="بستن",
                   command=win.destroy).pack(pady=15, ipadx=20)


class CustomerDialog:
    """پنجره ساخت/ویرایش مشتری."""

    def __init__(self, parent, on_done=None, customer_id=None, created_by=""):
        self.on_done = on_done
        self.customer_id = customer_id
        self.created_by = created_by

        self.win = tk.Toplevel(parent)
        self.win.title("مشتری جدید" if not customer_id else "ویرایش مشتری")
        self.win.geometry("520x620")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()
        if customer_id:
            self._load()

    def _build_ui(self):
        tk.Label(self.win,
                 text="➕ مشتری جدید" if not self.customer_id else "✏️ ویرایش مشتری",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="both", expand=True)

        self.vars = {}
        fields = [
            ("name", "نام *:"),
            ("company", "نام شرکت:"),
            ("phone", "تلفن ثابت:"),
            ("mobile", "موبایل:"),
            ("email", "ایمیل:"),
            ("city", "شهر:"),
            ("national_id", "کد ملی:"),
            ("economic_code", "کد اقتصادی:"),
        ]

        for i, (key, label) in enumerate(fields):
            tk.Label(f, text=label, font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=i, column=0,
                                          sticky="w", pady=6, padx=(0, 8))
            var = StringVar()
            self.vars[key] = var
            ttk.Entry(f, textvariable=var, width=30).grid(
                row=i, column=1, sticky="ew", pady=6)

        # آدرس
        row = len(fields)
        tk.Label(f, text="آدرس:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0,
                                      sticky="nw", pady=6, padx=(0, 8))
        self.address_text = tk.Text(f, width=30, height=3, font=C.FONT_BODY)
        self.address_text.grid(row=row, column=1, sticky="ew", pady=6)

        # یادداشت
        row += 1
        tk.Label(f, text="یادداشت:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0,
                                      sticky="nw", pady=6, padx=(0, 8))
        self.notes_text = tk.Text(f, width=30, height=4, font=C.FONT_BODY)
        self.notes_text.grid(row=row, column=1, sticky="ew", pady=6)

        f.columnconfigure(1, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="💾 ذخیره",
                   command=self._save).pack(side="left", padx=5,
                                             ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف",
                   command=self.win.destroy).pack(side="left", padx=5,
                                                    ipadx=20, ipady=4)

    def _load(self):
        c = customers_module.get_customer(self.customer_id)
        if not c:
            return
        for key in self.vars:
            self.vars[key].set(c[key] or "")
        self.address_text.insert("1.0", c["address"] or "")
        self.notes_text.insert("1.0", c["notes"] or "")

    def _save(self):
        try:
            name = self.vars["name"].get().strip()
            if not name:
                raise ValueError("نام مشتری الزامی است.")

            address = self.address_text.get("1.0", "end").strip()
            notes = self.notes_text.get("1.0", "end").strip()

            if self.customer_id:
                customers_module.update_customer(
                    self.customer_id,
                    name,
                    self.vars["company"].get(),
                    self.vars["phone"].get(),
                    self.vars["mobile"].get(),
                    self.vars["email"].get(),
                    address,
                    self.vars["city"].get(),
                    self.vars["national_id"].get(),
                    self.vars["economic_code"].get(),
                    notes,
                )
            else:
                customers_module.create_customer(
                    name,
                    self.vars["company"].get(),
                    self.vars["phone"].get(),
                    self.vars["mobile"].get(),
                    self.vars["email"].get(),
                    address,
                    self.vars["city"].get(),
                    self.vars["national_id"].get(),
                    self.vars["economic_code"].get(),
                    notes,
                    self.created_by,
                )
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)