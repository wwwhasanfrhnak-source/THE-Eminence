"""تب تسک‌لیست پروژه."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import tasks as tasks_module
from electrocalc.core import projects as proj
from electrocalc.ui.scrollable_frame import ScrollableFrame


class TasksTab(ScrollableFrame):
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

        ttk.Label(p, text="✅  تسک‌لیست پروژه‌ها",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p, text="مدیریت کارهای کوچیک هر پروژه با درصد پیشرفت",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # ===== دکمه‌ها =====
        bar = ttk.Frame(p)
        bar.pack(fill="x", pady=(0, 12))

        ttk.Button(bar, text="+ تسک جدید",
                   command=self._new).pack(side="left")
        ttk.Button(bar, text="✏️ ویرایش",
                   command=self._edit).pack(side="left", padx=8)
        ttk.Button(bar, text="✅ تغییر وضعیت (انجام شد/نشد)",
                   command=self._toggle).pack(side="left")
        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=8)
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")

        # ===== فیلترها =====
        filters = ttk.LabelFrame(p, text="🔍 فیلتر", padding=10)
        filters.pack(fill="x", pady=(0, 12))

        # پروژه
        ttk.Label(filters, text="پروژه:",
                  font=C.FONT_BODY).pack(side="right", padx=(0, 5))
        self.filter_project = StringVar(value="همه")
        self.project_combo = ttk.Combobox(
            filters, textvariable=self.filter_project,
            state="readonly", width=25,
        )
        self.project_combo.pack(side="right", padx=(0, 15))
        self.project_combo.bind("<<ComboboxSelected>>",
                                  lambda e: self.refresh())

        # کاربر
        if self._is_admin():
            ttk.Label(filters, text="کاربر:",
                      font=C.FONT_BODY).pack(side="right", padx=(0, 5))
            self.filter_user = StringVar(value="همه")
            self.user_combo = ttk.Combobox(
                filters, textvariable=self.filter_user,
                state="readonly", width=15,
            )
            self.user_combo.pack(side="right", padx=(0, 15))
            self.user_combo.bind("<<ComboboxSelected>>",
                                   lambda e: self.refresh())
        else:
            self.filter_user = None

        # وضعیت
        ttk.Label(filters, text="وضعیت:",
                  font=C.FONT_BODY).pack(side="right", padx=(0, 5))
        self.filter_status = StringVar(value="همه")
        status_combo = ttk.Combobox(
            filters, textvariable=self.filter_status,
            values=["همه", "در انتظار", "در حال انجام",
                    "انجام شده", "لغو شده"],
            state="readonly", width=15,
        )
        status_combo.pack(side="right")
        status_combo.bind("<<ComboboxSelected>>",
                            lambda e: self.refresh())

        # ===== خلاصه =====
        self.summary_var = StringVar(value="")
        ttk.Label(p, textvariable=self.summary_var,
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_SUCCESS).pack(anchor="w", pady=(0, 10))

        # ===== جدول =====
        cols = ("check", "id", "title", "project", "user",
                "priority", "due", "status")
        self.tree = ttk.Treeview(p, columns=cols, show="headings", height=15)

        headers = {
            "check": "✓", "id": "ID", "title": "عنوان",
            "project": "پروژه", "user": "مسئول",
            "priority": "اولویت", "due": "مهلت", "status": "وضعیت",
        }
        widths = {
            "check": 40, "id": 40, "title": 250, "project": 130,
            "user": 90, "priority": 90, "due": 90, "status": 100,
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                              anchor="w" if c in ("title", "project")
                              else "center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._toggle())

    def refresh(self):
        # پروژه‌ها
        if self._is_admin():
            projects = proj.list_projects()
        else:
            user = (self.app.current_user["username"]
                    if self.app.current_user else "")
            projects = proj.list_projects_for_user(user)

        proj_display = ["همه"] + [f"{p['id']} - {p['name']}" for p in projects]
        self.project_combo["values"] = proj_display

        # کاربران
        if self._is_admin():
            users = ["همه"] + [u["username"]
                                for u in tasks_module.get_active_users()]
            self.user_combo["values"] = users

        # فیلترها
        proj_filter = None
        if self.filter_project.get() != "همه":
            try:
                proj_filter = int(self.filter_project.get().split(" - ")[0])
            except Exception:
                pass

        user_filter = None
        if not self._is_admin() and self.app.current_user:
            user_filter = self.app.current_user["username"]
        elif self.filter_user and self.filter_user.get() != "همه":
            user_filter = self.filter_user.get()

        status_filter = None
        status_map = {"در انتظار": "pending",
                       "در حال انجام": "in_progress",
                       "انجام شده": "done", "لغو شده": "cancelled"}
        if self.filter_status.get() in status_map:
            status_filter = status_map[self.filter_status.get()]

        # پاک کردن جدول
        for i in self.tree.get_children():
            self.tree.delete(i)

        rows = tasks_module.list_tasks(
            project_id=proj_filter,
            assigned_to=user_filter,
            status=status_filter,
        )

        done_count = 0
        for t in rows:
            if t["status"] == "done":
                done_count += 1

            check = "☑" if t["status"] == "done" else "☐"
            prio_fa = tasks_module.PRIORITY_FA.get(t["priority"],
                                                     t["priority"])
            status_fa = tasks_module.STATUS_FA.get(t["status"], t["status"])

            self.tree.insert("", "end", iid=str(t["id"]),
                              values=(check, t["id"], t["title"],
                                       t["project_name"] or "-",
                                       t["assigned_to"] or "-",
                                       prio_fa,
                                       t["due_date"] or "-",
                                       status_fa))

        # رنگ‌بندی
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            if vals[7] == "انجام شده":
                self.tree.item(iid, tags=("done",))
        self.tree.tag_configure("done",
                                  foreground=C.COLOR_MUTED)

        self.summary_var.set(
            f"📊  مجموع: {len(rows)} تسک   |   انجام‌شده: {done_count}   "
            f"|   باقی‌مانده: {len(rows) - done_count}")

    def _selected_id(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "اول یک تسک انتخاب کن.")
            return None
        return int(s[0])

    def _new(self):
        projects = proj.list_projects()
        if not projects:
            messagebox.showwarning("هشدار",
                                    "اول باید حداقل یک پروژه بسازید.")
            return
        TaskDialog(self.winfo_toplevel(), on_done=self.refresh,
                    created_by=(self.app.current_user["username"]
                                if self.app.current_user else ""))

    def _edit(self):
        tid = self._selected_id()
        if not tid:
            return
        TaskDialog(self.winfo_toplevel(), on_done=self.refresh,
                    task_id=tid)

    def _toggle(self):
        tid = self._selected_id()
        if not tid:
            return
        tasks_module.toggle_task(tid)
        self.refresh()

    def _delete(self):
        tid = self._selected_id()
        if not tid:
            return
        if not messagebox.askyesno("تأیید", "این تسک حذف شود؟"):
            return
        tasks_module.delete_task(tid)
        self.refresh()


class TaskDialog:
    """پنجره ساخت/ویرایش تسک."""

    def __init__(self, parent, on_done=None, task_id=None, created_by=""):
        self.on_done = on_done
        self.task_id = task_id
        self.created_by = created_by

        self.win = tk.Toplevel(parent)
        self.win.title("تسک جدید" if not task_id else "ویرایش تسک")
        self.win.geometry("500x560")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()
        if task_id:
            self._load()

    def _build_ui(self):
        tk.Label(self.win,
                 text="➕ تسک جدید" if not self.task_id else "✏️ ویرایش تسک",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="both", expand=True)

        self.project_var = StringVar()
        self.title_var = StringVar()
        self.user_var = StringVar()
        self.priority_var = StringVar(value="متوسط")
        self.status_var = StringVar(value="در انتظار")
        self.due_var = StringVar()

        # پروژه
        tk.Label(f, text="پروژه *:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.project_map = {}
        proj_display = []
        for p in proj.list_projects():
            d = f"{p['id']} - {p['name']}"
            proj_display.append(d)
            self.project_map[d] = p["id"]
        proj_combo = ttk.Combobox(f, textvariable=self.project_var,
                                    values=proj_display,
                                    state="readonly", width=30)
        proj_combo.grid(row=0, column=1, sticky="ew", pady=6)
        if proj_display:
            proj_combo.current(0)

        # عنوان
        tk.Label(f, text="عنوان *:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(f, textvariable=self.title_var, width=30).grid(
            row=1, column=1, sticky="ew", pady=6)

        # مسئول
        tk.Label(f, text="مسئول:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=2, column=0, sticky="w", pady=6)
        users_list = ["(خالی)"] + [u["username"]
                                     for u in tasks_module.get_active_users()]
        user_combo = ttk.Combobox(f, textvariable=self.user_var,
                                    values=users_list,
                                    state="readonly", width=30)
        user_combo.grid(row=2, column=1, sticky="ew", pady=6)
        user_combo.current(0)

        # اولویت
        tk.Label(f, text="اولویت:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=3, column=0, sticky="w", pady=6)
        prio_combo = ttk.Combobox(f, textvariable=self.priority_var,
                                    values=list(tasks_module.PRIORITY_FA.values()),
                                    state="readonly", width=30)
        prio_combo.grid(row=3, column=1, sticky="ew", pady=6)
        prio_combo.current(1)

        # وضعیت (فقط ویرایش)
        if self.task_id:
            tk.Label(f, text="وضعیت:", font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=4, column=0, sticky="w", pady=6)
            status_combo = ttk.Combobox(f, textvariable=self.status_var,
                                          values=list(tasks_module.STATUS_FA.values()),
                                          state="readonly", width=30)
            status_combo.grid(row=4, column=1, sticky="ew", pady=6)
            status_combo.current(0)

        # تاریخ مهلت
        row_due = 5 if self.task_id else 4
        tk.Label(f, text="مهلت:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row_due, column=0,
                                      sticky="w", pady=6)
        ttk.Entry(f, textvariable=self.due_var, width=30).grid(
            row=row_due, column=1, sticky="ew", pady=6)
        tk.Label(f, text="مثال: 1404-08-15",
                 font=C.FONT_SMALL, bg=C.COLOR_BG,
                 fg=C.COLOR_MUTED).grid(row=row_due + 1, column=1,
                                         sticky="w")

        # توضیحات
        row_desc = row_due + 2
        tk.Label(f, text="توضیحات:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row_desc, column=0,
                                      sticky="nw", pady=6)
        self.desc_text = tk.Text(f, width=30, height=6, font=C.FONT_BODY)
        self.desc_text.grid(row=row_desc, column=1, sticky="ew", pady=6)

        f.columnconfigure(1, weight=1)

        # دکمه‌ها
        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="💾 ذخیره",
                   command=self._save).pack(side="left", padx=5,
                                             ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف",
                   command=self.win.destroy).pack(side="left", padx=5,
                                                    ipadx=20, ipady=4)

    def _load(self):
        t = tasks_module.get_task(self.task_id)
        if not t:
            return
        d = f"{t['project_id']} - {t['project_name']}"
        self.project_var.set(d)
        self.title_var.set(t["title"] or "")
        if t["assigned_to"]:
            self.user_var.set(t["assigned_to"])
        # اولویت
        for k, v in tasks_module.PRIORITY_FA.items():
            if k == t["priority"]:
                self.priority_var.set(v)
                break
        # وضعیت
        for k, v in tasks_module.STATUS_FA.items():
            if k == t["status"]:
                self.status_var.set(v)
                break
        self.due_var.set(t["due_date"] or "")
        self.desc_text.insert("1.0", t["description"] or "")

    def _save(self):
        try:
            project_id = self.project_map.get(self.project_var.get())
            if not project_id:
                raise ValueError("پروژه را انتخاب کن.")

            # اولویت
            priority = "medium"
            for k, v in tasks_module.PRIORITY_FA.items():
                if v == self.priority_var.get():
                    priority = k
                    break

            # وضعیت
            status = "pending"
            for k, v in tasks_module.STATUS_FA.items():
                if v == self.status_var.get():
                    status = k
                    break

            assigned = self.user_var.get()
            if assigned == "(خالی)":
                assigned = ""

            desc = self.desc_text.get("1.0", "end").strip()

            if self.task_id:
                tasks_module.update_task(
                    self.task_id,
                    self.title_var.get(),
                    desc, assigned, priority, status,
                    self.due_var.get(),
                )
            else:
                tasks_module.create_task(
                    project_id,
                    self.title_var.get(),
                    desc, assigned, priority,
                    self.due_var.get(),
                    self.created_by,
                )
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)