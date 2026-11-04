"""پنجره ورود با پروفایل گرد."""

import tkinter as tk
from tkinter import ttk, messagebox

from electrocalc.auth import users
from electrocalc.config import constants as C
from electrocalc.data.database import get_connection
from electrocalc.utils.avatar import get_avatar


def get_active_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE active = 1 ORDER BY username")
    rows = cur.fetchall()
    conn.close()
    return list(rows)


class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ورود به ElectroCalc")
        self.root.geometry("460x520")
        self.root.configure(bg=C.COLOR_BG)
        self.root.resizable(False, False)
        self.user = None
        self.user_list = []
        self.avatar_cache = {}
        self._center()
        self._build_ui()

    def _center(self):
        self.root.update_idletasks()
        w, h = 460, 520
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        tk.Label(
            self.root, text="⚡  THE Eminence",
            font=(C.FONT_FAMILY, 24, "bold"),
            bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG,
        ).pack(pady=(30, 3))

        tk.Label(
            self.root, text="ماشین‌حساب و مدیریت پروژه برق",
            font=C.FONT_BODY, bg=C.COLOR_BG, fg=C.COLOR_MUTED,
        ).pack(pady=(0, 15))

        # لیست کاربران با پروفایل گرد
        tk.Label(
            self.root, text="یک کاربر را انتخاب کنید:",
            font=C.FONT_BODY, bg=C.COLOR_BG, fg=C.COLOR_TEXT,
        ).pack(anchor="w", padx=50, pady=(5, 5))

        list_frame = tk.Frame(self.root, bg=C.COLOR_BG)
        list_frame.pack(fill="x", padx=50)

        self.users_container = tk.Frame(list_frame, bg=C.COLOR_BG)
        self.users_container.pack(fill="x")

        self._load_users()

        # ورودی‌ها
        form = tk.Frame(self.root, bg=C.COLOR_BG)
        form.pack(padx=50, pady=(20, 0), fill="x")

        tk.Label(form, text="نام کاربری:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=0, column=0, sticky="w", pady=8)
        self.username_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.username_var, width=22).grid(
            row=0, column=1, pady=8, sticky="ew")

        tk.Label(form, text="رمز عبور:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=1, column=0, sticky="w", pady=8)
        self.password_var = tk.StringVar()
        self.pass_entry = ttk.Entry(form, textvariable=self.password_var,
                                     width=22, show="●")
        self.pass_entry.grid(row=1, column=1, pady=8, sticky="ew")

        form.columnconfigure(1, weight=1)

        ttk.Button(self.root, text="ورود", command=self._login).pack(
            pady=20, ipadx=40, ipady=6)

        self.root.bind("<Return>", lambda e: self._login())
        self.root.protocol("WM_DELETE_WINDOW", self._cancel)

        if self.user_list:
            self._pick_user(0)

    def _load_users(self):
        """کاربران رو با پروفایل گرد نشون بده."""
        self.user_list = get_active_users()
        self.avatar_cache.clear()

        if not self.user_list:
            tk.Label(self.users_container, text="هیچ کاربری وجود ندارد",
                     font=C.FONT_SMALL, bg=C.COLOR_BG,
                     fg=C.COLOR_DANGER).pack()
            return

        for i, u in enumerate(self.user_list):
            avatar = get_avatar(u, 40)
            self.avatar_cache[f"av_{i}"] = avatar

            row = tk.Frame(self.users_container, bg=C.COLOR_BG,
                           cursor="hand2")
            row.pack(fill="x", pady=3)

            if avatar:
                lbl_img = tk.Label(row, image=avatar, bg=C.COLOR_BG)
                lbl_img.image = avatar
                lbl_img.pack(side="right", padx=(0, 10))

            name = u["full_name"] or u["username"]
            lbl = tk.Label(row, text=name, font=C.FONT_BODY,
                           bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                           anchor="e", padx=10)
            lbl.pack(side="right", fill="x", expand=True)

            for w in (row, lbl):
                w.bind("<Button-1>", lambda e, idx=i: self._pick_user(idx))

    def _pick_user(self, idx):
        if idx < 0 or idx >= len(self.user_list):
            return
        u = self.user_list[idx]
        self.username_var.set(u["username"])
        self.password_var.set("")
        self.pass_entry.focus_set()

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("هشدار", "نام کاربری و رمز را وارد کنید.")
            return
        user = users.login(username, password)
        if user is None:
            messagebox.showerror("خطا", "نام کاربری یا رمز اشتباه است.")
            self.password_var.set("")
            self.pass_entry.focus_set()
            return
        self.user = user
        self.root.destroy()

    def _cancel(self):
        self.user = None
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.user