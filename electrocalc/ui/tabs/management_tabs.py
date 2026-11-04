"""همه تب‌های مدیریتی در یک فایل."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, filedialog
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import management as mgmt
from electrocalc.core import projects as proj
from electrocalc.ui.scrollable_frame import ScrollableFrame


STATUS_FA = {"pending": "در انتظار", "approved": "تأیید شده",
             "rejected": "رد شده"}


def _read_float(text, name="مقدار"):
    t = str(text).strip()
    if not t:
        raise ValueError(f"«{name}» را وارد کن.")
    try:
        return float(t.replace(",", ""))
    except ValueError:
        raise ValueError(f"«{name}» باید عدد باشد.")


def _projects_map():
    """لیست پروژه‌ها برای combobox."""
    out = {}
    for p in proj.list_projects():
        out[f"{p['id']} - {p['name']}"] = p["id"]
    return out


# ==================== تب ساعات کار ====================
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
        ttk.Label(parent, text="ثبت ورود/خروج و ساعت کار پروژه",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 15))
        ttk.Button(bar, text="+ ثبت ساعت", command=self._new).pack(side="left")
        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=8)
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")

        cols = ("id", "project", "date", "start", "end", "hours", "status")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for k, t, w in [("id", "ID", 45), ("project", "پروژه", 140),
                        ("date", "تاریخ", 100), ("start", "ورود", 70),
                        ("end", "خروج", 70), ("hours", "ساعت", 60),
                        ("status", "وضعیت", 100)]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor="center" if k != "project" else "w")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        username = None
        if not self._is_admin() and self.app.current_user:
            username = self.app.current_user["username"]
        for t in mgmt.list_timesheets(username=username):
            self.tree.insert("", "end", values=(
                t["id"], t["project_name"] or "-", t["work_date"] or "-",
                t["start_time"] or "-", t["end_time"] or "-",
                f"{t['hours']:.1f}", STATUS_FA.get(t["status"], t["status"])))

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
        SimpleFormDialog(
            self.winfo_toplevel(),
            title="ثبت ساعت کار",
            fields=[
                ("project", "پروژه", "combo"),
                ("work_date", "تاریخ", "date"),
                ("start_time", "ساعت ورود (HH:MM)", "text"),
                ("end_time", "ساعت خروج (HH:MM)", "text"),
                ("hours", "مجموع ساعت", "text"),
                ("description", "توضیحات", "memo"),
            ],
            defaults={"work_date": datetime.now().strftime("%Y-%m-%d"),
                      "hours": "8"},
            on_save=self._save_new)

    def _save_new(self, data):
        username = self.app.current_user["username"] if self.app.current_user else "?"
        mgmt.create_timesheet(
            username=username,
            project_id=data.get("project"),
            work_date=data.get("work_date", ""),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            hours=_read_float(data.get("hours", "0"), "ساعت"),
            description=data.get("description", ""))
        self.refresh()

    def _delete(self):
        tid = self._selected_id()
        if not tid:
            return
        if not messagebox.askyesno("تأیید", "حذف شود؟"):
            return
        mgmt.delete_timesheet(tid)
        self.refresh()


# ==================== تب مصالح ====================
class MaterialsTab(ScrollableFrame):
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
        ttk.Label(parent, text="🔧  مصالح", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="لیست مصالح مصرفی هر پروژه",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 15))
        ttk.Button(bar, text="+ مصالح جدید", command=self._new).pack(side="left")
        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=8)
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")

        cols = ("id", "project", "name", "qty", "unit", "total", "status")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for k, t, w in [("id", "ID", 45), ("project", "پروژه", 130),
                        ("name", "نام", 180), ("qty", "تعداد", 70),
                        ("unit", "واحد", 60), ("total", "مبلغ", 100),
                        ("status", "وضعیت", 100)]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor="center" if k != "name" and k != "project" else "w")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        u = None
        if not self._is_admin() and self.app.current_user:
            u = self.app.current_user["username"]
        for m in mgmt.list_materials(created_by=u):
            self.tree.insert("", "end", values=(
                m["id"], m["project_name"] or "-", m["name"],
                f"{m['quantity']:.2f}", m["unit"] or "-",
                f"{m['total_price']:,.0f}",
                STATUS_FA.get(m["status"], m["status"])))

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
        SimpleFormDialog(
            self.winfo_toplevel(),
            title="مصالح جدید",
            fields=[
                ("project", "پروژه", "combo"),
                ("name", "نام مصالح", "text"),
                ("quantity", "تعداد", "text"),
                ("unit", "واحد", "text"),
                ("unit_price", "قیمت واحد", "text"),
                ("material_date", "تاریخ", "date"),
                ("description", "توضیحات", "memo"),
            ],
            defaults={"material_date": datetime.now().strftime("%Y-%m-%d"),
                      "quantity": "1", "unit_price": "0"},
            on_save=self._save_new)

    def _save_new(self, data):
        u = self.app.current_user["username"] if self.app.current_user else "?"
        mgmt.create_material(
            project_id=data.get("project"),
            name=data.get("name", "").strip() or "?",
            quantity=_read_float(data.get("quantity", "0"), "تعداد"),
            unit=data.get("unit", ""),
            unit_price=_read_float(data.get("unit_price", "0"), "قیمت"),
            description=data.get("description", ""),
            created_by=u,
            material_date=data.get("material_date", ""))
        self.refresh()

    def _delete(self):
        mid = self._selected_id()
        if not mid:
            return
        if not messagebox.askyesno("تأیید", "حذف شود؟"):
            return
        mgmt.delete_material(mid)
        self.refresh()


# ==================== تب هزینه‌ها ====================
class ExpensesTab(ScrollableFrame):
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
        ttk.Label(parent, text="💰  هزینه‌ها", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="ثبت و مدیریت هزینه‌های پروژه",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 15))
        ttk.Button(bar, text="+ هزینه جدید", command=self._new).pack(side="left")
        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=8)
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")

        cols = ("id", "project", "title", "amount", "category", "date", "status")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for k, t, w in [("id", "ID", 45), ("project", "پروژه", 130),
                        ("title", "عنوان", 180), ("amount", "مبلغ", 100),
                        ("category", "دسته", 100), ("date", "تاریخ", 100),
                        ("status", "وضعیت", 100)]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor="center" if k != "title" and k != "project" else "w")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        u = None
        if not self._is_admin() and self.app.current_user:
            u = self.app.current_user["username"]
        for e in mgmt.list_expenses(created_by=u):
            self.tree.insert("", "end", values=(
                e["id"], e["project_name"] or "-", e["title"],
                f"{e['amount']:,.0f}", e["category"] or "-",
                e["expense_date"] or "-",
                STATUS_FA.get(e["status"], e["status"])))

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
        SimpleFormDialog(
            self.winfo_toplevel(),
            title="هزینه جدید",
            fields=[
                ("project", "پروژه", "combo"),
                ("title", "عنوان", "text"),
                ("amount", "مبلغ", "text"),
                ("category", "دسته", "text"),
                ("expense_date", "تاریخ", "date"),
                ("description", "توضیحات", "memo"),
            ],
            defaults={"expense_date": datetime.now().strftime("%Y-%m-%d"),
                      "amount": "0"},
            on_save=self._save_new)

    def _save_new(self, data):
        u = self.app.current_user["username"] if self.app.current_user else "?"
        mgmt.create_expense(
            project_id=data.get("project"),
            title=data.get("title", "").strip() or "?",
            amount=_read_float(data.get("amount", "0"), "مبلغ"),
            category=data.get("category", ""),
            description=data.get("description", ""),
            created_by=u,
            expense_date=data.get("expense_date", ""))
        self.refresh()

    def _delete(self):
        eid = self._selected_id()
        if not eid:
            return
        if not messagebox.askyesno("تأیید", "حذف شود؟"):
            return
        mgmt.delete_expense(eid)
        self.refresh()


# ==================== تب فایل‌ها ====================
class FilesTab(ScrollableFrame):
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
        ttk.Label(parent, text="📎  فایل‌ها", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="آپلود و مدیریت عکس/PDF/نقشه",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 15))
        ttk.Button(bar, text="+ آپلود فایل", command=self._upload).pack(side="left")
        ttk.Button(bar, text="👁 باز کردن",
                   command=self._open).pack(side="left", padx=8)
        if self._is_admin():
            ttk.Button(bar, text="🗑 حذف",
                       command=self._delete).pack(side="left")
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=8)

        cols = ("id", "project", "title", "uploaded_by", "uploaded_at")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for k, t, w in [("id", "ID", 45), ("project", "پروژه", 140),
                        ("title", "عنوان", 220), ("uploaded_by", "آپلودکننده", 120),
                        ("uploaded_at", "تاریخ", 140)]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor="center" if k != "title" and k != "project" else "w")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        u = None
        if not self._is_admin() and self.app.current_user:
            u = self.app.current_user["username"]
        for f in mgmt.list_files(uploaded_by=u):
            self.tree.insert("", "end", values=(
                f["id"], f["project_name"] or "-", f["title"],
                f["uploaded_by"] or "-",
                (f["uploaded_at"] or "")[:16].replace("T", " ")))

    def _selected_id(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "یک ردیف انتخاب کن.")
            return None
        return int(self.tree.item(s[0], "values")[0])

    def _upload(self):
        if not proj.list_projects():
            messagebox.showwarning("هشدار", "اول یک پروژه بساز.")
            return
        from electrocalc.core.management import list_files
        path = filedialog.askopenfilename(
            title="انتخاب فایل",
            filetypes=[("همه فایل‌ها", "*.*"),
                       ("عکس", "*.png *.jpg *.jpeg"),
                       ("PDF", "*.pdf")])
        if not path:
            return
        SimpleFormDialog(
            self.winfo_toplevel(),
            title="آپلود فایل",
            fields=[
                ("project", "پروژه", "combo"),
                ("title", "عنوان فایل", "text"),
                ("description", "توضیحات", "memo"),
            ],
            defaults={"title": path.split("/")[-1].split("\\")[-1]},
            on_save=lambda d: self._do_upload(d, path))

    def _do_upload(self, data, path):
        u = self.app.current_user["username"] if self.app.current_user else "?"
        mgmt.create_file(
            project_id=data.get("project"),
            title=data.get("title", "").strip() or "?",
            source_path=path,
            uploaded_by=u,
            description=data.get("description", ""))
        self.refresh()

    def _open(self):
        fid = self._selected_id()
        if not fid:
            return
        from electrocalc.data.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT filepath FROM files WHERE id = ?", (fid,))
        row = cur.fetchone()
        conn.close()
        if row:
            import os
            try:
                os.startfile(row["filepath"])
            except Exception as e:
                messagebox.showerror("خطا", str(e))

    def _delete(self):
        fid = self._selected_id()
        if not fid:
            return
        if not messagebox.askyesno("تأیید", "حذف شود؟"):
            return
        mgmt.delete_file(fid)
        self.refresh()


# ==================== تب پیام‌ها ====================
class MessagesTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.box_var = StringVar(value="inbox")
        self.build_ui()
        self.refresh()

    def build_ui(self):
        parent = self.inner
        ttk.Label(parent, text="💬  پیام‌ها", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="پیام بین کاربران برنامه",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 15))
        ttk.Button(bar, text="✉️ پیام جدید",
                   command=self._new).pack(side="left")
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=8)

        ttk.Label(bar, text="صندوق:",
                  font=C.FONT_BODY).pack(side="left", padx=(15, 5))
        ttk.Radiobutton(bar, text="دریافتی", value="inbox",
                        variable=self.box_var,
                        command=self.refresh).pack(side="left")
        ttk.Radiobutton(bar, text="ارسالی", value="sent",
                        variable=self.box_var,
                        command=self.refresh).pack(side="left", padx=8)

        cols = ("id", "from_to", "subject", "date", "read")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        for k, t, w in [("id", "ID", 45), ("from_to", "از / به", 150),
                        ("subject", "موضوع", 250), ("date", "تاریخ", 140),
                        ("read", "وضعیت", 100)]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor="center" if k != "subject" else "w")
        self.tree.bind("<Double-1>", lambda e: self._open())
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        if not self.app.current_user:
            return
        me = self.app.current_user["username"]
        box = self.box_var.get()
        for m in mgmt.list_messages(me, box):
            if box == "inbox":
                ft = f"از: {m['sender']}"
                read = "خوانده" if m["is_read"] else "🔵 جدید"
            else:
                ft = f"به: {m['receiver']}"
                read = "-"
            self.tree.insert("", "end", values=(
                m["id"], ft, m["subject"] or "-",
                (m["sent_at"] or "")[:16].replace("T", " "), read))

    def _selected_id(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "یک پیام انتخاب کن.")
            return None
        return int(self.tree.item(s[0], "values")[0])

    def _new(self):
        from electrocalc.data.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE active = 1 ORDER BY username")
        users_list = [r["username"] for r in cur.fetchall()]
        conn.close()
        if not users_list:
            return
        MessageDialog(self.winfo_toplevel(), users_list,
                      self.app.current_user["username"] if self.app.current_user else "?",
                      on_done=self.refresh)

    def _open(self):
        mid = self._selected_id()
        if not mid:
            return
        from electrocalc.data.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM messages WHERE id = ?", (mid,))
        row = cur.fetchone()
        conn.close()
        if row:
            mgmt.mark_message_read(mid)
            messagebox.showinfo(
                row["subject"] or "(بدون موضوع)",
                f"از: {row['sender']}\nبه: {row['receiver']}\n\n{row['body']}")
            self.refresh()


# ==================== تب تأییدها ====================
class ApprovalsTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()
        self.refresh()

    def build_ui(self):
        parent = self.inner
        ttk.Label(parent, text="✅  تأییدها", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="تأیید یا رد کردن آیتم‌های در انتظار",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        bar = ttk.Frame(parent)
        bar.pack(fill="x", pady=(0, 15))
        ttk.Button(bar, text="✅ تأیید",
                   command=self._approve).pack(side="left")
        ttk.Button(bar, text="❌ رد",
                   command=self._reject).pack(side="left", padx=8)
        ttk.Button(bar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")

        cols = ("type", "title", "who", "date", "project")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=15)
        for k, t, w in [("type", "نوع", 100), ("title", "عنوان", 220),
                        ("who", "ثبت‌کننده", 120), ("date", "تاریخ", 110),
                        ("project", "پروژه", 160)]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor="center" if k != "title" and k != "project" else "w")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._items = mgmt.list_pending_for_approval()
        for idx, it in enumerate(self._items):
            self.tree.insert("", "end", iid=str(idx), values=(
                it["type"], it["title"], it["who"] or "-",
                it["date"] or "-", it["project"] or "-"))

    def _selected_item(self):
        s = self.tree.selection()
        if not s:
            messagebox.showwarning("هشدار", "یک آیتم انتخاب کن.")
            return None
        return self._items[int(s[0])]

    def _approve(self):
        it = self._selected_item()
        if not it:
            return
        u = self.app.current_user["username"] if self.app.current_user else "admin"
        mgmt.approve_item(it["table"], it["id"], u)
        self.refresh()

    def _reject(self):
        it = self._selected_item()
        if not it:
            return
        u = self.app.current_user["username"] if self.app.current_user else "admin"
        mgmt.reject_item(it["table"], it["id"], u)
        self.refresh()


# ==================== تب آموزش ====================
class EducationTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()

    def build_ui(self):
        parent = self.inner
        ttk.Label(parent, text="🎓  آموزش", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="مطالب آموزشی و راهنماهای کاربردی",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 20))

        items = [
            ("⚡ قانون اهم",
             "رابطه بین ولتاژ، جریان و مقاومت:\n"
             "V = I × R\n"
             "• ولتاژ (V): فشار الکتریکی — واحد ولت\n"
             "• جریان (I): شدت جریان — واحد آمپر\n"
             "• مقاومت (R): مقاومت مدار — واحد اهم\n\n"
             "مثال: اگر جریان ۲ آمپر و مقاومت ۱۰ اهم باشد،\n"
             "ولتاژ = ۲ × ۱۰ = ۲۰ ولت"),
            ("💡 توان الکتریکی",
             "توان = انرژی مصرفی در واحد زمان\n\n"
             "تک‌فاز: P = V × I × cos φ\n"
             "سه‌فاز: P = √3 × V × I × cos φ\n\n"
             "• توان اکتیو (P): وات — کار مفید\n"
             "• توان ظاهری (S): ولت‌آمپر\n"
             "• توان راکتیو (Q): وار"),
            ("📉 افت ولتاژ کابل",
             "افت ولتاژ = (ضریب × ρ × L × I) / A\n\n"
             "• ρ مس = ۰.۰۱۷۵\n"
             "• ρ آلومینیوم = ۰.۰۲۸\n"
             "• ضریب تک‌فاز = ۲ (رفت و برگشت)\n"
             "• ضریب سه‌فاز = √3\n\n"
             "استاندارد: افت ولتاژ روشنایی < ۳٪ — موتور < ۵٪"),
            ("🔌 انتخاب کابل",
             "برای انتخاب سطح مقطع کابل:\n"
             "۱. جریان بار را محاسبه کن\n"
             "۲. طول کابل را در نظر بگیر\n"
             "۳. افت ولتاژ مجاز را چک کن\n"
             "۴. جریان مجاز کابل را از جدول بگیر\n\n"
             "مقاطع رایج: ۱.۵ ، ۲.۵ ، ۴ ، ۶ ، ۱۰ ، ۱۶ ، ۲۵ ، ۳۵ mm²"),
            ("⚙️ محاسبه جریان موتور",
             "جریان نامی موتور:\n"
             "I = P / (√3 × V × cos φ × η)\n\n"
             "• cos φ معمول: ۰.۸۵\n"
             "• بازده η معمول: ۰.۹\n"
             "• جریان راه‌انداز: ۶ تا ۸ برابر جریان نامی"),
            ("🔒 انتخاب فیوز",
             "فیوز = جریان مدار × ۱.۲۵\n\n"
             "سپس نزدیک‌ترین فیوز استاندارد بزرگ‌تر را انتخاب کن:\n"
             "۲، ۴، ۶، ۱۰، ۱۶، ۲۰، ۲۵، ۳۲، ۴۰، ۵۰، ۶۳ آمپر ..."),
        ]

        for title, content in items:
            card = ttk.LabelFrame(parent, text=title, padding=15)
            card.pack(fill="x", pady=8)
            tk.Label(card, text=content, font=C.FONT_BODY,
                     bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                     justify="right", anchor="e", wraplength=700).pack(
                anchor="e", fill="x")


# ==================== دیالوگ عمومی ====================
class SimpleFormDialog:
    """پنجره فرم ساده برای ثبت اطلاعات."""

    def __init__(self, parent, title, fields, defaults=None, on_save=None):
        self.on_save = on_save
        self.fields = fields
        self.defaults = defaults or {}
        self.project_map = _projects_map()
        self.vars = {}
        self.widgets = {}

        self.win = tk.Toplevel(parent)
        self.win.title(title)
        h = min(150 + len(fields) * 45, 650)
        self.win.geometry(f"480x{h}")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui(title)

    def _build_ui(self, title):
        tk.Label(self.win, text=f"➕ {title}", font=C.FONT_TITLE,
                 bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="both", expand=True)

        for i, (key, label, kind) in enumerate(self.fields):
            tk.Label(f, text=f"{label}:", font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=i, column=0, sticky="nw", pady=6)

            if kind == "combo":
                var = StringVar()
                display = list(self.project_map.keys())
                combo = ttk.Combobox(f, textvariable=var, values=display,
                                      state="readonly", width=30)
                if display:
                    combo.current(0)
                combo.grid(row=i, column=1, pady=6, sticky="ew")
                self.vars[key] = var
            elif kind == "memo":
                txt = tk.Text(f, width=30, height=4, font=C.FONT_BODY)
                txt.grid(row=i, column=1, pady=6, sticky="ew")
                self.widgets[key] = txt
            else:
                var = StringVar(value=self.defaults.get(key, ""))
                ttk.Entry(f, textvariable=var, width=30).grid(
                    row=i, column=1, pady=6, sticky="ew")
                self.vars[key] = var

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
            data = {}
            for key, label, kind in self.fields:
                if kind == "combo":
                    data[key] = self.project_map.get(self.vars[key].get())
                elif kind == "memo":
                    data[key] = self.widgets[key].get("1.0", "end").strip()
                else:
                    data[key] = self.vars[key].get()
            if self.on_save:
                self.on_save(data)
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)


# ==================== دیالوگ پیام ====================
class MessageDialog:
    def __init__(self, parent, users_list, sender, on_done=None):
        self.on_done = on_done
        self.sender = sender
        self.win = tk.Toplevel(parent)
        self.win.title("پیام جدید")
        self.win.geometry("480x500")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()

        tk.Label(self.win, text="✉️ پیام جدید", font=C.FONT_TITLE,
                 bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="both", expand=True)

        tk.Label(f, text="گیرنده:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=0, column=0, sticky="w", pady=6)
        self.to_var = StringVar()
        combo = ttk.Combobox(f, textvariable=self.to_var,
                              values=users_list, state="readonly", width=30)
        combo.grid(row=0, column=1, pady=6, sticky="ew")
        if users_list:
            combo.current(0)

        tk.Label(f, text="موضوع:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=1, column=0, sticky="w", pady=6)
        self.subject_var = StringVar()
        ttk.Entry(f, textvariable=self.subject_var, width=30).grid(
            row=1, column=1, pady=6, sticky="ew")

        tk.Label(f, text="متن:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=2, column=0, sticky="nw", pady=6)
        self.body_text = tk.Text(f, width=30, height=12, font=C.FONT_BODY)
        self.body_text.grid(row=2, column=1, pady=6, sticky="ew")

        f.columnconfigure(1, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="ارسال", command=self._send).pack(
            side="left", padx=5, ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف",
                   command=self.win.destroy).pack(
            side="left", padx=5, ipadx=20, ipady=4)

    def _send(self):
        try:
            to = self.to_var.get().strip()
            if not to:
                raise ValueError("گیرنده را انتخاب کن.")
            subj = self.subject_var.get().strip()
            body = self.body_text.get("1.0", "end").strip()
            if not body:
                raise ValueError("متن پیام خالی است.")
            mgmt.create_message(self.sender, to, subj, body)
            messagebox.showinfo("موفق", "پیام ارسال شد.", parent=self.win)
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)