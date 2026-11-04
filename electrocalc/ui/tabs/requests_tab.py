"""تب درخواست مصالح — مهندس می‌سازه، مدیر تأیید و به مشتری می‌فرسته."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import material_requests as mr_module
from electrocalc.core import projects as proj
from electrocalc.ui.scrollable_frame import ScrollableFrame


class RequestsTab(ScrollableFrame):
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

        ttk.Label(p, text="📋  درخواست مصالح",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p,
                  text="مهندس نیاز پروژه رو ثبت می‌کنه → مدیر تأیید می‌کنه → برای مشتری می‌ره",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # دکمه‌ها
        bar = ttk.Frame(p)
        bar.pack(fill="x", pady=(0, 12))

        ttk.Button(bar, text="+ درخواست جدید",
                   command=self._new).pack(side="left")
        ttk.Button(bar, text="👁 مشاهده",
                   command=self._view).pack(side="left", padx=8)

        if self._is_admin():
            ttk.Button(bar, text="✅ تأیید",
                       command=lambda: self._set_status("approved")).pack(side="left")
            ttk.Button(bar, text="📤 ارسال به مشتری",
                       command=lambda: self._set_status("sent")).pack(side="left", padx=8)
            ttk.Button(bar, text="❌ رد",
                       command=lambda: self._set_status("rejected")).pack(side="left")
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=8)

        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")

        # فیلتر
        f = ttk.Frame(p)
        f.pack(fill="x", pady=(0, 10))

        ttk.Label(f, text="وضعیت:",
                  font=C.FONT_BODY).pack(side="right", padx=(0, 5))
        self.filter_status = StringVar(value="همه")
        status_combo = ttk.Combobox(
            f, textvariable=self.filter_status,
            values=["همه"] + list(mr_module.STATUS_FA.values()),
            state="readonly", width=20,
        )
        status_combo.pack(side="right")
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # خلاصه
        self.summary_var = StringVar(value="")
        ttk.Label(p, textvariable=self.summary_var,
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_SUCCESS).pack(anchor="w", pady=(0, 10))

        # جدول
        cols = ("id", "title", "project", "requester", "total",
                "customer", "status")
        self.tree = ttk.Treeview(p, columns=cols, show="headings", height=15)

        headers = {
            "id": "ID", "title": "عنوان", "project": "پروژه",
            "requester": "درخواست‌کننده", "total": "جمع تخمینی",
            "customer": "مشتری", "status": "وضعیت",
        }
        widths = {
            "id": 40, "title": 200, "project": 130, "requester": 100,
            "total": 120, "customer": 130, "status": 130,
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                              anchor="center" if c in ("id", "total")
                              else "w")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._view())

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        # فیلتر وضعیت
        status_filter = None
        if self.filter_status.get() != "همه":
            for k, v in mr_module.STATUS_FA.items():
                if v == self.filter_status.get():
                    status_filter = k
                    break

        # فیلتر کاربر
        requester = None
        if not self._is_admin() and self.app.current_user:
            requester = self.app.current_user["username"]

        rows = mr_module.list_requests(requester=requester,
                                        status=status_filter)

        total_amount = 0
        for r in rows:
            total_amount += r["total_estimate"] or 0
            status_fa = mr_module.STATUS_FA.get(r["status"], r["status"])
            self.tree.insert("", "end", iid=str(r["id"]),
                              values=(r["id"], r["title"],
                                       r["project_name"] or "-",
                                       r["requester"],
                                       f"{r['total_estimate']:,.0f}",
                                       r["customer_name"] or "-",
                                       status_fa))

        # رنگ‌بندی بر اساس وضعیت
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            status = vals[6]
            if status == "ارسال شده به مشتری":
                self.tree.item(iid, tags=("sent",))
            elif status == "تأیید شده":
                self.tree.item(iid, tags=("approved",))
            elif status == "رد شده":
                self.tree.item(iid, tags=("rejected",))

        self.tree.tag_configure("sent", foreground="#10b981")
        self.tree.tag_configure("approved", foreground="#0284c7")
        self.tree.tag_configure("rejected", foreground=C.COLOR_MUTED)

        self.summary_var.set(
            f"📊  مجموع: {len(rows)} درخواست   |   "
            f"جمع تخمینی: {total_amount:,.0f} تومان")

    def _selected_id(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "اول یک درخواست انتخاب کن.")
            return None
        return int(s[0])

    def _new(self):
        if not proj.list_projects():
            messagebox.showwarning("هشدار",
                                    "اول باید حداقل یک پروژه بسازید.")
            return
        RequestDialog(self.winfo_toplevel(),
                       on_done=self.refresh,
                       requester=(self.app.current_user["username"]
                                  if self.app.current_user else ""))

    def _view(self):
        rid = self._selected_id()
        if not rid:
            return
        ViewDialog(self.winfo_toplevel(), rid, self._is_admin(),
                    on_done=self.refresh)

    def _set_status(self, status):
        rid = self._selected_id()
        if not rid:
            return

        status_fa = mr_module.STATUS_FA[status]
        if not messagebox.askyesno("تأیید", f"وضعیت به «{status_fa}» تغییر کنه؟"):
            return

        try:
            mr_module.update_status(
                rid, status,
                approved_by=(self.app.current_user["username"]
                             if self.app.current_user else "admin"),
            )
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _delete(self):
        rid = self._selected_id()
        if not rid:
            return
        if not messagebox.askyesno("تأیید", "این درخواست حذف شود؟"):
            return
        mr_module.delete_request(rid)
        self.refresh()


class RequestDialog:
    """پنجره ساخت درخواست جدید."""

    def __init__(self, parent, on_done=None, requester=""):
        self.on_done = on_done
        self.requester = requester

        self.win = tk.Toplevel(parent)
        self.win.title("درخواست مصالح جدید")
        self.win.geometry("620x700")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()

    def _build_ui(self):
        tk.Label(self.win, text="📋  درخواست مصالح جدید",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="both", expand=True)

        # پروژه
        tk.Label(f, text="پروژه *:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.project_var = StringVar()
        self.project_map = {}
        proj_list = []
        for p in proj.list_projects():
            d = f"{p['id']} - {p['name']}"
            proj_list.append(d)
            self.project_map[d] = (p["id"], p["customer"] or "")
        proj_combo = ttk.Combobox(f, textvariable=self.project_var,
                                    values=proj_list, state="readonly",
                                    width=45)
        proj_combo.grid(row=0, column=1, sticky="ew", pady=6)
        if proj_list:
            proj_combo.current(0)

        # عنوان
        tk.Label(f, text="عنوان *:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.title_var = StringVar()
        ttk.Entry(f, textvariable=self.title_var, width=45).grid(
            row=1, column=1, sticky="ew", pady=6)

        # مشتری
        tk.Label(f, text="مشتری:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=2, column=0, sticky="w", pady=6)
        self.customer_var = StringVar()
        customers = ["(بدون مشتری)"] + mr_module.get_customers_list()
        cust_combo = ttk.Combobox(f, textvariable=self.customer_var,
                                    values=customers, width=45)
        cust_combo.grid(row=2, column=1, sticky="ew", pady=6)
        cust_combo.current(0)

        # توضیحات
        tk.Label(f, text="توضیحات کلی:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=3, column=0, sticky="nw", pady=6)
        self.desc_text = tk.Text(f, width=45, height=3, font=C.FONT_BODY)
        self.desc_text.grid(row=3, column=1, sticky="ew", pady=6)

        # لیست اقلام
        tk.Label(f, text="📝  لیست اقلام:", font=C.FONT_HEADER,
                 bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(15, 5))

        tk.Label(f, text="(هر قلم در یک خط — مثال: ۵۰ متر کابل ۳۵ ضخیم)",
                 font=C.FONT_SMALL, bg=C.COLOR_BG,
                 fg=C.COLOR_MUTED).grid(row=5, column=0, columnspan=2,
                                         sticky="w", pady=(0, 5))

        self.items_text = tk.Text(f, width=45, height=10, font=C.FONT_BODY)
        self.items_text.grid(row=6, column=0, columnspan=2,
                              sticky="ew", pady=6)

        # جمع تخمینی
        tk.Label(f, text="جمع تخمینی (تومان):", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=7, column=0, sticky="w", pady=6)
        self.total_var = StringVar()
        ttk.Entry(f, textvariable=self.total_var, width=45).grid(
            row=7, column=1, sticky="ew", pady=6)

        f.columnconfigure(1, weight=1)

        # دکمه‌ها
        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="💾 ثبت درخواست",
                   command=self._save).pack(side="left", padx=5,
                                             ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف",
                   command=self.win.destroy).pack(side="left", padx=5,
                                                    ipadx=20, ipady=4)

    def _save(self):
        try:
            project_info = self.project_map.get(self.project_var.get())
            if not project_info:
                raise ValueError("پروژه را انتخاب کن.")
            project_id, project_customer = project_info

            customer = self.customer_var.get().strip()
            if customer == "(بدون مشتری)":
                customer = project_customer or ""

            total_text = self.total_var.get().strip().replace(",", "")
            try:
                total = float(total_text) if total_text else 0
            except ValueError:
                total = 0

            mr_module.create_request(
                project_id=project_id,
                requester=self.requester,
                title=self.title_var.get(),
                description=self.desc_text.get("1.0", "end").strip(),
                items_text=self.items_text.get("1.0", "end").strip(),
                total_estimate=total,
                customer_name=customer,
            )
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)


class ViewDialog:
    """پنجره نمایش جزئیات درخواست."""

    def __init__(self, parent, request_id, is_admin, on_done=None):
        self.request_id = request_id
        self.is_admin = is_admin
        self.on_done = on_done

        r = mr_module.get_request(request_id)
        if not r:
            messagebox.showerror("خطا", "درخواست پیدا نشد.")
            return

        self.win = tk.Toplevel(parent)
        self.win.title(f"درخواست: {r['title']}")
        self.win.geometry("640x700")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui(r)

    def _build_ui(self, r):
        p = self.win

        # عنوان
        header = tk.Frame(p, bg=C.COLOR_HEADER_BG, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text=f"📋  {r['title']}",
                 font=("Segoe UI", 15, "bold"),
                 bg=C.COLOR_HEADER_BG, fg="white",
                 anchor="e").pack(side="right", padx=20, pady=20)

        status_fa = mr_module.STATUS_FA.get(r["status"], r["status"])
        tk.Label(header, text=status_fa,
                 font=("Segoe UI", 10),
                 bg=C.COLOR_HEADER_BG, fg="#ffdd00",
                 anchor="w").pack(side="left", padx=20)

        # اطلاعات
        info_frame = tk.Frame(p, bg=C.COLOR_BG)
        info_frame.pack(fill="x", padx=30, pady=15)

        def add_row(label, value):
            row = tk.Frame(info_frame, bg=C.COLOR_BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=("Segoe UI", 10, "bold"),
                     bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                     anchor="e", width=15).pack(side="right")
            tk.Label(row, text=value or "-", font=C.FONT_BODY,
                     bg=C.COLOR_BG, fg=C.COLOR_MUTED,
                     anchor="e").pack(side="right", padx=10)

        add_row("پروژه:", r["project_name"])
        add_row("درخواست‌کننده:", r["requester"])
        add_row("مشتری:", r["customer_name"])
        add_row("جمع تخمینی:",
                f"{r['total_estimate']:,.0f} تومان")
        add_row("تاریخ ثبت:", (r["created_at"] or "")[:19].replace("T", " "))

        if r["description"]:
            tk.Label(p, text="📄 توضیحات:",
                     font=("Segoe UI", 10, "bold"),
                     bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                     anchor="e").pack(anchor="e", padx=30, pady=(10, 0))
            tk.Label(p, text=r["description"],
                     font=C.FONT_BODY, bg=C.COLOR_BG,
                     fg=C.COLOR_MUTED, wraplength=550,
                     justify="right", anchor="e").pack(
                anchor="e", padx=30, pady=(0, 10))

        # لیست اقلام
        tk.Label(p, text="📝 لیست اقلام درخواستی:",
                 font=("Segoe UI", 12, "bold"),
                 bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG,
                 anchor="e").pack(anchor="e", padx=30, pady=(10, 5))

        items_frame = tk.Frame(p, bg=C.COLOR_TAB_BG,
                                highlightbackground=C.COLOR_BORDER,
                                highlightthickness=1)
        items_frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        items_txt = tk.Text(items_frame, font=("Segoe UI", 11),
                             bg=C.COLOR_TAB_BG, fg=C.COLOR_TEXT,
                             relief="flat", padx=15, pady=15,
                             wrap="word")
        items_txt.pack(fill="both", expand=True)
        items_txt.insert("1.0", r["items_text"] or "(خالی)")
        items_txt.config(state="disabled")

        # یادداشت مدیر
        if r["admin_note"]:
            tk.Label(p, text="💬 یادداشت مدیر:",
                     font=("Segoe UI", 10, "bold"),
                     bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                     anchor="e").pack(anchor="e", padx=30, pady=(5, 0))
            tk.Label(p, text=r["admin_note"],
                     font=C.FONT_BODY, bg=C.COLOR_BG,
                     fg=C.COLOR_MUTED, wraplength=550,
                     justify="right", anchor="e").pack(
                anchor="e", padx=30, pady=(0, 10))

        # دکمه‌های admin
        if self.is_admin:
            btn_row = tk.Frame(p, bg=C.COLOR_BG)
            btn_row.pack(fill="x", pady=10, padx=30)

            tk.Label(btn_row, text="یادداشت مدیر:",
                     font=C.FONT_BODY, bg=C.COLOR_BG,
                     fg=C.COLOR_TEXT).pack(side="right", padx=(0, 5))
            self.note_var = StringVar(value=r["admin_note"] or "")
            ttk.Entry(btn_row, textvariable=self.note_var,
                       width=30).pack(side="right", padx=(0, 10))

        # دکمه‌های پایین
        btns = tk.Frame(p, bg=C.COLOR_BG)
        btns.pack(fill="x", pady=15, padx=30)

        if self.is_admin:
            ttk.Button(btns, text="✅ تأیید",
                       command=lambda: self._change("approved")).pack(
                side="right", padx=3, ipadx=15)
            ttk.Button(btns, text="📤 ارسال به مشتری",
                       command=lambda: self._change("sent")).pack(
                side="right", padx=3, ipadx=15)
            ttk.Button(btns, text="❌ رد",
                       command=lambda: self._change("rejected")).pack(
                side="right", padx=3, ipadx=15)

        ttk.Button(btns, text="بستن",
                   command=self.win.destroy).pack(side="left", padx=3,
                                                    ipadx=20)

    def _change(self, status):
        try:
            from electrocalc.auth import users as um
            note = getattr(self, "note_var", StringVar()).get()
            user = um.get_user("admin")
            mr_module.update_status(
                self.request_id, status,
                admin_note=note,
                approved_by="admin",
            )
            messagebox.showinfo("موفق", "وضعیت تغییر کرد.")
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e))