"""پنجره تنظیم مجوزهای کاربر."""

import tkinter as tk
from tkinter import ttk, messagebox

from electrocalc.auth import permissions as perms_module
from electrocalc.config import constants as C


class PermissionsDialog:
    def __init__(self, parent, username: str, user_row, on_done=None):
        self.username = username
        self.user_row = user_row
        self.on_done = on_done
        self.vars = {}

        self.win = tk.Toplevel(parent)
        self.win.title(f"مجوزهای {username}")
        self.win.geometry("500x620")
        self.win.configure(bg=C.COLOR_BG)
        self.win.transient(parent)
        self.win.grab_set()
        self._center(parent)
        self._build_ui()

    def _center(self, parent):
        self.win.update_idletasks()
        w, h = 500, 620
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
        self.win.geometry(f"{w}x{h}+{px}+{py}")

    def _build_ui(self):
        tk.Label(self.win, text="🔐  تنظیم مجوزها",
                 font=C.FONT_TITLE, bg=C.COLOR_BG,
                 fg=C.COLOR_HEADER_BG).pack(pady=(20, 5))

        full_name = self.user_row["full_name"] or self.user_row["username"]
        role_fa = {"admin": "مدیر", "engineer": "مهندس",
                   "viewer": "ناظر"}.get(self.user_row["role"], "")

        tk.Label(self.win, text=f"{full_name}  —  {role_fa}",
                 font=C.FONT_BODY, bg=C.COLOR_BG,
                 fg=C.COLOR_MUTED).pack(pady=(0, 15))

        # اگه admin هست، همه مجوزها داره
        is_admin = self.user_row["role"] == "admin"

        if is_admin:
            tk.Label(self.win,
                     text="⚠️ کاربر admin به‌طور خودکار همه مجوزها را دارد.",
                     font=C.FONT_SMALL, bg=C.COLOR_BG,
                     fg=C.COLOR_DANGER).pack(pady=(0, 10))

        # فریم قابل اسکرول
        container = tk.Frame(self.win, bg=C.COLOR_BG)
        container.pack(fill="both", expand=True, padx=20)

        canvas = tk.Canvas(container, bg=C.COLOR_BG, highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        canvas.pack(side="right", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=C.COLOR_BG)
        canvas.create_window((0, 0), window=inner, anchor="nw",
                              width=430)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        current = set(perms_module.get_user_permissions(self.user_row))

        for key, label in perms_module.PERMISSIONS.items():
            var = tk.BooleanVar(value=(key in current))
            self.vars[key] = var
            cb = tk.Checkbutton(
                inner, text=label, variable=var,
                bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                activebackground=C.COLOR_BG,
                font=C.FONT_BODY, anchor="e",
                state=("disabled" if is_admin else "normal"),
                padx=10, pady=6,
            )
            cb.pack(fill="x")

        # دکمه‌ها
        btns = tk.Frame(self.win, bg=C.COLOR_BG)
        btns.pack(pady=15)

        if not is_admin:
            ttk.Button(btns, text="💾 ذخیره",
                       command=self._save).pack(side="left", padx=5,
                                                 ipadx=20, ipady=4)
            ttk.Button(btns, text="✅ انتخاب همه",
                       command=self._select_all).pack(side="left", padx=5,
                                                        ipadx=15, ipady=4)
            ttk.Button(btns, text="❌ حذف همه",
                       command=self._clear_all).pack(side="left", padx=5,
                                                       ipadx=15, ipady=4)

        ttk.Button(btns, text="بستن",
                   command=self.win.destroy).pack(side="left", padx=5,
                                                   ipadx=20, ipady=4)

    def _select_all(self):
        for v in self.vars.values():
            v.set(True)

    def _clear_all(self):
        for v in self.vars.values():
            v.set(False)

    def _save(self):
        selected = [k for k, v in self.vars.items() if v.get()]
        try:
            perms_module.set_permissions(self.username, selected)
            messagebox.showinfo("موفق", "مجوزها ذخیره شد.", parent=self.win)
            if self.on_done:
                self.on_done()
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)