"""تب کاربران — فقط admin."""

import tkinter as tk
from tkinter import ttk, messagebox

from electrocalc.auth import users as users_module
from electrocalc.auth import permissions as perms_module
from electrocalc.config import constants as C
from electrocalc.ui.scrollable_frame import ScrollableFrame
from electrocalc.ui.change_password_dialog import ChangePasswordDialog
from electrocalc.ui.permissions_dialog import PermissionsDialog


class UsersTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()
        self.refresh()

    def build_ui(self):
        parent = self.inner

        ttk.Label(parent, text="👥  مدیریت کاربران", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(parent, text="ساخت، مجوز، فعال/غیرفعال، تایمر",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", pady=(0, 15))
        ttk.Button(btn_frame, text="+ کاربر جدید",
                   command=self._new_user).pack(side="left")
        ttk.Button(btn_frame, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🔐 مجوزها",
                   command=self._edit_permissions).pack(side="left")
        ttk.Button(btn_frame, text="⏱ تایمر",
                   command=self._toggle_timer).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🔑 تغییر رمز",
                   command=self._change_password).pack(side="left")
        ttk.Button(btn_frame, text="🔒 فعال/غیرفعال",
                   command=self._toggle_active).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🗑 حذف",
                   command=self._delete_user).pack(side="left")

        cols = ("id", "username", "full_name", "role", "active", "timer")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="نام کاربری")
        self.tree.heading("full_name", text="نام کامل")
        self.tree.heading("role", text="نقش")
        self.tree.heading("active", text="وضعیت")
        self.tree.heading("timer", text="⏱ تایمر")
        self.tree.column("id", width=45, anchor="center")
        self.tree.column("username", width=120)
        self.tree.column("full_name", width=160)
        self.tree.column("role", width=90, anchor="center")
        self.tree.column("active", width=90, anchor="center")
        self.tree.column("timer", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        from electrocalc.data.database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ORDER BY id")
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            role_fa = {"admin": "مدیر", "engineer": "مهندس",
                       "viewer": "ناظر"}.get(row["role"], row["role"])
            active_fa = "✅ فعال" if row["active"] else "🔒 غیرفعال"
            has_timer = perms_module.has_permission(row, "use_auto_timer")
            timer_fa = "✅ دارد" if has_timer else "❌ ندارد"
            self.tree.insert("", "end", values=(
                row["id"], row["username"], row["full_name"] or "-",
                role_fa, active_fa, timer_fa))

    def _selected_username(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("هشدار", "اول یک کاربر را انتخاب کنید.")
            return None
        return self.tree.item(sel[0], "values")[1]

    def _new_user(self):
        NewUserDialog(self.winfo_toplevel(), on_done=self.refresh)

    def _edit_permissions(self):
        username = self._selected_username()
        if not username:
            return
        user_row = users_module.get_user(username)
        if not user_row:
            return
        dlg = PermissionsDialog(self.winfo_toplevel(), username, user_row,
                                 on_done=self.refresh)
        self.wait_window(dlg.win)

    def _toggle_timer(self):
        username = self._selected_username()
        if not username:
            return
        if username == "admin":
            messagebox.showerror("خطا", "admin همیشه بدون تایمر است.")
            return

        user = users_module.get_user(username)
        if not user:
            return

        current = perms_module.get_user_permissions(user)
        if "use_auto_timer" in current:
            new_list = [p for p in current if p != "use_auto_timer"]
            action = "غیرفعال"
        else:
            new_list = current + ["use_auto_timer"]
            action = "فعال"

        try:
            perms_module.set_permissions(username, new_list)
            messagebox.showinfo("موفق", f"تایمر برای «{username}» {action} شد.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _change_password(self):
        username = self._selected_username()
        if not username:
            return
        dlg = ChangePasswordDialog(self.winfo_toplevel(),
                                    target_username=username, need_old=False)
        self.wait_window(dlg.win)

    def _toggle_active(self):
        username = self._selected_username()
        if not username:
            return
        if username == "admin":
            messagebox.showerror("خطا", "کاربر admin را نمی‌توان غیرفعال کرد.")
            return
        try:
            new_state = users_module.toggle_active(username)
            msg = "کاربر فعال شد." if new_state else "کاربر غیرفعال شد."
            messagebox.showinfo("موفق", msg)
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _delete_user(self):
        username = self._selected_username()
        if not username:
            return
        if username == "admin":
            messagebox.showerror("خطا", "کاربر admin را نمی‌توان حذف کرد.")
            return
        if not messagebox.askyesno("تأیید", f"کاربر «{username}» حذف شود؟"):
            return
        from electrocalc.data.database import get_connection
        conn = get_connection()
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        self.refresh()


class NewUserDialog:
    def __init__(self, parent, on_done=None):
        self.on_done = on_done
        self.win = tk.Toplevel(parent)
        self.win.title("کاربر جدید")
        self.win.geometry("420x520")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._build_ui()

    def _build_ui(self):
        tk.Label(self.win, text="➕ کاربر جدید", font=C.FONT_TITLE,
                 bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG).pack(pady=(20, 15))
        f = tk.Frame(self.win, bg=C.COLOR_BG)
        f.pack(padx=30, fill="x")

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.fullname_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.role_var = tk.StringVar(value="engineer")
        self.timer_var = tk.BooleanVar(value=True)

        rows = [
            ("نام کاربری:", self.username_var, "entry"),
            ("رمز عبور:", self.password_var, "pass"),
            ("نام کامل:", self.fullname_var, "entry"),
            ("تلفن:", self.phone_var, "entry"),
        ]
        for i, (label, var, kind) in enumerate(rows):
            tk.Label(f, text=label, font=C.FONT_BODY, bg=C.COLOR_BG).grid(
                row=i, column=0, sticky="w", pady=8)
            show = "●" if kind == "pass" else ""
            ttk.Entry(f, textvariable=var, width=20, show=show).grid(
                row=i, column=1, pady=8, sticky="ew")

        tk.Label(f, text="نقش:", font=C.FONT_BODY, bg=C.COLOR_BG).grid(
            row=4, column=0, sticky="w", pady=8)
        role_frame = tk.Frame(f, bg=C.COLOR_BG)
        role_frame.grid(row=4, column=1, sticky="ew", pady=8)
        for val, txt in [("engineer", "مهندس"), ("viewer", "ناظر"),
                          ("admin", "مدیر")]:
            ttk.Radiobutton(role_frame, text=txt, value=val,
                            variable=self.role_var).pack(side="left", padx=5)

        tk.Checkbutton(f, text="⏱  استفاده از تایمر خودکار",
                       variable=self.timer_var,
                       bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                       activebackground=C.COLOR_BG,
                       font=C.FONT_BODY, anchor="e").grid(
            row=5, column=0, columnspan=2, sticky="e", pady=10)

        f.columnconfigure(1, weight=1)

        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=20)
        ttk.Button(btns, text="ذخیره", command=self._save).pack(
            side="left", padx=5, ipadx=15, ipady=3)
        ttk.Button(btns, text="انصراف", command=self.win.destroy).pack(
            side="left", padx=5, ipadx=15, ipady=3)

    def _save(self):
        try:
            un = self.username_var.get().strip()
            pw = self.password_var.get()
            if not un or not pw:
                messagebox.showerror("خطا", "نام کاربری و رمز الزامی است.",
                                     parent=self.win)
                return
            if len(pw) < 6:
                messagebox.showerror("خطا", "رمز باید حداقل ۶ کاراکتر باشد.",
                                     parent=self.win)
                return

            users_module.create_user(
                username=un, password=pw,
                full_name=self.fullname_var.get().strip(),
                role=self.role_var.get(),
                phone=self.phone_var.get().strip())

            if self.timer_var.get():
                perms_module.set_permissions(un, ["use_auto_timer"])

            messagebox.showinfo("موفق", "کاربر ساخته شد.", parent=self.win)
            self.win.destroy()
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)