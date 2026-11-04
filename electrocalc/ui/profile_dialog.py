"""پنجره تغییر پروفایل کاربر."""

import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime

from electrocalc.auth import users
from electrocalc.config import constants as C
from electrocalc.utils.avatar import get_avatar, ASSETS_DIR


class ProfileDialog:
    def __init__(self, parent, username: str, on_done=None):
        self.username = username
        self.on_done = on_done
        self.changed = False
        self.preview_img = None

        self.win = tk.Toplevel(parent)
        self.win.title("تغییر پروفایل")
        self.win.geometry("400x500")
        self.win.configure(bg=C.COLOR_BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self._center(parent)
        self._build_ui()

    def _center(self, parent):
        self.win.update_idletasks()
        w, h = 400, 500
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - w // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - h // 2
        self.win.geometry(f"{w}x{h}+{px}+{py}")

    def _build_ui(self):
        tk.Label(
            self.win, text="📸  تغییر پروفایل",
            font=C.FONT_TITLE, bg=C.COLOR_BG, fg=C.COLOR_HEADER_BG,
        ).pack(pady=(25, 15))

        # نمایش پروفایل فعلی
        self.preview_label = tk.Label(self.win, bg=C.COLOR_BG)
        self.preview_label.pack(pady=10)
        self._load_preview()

        # دکمه‌ها
        btn_frame = tk.Frame(self.win, bg=C.COLOR_BG)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="📁 انتخاب عکس جدید",
                   command=self._choose_image).pack(pady=5, ipadx=20, ipady=4)
        ttk.Button(btn_frame, text="🗑 حذف پروفایل",
                   command=self._delete_profile).pack(pady=5, ipadx=20, ipady=4)
        ttk.Button(btn_frame, text="بستن",
                   command=self.win.destroy).pack(pady=5, ipadx=20, ipady=4)

        tk.Label(
            self.win, text="فرمت‌های مجاز: PNG, JPG, JPEG",
            font=C.FONT_SMALL, bg=C.COLOR_BG, fg=C.COLOR_MUTED,
        ).pack()

    def _load_preview(self):
        user = users.get_user(self.username)
        img = get_avatar(user, 150)
        if img:
            self.preview_label.config(image=img)
            self.preview_label.image = img
            self.preview_img = img

    def _choose_image(self):
        path = filedialog.askopenfilename(
            title="انتخاب عکس پروفایل",
            filetypes=[("تصویر", "*.png *.jpg *.jpeg *.bmp")],
        )
        if not path:
            return

        try:
            # کپی به پوشه assets
            ext = Path(path).suffix.lower()
            new_name = f"avatar_{self.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            dest = ASSETS_DIR / new_name
            shutil.copy(path, dest)

            # ذخیره در پایگاه داده
            users.set_avatar(self.username, str(dest))

            self.changed = True
            self._load_preview()
            messagebox.showinfo("موفق", "پروفایل تغییر کرد.", parent=self.win)
            if self.on_done:
                self.on_done()
        except Exception as e:
            messagebox.showerror("خطا", str(e), parent=self.win)

    def _delete_profile(self):
        if not messagebox.askyesno("تأیید", "پروفایل حذف شود؟", parent=self.win):
            return
        users.set_avatar(self.username, "")
        self.changed = True
        self._load_preview()
        if self.on_done:
            self.on_done()