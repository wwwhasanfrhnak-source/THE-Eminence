"""تب پروژه‌ها — با خروجی Excel و PDF."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, StringVar
from pathlib import Path
from datetime import datetime

from electrocalc.config import constants as C
from electrocalc.core import projects as proj
from electrocalc.ui.scrollable_frame import ScrollableFrame


class ProjectsTab(ScrollableFrame):
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

        ttk.Label(parent, text="📁  پروژه‌ها", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="ساخت، ویرایش و مدیریت پروژه‌های مشترک",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 15))

        if self._is_admin():
            ttk.Button(toolbar, text="+ پروژه جدید",
                       command=self._new).pack(side="left")
            ttk.Button(toolbar, text="✏️ ویرایش",
                       command=self._edit).pack(side="left", padx=5)
            ttk.Button(toolbar, text="👥 اعضا",
                       command=self._edit_members).pack(side="left")
            ttk.Button(toolbar, text="🗑 حذف",
                       command=self._delete).pack(side="left", padx=5)
        else:
            ttk.Button(toolbar, text="+ پروژه جدید",
                       command=self._new).pack(side="left")

        ttk.Button(toolbar, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=5)

        search_frame = ttk.Frame(parent)
        search_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(search_frame, text="🔍 جستجو:",
                  font=C.FONT_BODY).pack(side="left", padx=(0, 8))
        self.search_var = StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        entry.pack(side="left")
        entry.bind("<KeyRelease>", lambda e: self.refresh())

        cols = ("id", "name", "customer", "status", "start_date", "members")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=13)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="نام پروژه")
        self.tree.heading("customer", text="مشتری")
        self.tree.heading("status", text="وضعیت")
        self.tree.heading("start_date", text="شروع")
        self.tree.heading("members", text="👥 اعضا")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("name", width=220)
        self.tree.column("customer", width=160)
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("start_date", width=100, anchor="center")
        self.tree.column("members", width=80, anchor="center")

        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        search = self.search_var.get().strip()

        if self._is_admin():
            projects = proj.list_projects(search)
        else:
            username = (self.app.current_user["username"]
                        if self.app.current_user else "")
            projects = proj.list_projects_for_user(username, search)

        for p in projects:
            status_fa = proj.STATUS_FA.get(p["status"], p["status"])
            m = proj.count_members(p["id"])
            self.tree.insert("", "end", values=(
                p["id"], p["name"], p["customer"] or "-",
                status_fa, p["start_date"] or "-", f"{m} نفر"))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("هشدار", "اول یک پروژه انتخاب کنید.")
            return None
        return int(self.tree.item(sel[0], "values")[0])

    def _new(self):
        ProjectDialog(self.winfo_toplevel(), on_done=self.refresh,
                      created_by=(self.app.current_user["username"]
                                  if self.app.current_user else ""))

    def _edit(self):
        pid = self._selected_id()
        if not pid:
            return
        ProjectDialog(self.winfo_toplevel(), on_done=self.refresh, project_id=pid)

    def _edit_members(self):
        pid = self._selected_id()
        if not pid:
            return
        MembersDialog(self.winfo_toplevel(), pid, on_done=self.refresh)

    def _delete(self):
        pid = self._selected_id()
        if not pid:
            return
        if not messagebox.askyesno("تأیید", "این پروژه و همه اعضاش حذف شوند؟"):
            return
        proj.delete_project(pid)
        self.refresh()

    # ⭐ متدهای خروجی — برای وقتی که از هدر فراخوانی می‌شن
    def export_excel(self):
        try:
            headers = ["نام پروژه", "مشتری", "وضعیت", "شروع", "اعضا"]
            rows = []
            for item in self.tree.get_children():
                vals = self.tree.item(item, "values")
                rows.append((vals[1], vals[2], vals[3], vals[4], vals[5]))

            if not rows:
                messagebox.showwarning("هشدار", "چیزی برای خروجی نیست.")
                return

            from electrocalc.core import export
            path = export.export_to_excel(
                headers, rows, title="پروژه‌ها",
            )
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(str(Path(path).parent))
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def export_pdf(self):
        try:
            headers = ["نام پروژه", "مشتری", "وضعیت", "شروع", "اعضا"]
            rows = []
            for item in self.tree.get_children():
                vals = self.tree.item(item, "values")
                rows.append((vals[1], vals[2], vals[3], vals[4], vals[5]))

            if not rows:
                messagebox.showwarning("هشدار", "چیزی برای خروجی نیست.")
                return

            from electrocalc.core import export
            path = export.export_to_pdf(
                headers, rows, title="پروژه‌ها",
            )
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(str(path))
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("خطا", str(e))


# ========================================================
class ProjectDialog:
    def __init__(self, parent, on_done=None, project_id=None, created_by=""):
        self.on_done = on_done
        self.project_id = project_id
        self.created_by = created_by
        self.member_usernames = []

        self.win = tk.Toplevel(parent)
        self.win.title("پروژه جدید" if not project_id else "ویرایش پروژه")
        self.win.geometry("520x700")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui()
        if project_id:
            self._load()

    def _build_ui(self):
        tk.Label(self.win,
                 text="➕ پروژه جدید" if not self.project_id else "✏️ ویرایش پروژه",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))

        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="both", expand=True)

        self.name_var = StringVar()
        self.customer_var = StringVar()
        self.address_var = StringVar()
        self.status_var = StringVar(value="در حال انجام")
        self.start_var = StringVar()
        self.end_var = StringVar()

        tk.Label(f, text="نام پروژه *:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(f, textvariable=self.name_var, width=30).grid(
            row=0, column=1, pady=5, sticky="ew")

        tk.Label(f, text="مشتری:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(f, textvariable=self.customer_var, width=30).grid(
            row=1, column=1, pady=5, sticky="ew")

        tk.Label(f, text="آدرس:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(f, textvariable=self.address_var, width=30).grid(
            row=2, column=1, pady=5, sticky="ew")

        date_row = tk.Frame(f, bg=C.COLOR_BG)
        date_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        tk.Label(date_row, text="شروع:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).pack(side="right", padx=(0, 5))
        ttk.Entry(date_row, textvariable=self.start_var, width=12).pack(
            side="right", padx=(0, 15))
        tk.Label(date_row, text="پایان:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).pack(side="right", padx=(0, 5))
        ttk.Entry(date_row, textvariable=self.end_var, width=12).pack(
            side="right")

        tk.Label(f, text="وضعیت:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=4, column=0, sticky="w", pady=5)
        status_combo = ttk.Combobox(f, textvariable=self.status_var,
                                     state="readonly", width=28)
        status_combo["values"] = list(proj.STATUS_FA.values())
        status_combo.current(1)
        status_combo.grid(row=4, column=1, pady=5, sticky="ew")

        tk.Label(f, text="توضیحات:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=5, column=0, sticky="nw", pady=5)
        self.desc_text = tk.Text(f, width=30, height=4, font=C.FONT_BODY)
        self.desc_text.grid(row=5, column=1, pady=5, sticky="ew")

        tk.Label(f, text="👥 اعضای پروژه:", font=C.FONT_HEADER,
                 bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(15, 5))

        tk.Label(f, text="(با Ctrl چند نفر را انتخاب کن)",
                 font=C.FONT_SMALL, bg=C.COLOR_BG,
                 fg=C.COLOR_MUTED).grid(row=7, column=0, columnspan=2,
                                         sticky="w", pady=(0, 5))

        member_frame = tk.Frame(f, bg=C.COLOR_BG)
        member_frame.grid(row=8, column=0, columnspan=2, sticky="nsew",
                          pady=5)

        self.members_listbox = tk.Listbox(
            member_frame, selectmode=tk.MULTIPLE, height=6,
            font=C.FONT_BODY, activestyle="none")
        sb = ttk.Scrollbar(member_frame, orient="vertical",
                            command=self.members_listbox.yview)
        self.members_listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.members_listbox.pack(side="right", fill="both", expand=True)

        self._load_users()

        f.columnconfigure(1, weight=1)
        f.rowconfigure(8, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=15)
        ttk.Button(btns, text="ذخیره", command=self._save).pack(
            side="left", padx=5, ipadx=20, ipady=4)
        ttk.Button(btns, text="انصراف", command=self.win.destroy).pack(
            side="left", padx=5, ipadx=20, ipady=4)

    def _load_users(self):
        self.members_listbox.delete(0, tk.END)
        self.member_usernames = []
        for u in proj.get_active_users():
            display = f"{u['full_name'] or u['username']}  ({u['username']})"
            role_fa = {"admin": "مدیر", "engineer": "مهندس",
                       "viewer": "ناظر"}.get(u["role"], u["role"])
            display += f"  —  {role_fa}"
            self.members_listbox.insert(tk.END, display)
            self.member_usernames.append(u["username"])

    def _load(self):
        p = proj.get_project(self.project_id)
        if not p:
            return
        self.name_var.set(p["name"])
        self.customer_var.set(p["customer"] or "")
        self.address_var.set(p["address"] or "")
        self.start_var.set(p["start_date"] or "")
        self.end_var.set(p["end_date"] or "")
        self.desc_text.insert("1.0", p["description"] or "")

        status_fa = proj.STATUS_FA.get(p["status"], "در حال انجام")
        self.status_var.set(status_fa)

        current_members = set(proj.get_members(self.project_id))
        for i, un in enumerate(self.member_usernames):
            if un in current_members:
                self.members_listbox.selection_set(i)

    def _save(self):
        try:
            status_key = "in_progress"
            status_fa_val = self.status_var.get()
            for k, v in proj.STATUS_FA.items():
                if v == status_fa_val:
                    status_key = k
                    break

            desc = self.desc_text.get("1.0", "end").strip()
            selected_idx = self.members_listbox.curselection()
            selected_usernames = [self.member_usernames[i] for i in selected_idx]

            if self.project_id:
                proj.update_project(
                    self.project_id, self.name_var.get(),
                    self.customer_var.get(), self.address_var.get(),
                    desc, status_key,
                    self.start_var.get(), self.end_var.get(),
                )
                proj.set_members(self.project_id, selected_usernames)
            else:
                pid = proj.create_project(
                    self.name_var.get(), self.customer_var.get(),
                    self.address_var.get(), desc, status_key,
                    self.start_var.get(), self.end_var.get(),
                    self.created_by,
                )
                proj.set_members(pid, selected_usernames)

            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)


# ========================================================
class MembersDialog:
    def __init__(self, parent, project_id, on_done=None):
        self.project_id = project_id
        self.on_done = on_done
        self.member_usernames = []

        p = proj.get_project(project_id)
        if not p:
            messagebox.showerror("خطا", "پروژه پیدا نشد.")
            return

        self.win = tk.Toplevel(parent)
        self.win.title(f"اعضای پروژه: {p['name']}")
        self.win.geometry("460x520")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui(p)

    def _build_ui(self, project):
        tk.Label(self.win, text="👥  اعضای پروژه",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 5))
        tk.Label(self.win, text=project["name"],
                 font=C.FONT_BODY, bg=C.COLOR_BG,
                 fg=C.COLOR_MUTED).pack(pady=(0, 15))

        tk.Label(self.win, text="با Ctrl چند نفر را انتخاب کن",
                 font=C.FONT_SMALL, bg=C.COLOR_BG,
                 fg=C.COLOR_MUTED).pack(pady=(0, 8))

        frame = tk.Frame(self.win, bg=C.COLOR_BG)
        frame.pack(fill="both", expand=True, padx=30)

        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=15,
                                   font=C.FONT_BODY, activestyle="none")
        sb = ttk.Scrollbar(frame, orient="vertical",
                            command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.listbox.pack(side="right", fill="both", expand=True)

        for u in proj.get_active_users():
            display = f"{u['full_name'] or u['username']}  ({u['username']})"
            self.listbox.insert(tk.END, display)
            self.member_usernames.append(u["username"])

        current = set(proj.get_members(self.project_id))
        for i, un in enumerate(self.member_usernames):
            if un in current:
                self.listbox.selection_set(i)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=15)
        ttk.Button(btns, text="💾 ذخیره", command=self._save).pack(
            side="left", padx=5, ipadx=20, ipady=4)
        ttk.Button(btns, text="✅ همه", command=self._select_all).pack(
            side="left", padx=5, ipadx=15, ipady=4)
        ttk.Button(btns, text="❌ هیچ‌کدام", command=self._clear_all).pack(
            side="left", padx=5, ipadx=15, ipady=4)
        ttk.Button(btns, text="انصراف", command=self.win.destroy).pack(
            side="left", padx=5, ipadx=20, ipady=4)

    def _select_all(self):
        self.listbox.selection_set(0, tk.END)

    def _clear_all(self):
        self.listbox.selection_clear(0, tk.END)

    def _save(self):
        try:
            selected = [self.member_usernames[i]
                        for i in self.listbox.curselection()]
            proj.set_members(self.project_id, selected)
            messagebox.showinfo("موفق", "اعضا ذخیره شد.", parent=self.win)
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)