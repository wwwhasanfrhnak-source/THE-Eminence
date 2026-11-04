"""پنجره تغییر رمز عبور."""

import tkinter as tk
from tkinter import ttk, messagebox

from electrocalc.auth import users
from electrocalc.config import constants as C


class ChangePasswordDialog:
    def __init__(self, parent, target_username: str, need_old: bool = True):
        self.target_username = target_username
        self.need_old = need_old
        self.success = False

        self.win = tk.Toplevel(parent)
        self.win.title("تغییر رمز عبور")
        self.win.configure(bg=C.COLOR_BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        h = 320 if need_old else 260
        self.win.geometry(f"400x{h}")

        self._center(parent)
        self._build_ui()

    def _center(self, parent) -> None:
        self.win.update_idletasks()
        w = 400
        h = 320 if self.need_old else 260
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
        self.win.geometry(f"{w}x{h}+{px}+{py}")

    def _build_ui(self) -> None:
        tk.Label(
            self.win, text=f"تغییر رمز: {self.target_username}",
            font=C.FONT_TITLE, bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG,
        ).pack(pady=(20, 15))

        frame = tk.Frame(self.win, bg=C.COLOR_BG)
        frame.pack(padx=30, fill="x")

        row = 0
        if self.need_old:
            tk.Label(frame, text="رمز فعلی:", font=C.FONT_BODY,
                     bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=8)
            self.old_var = tk.StringVar()
            ttk.Entry(frame, textvariable=self.old_var, show="●",
                      width=20).grid(row=row, column=1, pady=8, sticky="ew")
            row += 1

        tk.Label(frame, text="رمز جدید:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=8)
        self.new_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.new_var, show="●",
                  width=20).grid(row=row, column=1, pady=8, sticky="ew")
        row += 1

        tk.Label(frame, text="تکرار رمز جدید:", font=C.FONT_BODY,
                 bg=C.COLOR_BG).grid(row=row, column=0, sticky="w", pady=8)
        self.confirm_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.confirm_var, show="●",
                  width=20).grid(row=row, column=1, pady=8, sticky="ew")

        frame.columnconfigure(1, weight=1)

        tk.Label(self.win, text="حداقل ۶ کاراکتر",
                 font=C.FONT_SMALL, bg=C.COLOR_BG, fg=C.COLOR_MUTED).pack(pady=(5, 0))

        btn_frame = tk.Frame(self.win, bg=C.COLOR_BG)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="ذخیره", command=self._save).pack(
            side="left", padx=5, ipadx=15, ipady=3)
        ttk.Button(btn_frame, text="انصراف", command=self._cancel).pack(
            side="left", padx=5, ipadx=15, ipady=3)

    def _save(self) -> None:
        try:
            if self.need_old:
                user = users.login(self.target_username, self.old_var.get())
                if user is None:
                    messagebox.showerror("خطا", "رمز فعلی اشتباه است.",
                                         parent=self.win)
                    return

            new = self.new_var.get()
            confirm = self.confirm_var.get()

            if len(new) < 6:
                messagebox.showerror("خطا", "رمز باید حداقل ۶ کاراکتر باشد.",
                                     parent=self.win)
                return

            if new != confirm:
                messagebox.showerror("خطا", "رمز جدید و تکرار یکسان نیستند.",
                                     parent=self.win)
                return

            ok = users.change_password(self.target_username, new)
            if ok:
                messagebox.showinfo("موفق", "رمز عبور تغییر کرد.",
                                    parent=self.win)
                self.success = True
                self.win.destroy()
            else:
                messagebox.showerror("خطا", "کاربر پیدا نشد.", parent=self.win)
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)

    def _cancel(self) -> None:
        self.success = False
        self.win.destroy()