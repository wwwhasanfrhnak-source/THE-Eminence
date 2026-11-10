"""Login window using the shared THE Eminence enterprise design system."""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk, ImageSequence

from electrocalc.auth import users
from electrocalc.config import themes as themes_module
from electrocalc.core import settings as settings_module
from electrocalc.data.database import get_connection
from electrocalc.ui.design_system import configure_ttk, style_toplevel, TOKENS
from electrocalc.utils.avatar import get_avatar


def get_active_users():
    connection = get_connection()
    try:
        return list(connection.execute(
            "SELECT * FROM users WHERE active = 1 ORDER BY username"
        ).fetchall())
    finally:
        connection.close()


class LoginWindow:
    def __init__(self):
        self.theme_name = settings_module.get_setting("app_theme", "light")
        if self.theme_name not in themes_module.get_names():
            self.theme_name = "light"
        self.palette = themes_module.get_palette(self.theme_name)
        self.root = tk.Tk()
        self.root.title("ورود به THE Eminence")
        self.root.geometry("520x750")
        self.root.minsize(480, 720)
        self.root.resizable(True, True)
        style_toplevel(self.root, self.palette)
        configure_ttk(ttk.Style(self.root), self.palette)
        self.user = None
        self.user_list = []
        self.avatar_cache = {}
        self._center()
        self._build_ui()

    def _center(self):
        self.root.update_idletasks()
        width, height = 520, 750
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        p = self.palette
        shell = tk.Frame(self.root, bg=p["bg"], padx=28, pady=15)
        shell.pack(fill="both", expand=True)

        # 1. لوگو
        brand_card = tk.Frame(shell, bg=p["sidebar"], highlightbackground=p["border"],
                              highlightthickness=1, padx=20, pady=15)
        brand_card.pack(fill="x", pady=(0, 10))
        tk.Label(brand_card, text="⚡  THE Eminence", bg=p["sidebar"], fg=p["accent"],
                 font=(TOKENS["font_family"], 24, "bold")).pack(anchor="center")
        tk.Label(brand_card, text="PROFESSIONAL ELECTRICAL MANAGEMENT",
                 bg=p["sidebar"], fg=p["muted"], font=(TOKENS["font_family"], 8, "bold")).pack(pady=(4, 0))

        # ==================== دکمه Enter (بالای صفحه) ====================
        top_bar = tk.Frame(shell, bg=p["bg"])
        top_bar.pack(fill="x", pady=(5, 10))  # فاصله از لوگو و کادر پایین
        
        # عنوان سمت راست
        tk.Label(top_bar, text="به حساب کاربری خود وارد شوید", bg=p["bg"], fg=p["text"],
                 font=(TOKENS["font_family"], 15, "bold")).pack(side="right")
                 
        # دکمه عکس سمت چپ (با فاصله از پایین)
        self.enter_btn = tk.Label(top_bar, bg=p["bg"], cursor="hand2")
        self.enter_btn.pack(side="left", pady=5)
        self.enter_btn.bind("<Button-1>", lambda e: self._login())
        
        # بارگذاری عکس PNG
        base_dir = r"C:\Users\H.R\Desktop\برنامه برق\ElectroCalc"
        png_path = os.path.join(base_dir, "assets", "enter_anim.png")
        try:
            img = Image.open(png_path)
            img = img.resize((45, 45), Image.LANCZOS)
            self._enter_img = ImageTk.PhotoImage(img)
            self.enter_btn.configure(image=self._enter_img)
        except Exception as e:
            print(f"Error loading PNG: {e}")
        # =========================================================================

        # 2. انتخاب سریع کاربر
        user_card = tk.Frame(shell, bg=p["sidebar"], highlightbackground=p["border"], highlightthickness=1)
        user_card.pack(fill="x", pady=(0, 10))
        tk.Label(user_card, text="انتخاب سریع کاربر", bg=p["sidebar"], fg=p["text"],
                 font=(TOKENS["font_family"], 10, "bold"), anchor="e").pack(fill="x", padx=14, pady=(8, 4))
        self.users_container = tk.Frame(user_card, bg=p["sidebar"])
        self.users_container.pack(fill="x", padx=10, pady=(0, 8))
        self._load_users()

        # 3. فرم ورود
        form = tk.Frame(shell, bg=p["sidebar"], highlightbackground=p["border"],
                        highlightthickness=1, padx=16, pady=10)
        form.pack(fill="x")
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        tk.Label(form, text="نام کاربری", bg=p["sidebar"], fg=p["muted"],
                 font=(TOKENS["font_family"], 9, "bold"), anchor="e").pack(fill="x")
        ttk.Entry(form, textvariable=self.username_var).pack(fill="x", pady=(2, 8), ipady=4)
        tk.Label(form, text="رمز عبور", bg=p["sidebar"], fg=p["muted"],
                 font=(TOKENS["font_family"], 9, "bold"), anchor="e").pack(fill="x")
        self.pass_entry = ttk.Entry(form, textvariable=self.password_var, show="●")
        self.pass_entry.pack(fill="x", pady=(2, 4), ipady=4)

        # 4. فضای انیمیشن (تیک و ضربدر) - با فاصله بیشتر از فرم
        self.anim_frame = tk.Frame(shell, bg=p["bg"], height=90)
        self.anim_frame.pack(fill="x", pady=(15, 0))  # فاصله ۱۵ پیکسلی از بالا
        self.anim_frame.pack_propagate(False)
        self.anim_label = tk.Label(self.anim_frame, bg=p["bg"])
        self.anim_label.pack(expand=True)

        tk.Label(shell, text="THE Eminence  •  محیط امن مدیریت پروژه‌های برق",
                 bg=p["bg"], fg=p["muted"], font=(TOKENS["font_family"], 8)).pack(side="bottom", pady=(5, 0))

        # 5. فعال کردن Enter کیبورد
        self.root.bind("<Return>", lambda event: self._login())
        self.pass_entry.bind("<Return>", lambda event: self._login())
        self.root.protocol("WM_DELETE_WINDOW", self._cancel)

        if self.user_list:
            self._pick_user(0)

    def _load_users(self):
        self.user_list = get_active_users()
        self.avatar_cache.clear()
        if not self.user_list:
            tk.Label(self.users_container, text="هیچ کاربر فعالی وجود ندارد",
                     font=(TOKENS["font_family"], 9), bg=self.palette["sidebar"],
                     fg=self.palette["danger"], pady=10).pack(fill="x")
            return
        for index, user in enumerate(self.user_list):
            self.avatar_cache[f"av_{index}"] = get_avatar(user, 34)
            row = tk.Frame(self.users_container, bg=self.palette["sidebar"], cursor="hand2",
                           highlightbackground=self.palette["border"], highlightthickness=1)
            row.pack(fill="x", pady=3)
            avatar = self.avatar_cache[f"av_{index}"]
            if avatar:
                image_label = tk.Label(row, image=avatar, bg=self.palette["sidebar"])
                image_label.image = avatar
                image_label.pack(side="right", padx=8, pady=5)
            display_name = user["full_name"] or user["username"]
            name_label = tk.Label(row, text=display_name, font=(TOKENS["font_family"], 9, "bold"),
                                  bg=self.palette["sidebar"], fg=self.palette["text"], anchor="e", padx=10, pady=9)
            name_label.pack(side="right", fill="x", expand=True)
            for widget in (row, name_label):
                widget.bind("<Button-1>", lambda event, idx=index: self._pick_user(idx))
                widget.bind("<Enter>", lambda event, target=row: target.configure(bg=self.palette["bg"]))
                widget.bind("<Leave>", lambda event, target=row: target.configure(bg=self.palette["sidebar"]))

    def _pick_user(self, idx):
        if 0 <= idx < len(self.user_list):
            self.username_var.set(self.user_list[idx]["username"])
            self.password_var.set("")
            self.pass_entry.focus_set()

    def _show_anim(self, gif_name):
        self.anim_label.configure(image="")
        base_dir = r"C:\Users\H.R\Desktop\برنامه برق\ElectroCalc"
        gif_path = os.path.join(base_dir, "assets", gif_name)
        try:
            img = Image.open(gif_path)
            frames = []
            for frame in ImageSequence.Iterator(img):
                frame_img = frame.convert("RGBA").resize((70, 70), Image.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame_img))
            current = [0]
            def animate():
                if current[0] >= len(frames):
                    return
                self.anim_label.configure(image=frames[current[0]])
                current[0] += 1
                self.anim_frame.after(60, animate)
            animate()
        except Exception as e:
            print(f"Anim Error: {e}")

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showwarning("ورود", "نام کاربری و رمز عبور را وارد کنید.", parent=self.root)
            return
        
        authenticated_user = users.login(username, password)
        
        if authenticated_user is None:
            self._show_anim("error.gif")
            messagebox.showerror("ورود ناموفق", "نام کاربری یا رمز عبور نادرست است.", parent=self.root)
            self.password_var.set("")
            self.pass_entry.focus_set()
            return
        
        self._show_anim("success.gif")
        self.user = authenticated_user
        self.root.after(4000, self.root.destroy)

    def _cancel(self):
        self.user = None
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.user