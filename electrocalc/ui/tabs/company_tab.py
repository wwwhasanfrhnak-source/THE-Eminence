"""تب اطلاعات شرکت — فقط مدیر."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, StringVar
from pathlib import Path

from electrocalc.config import constants as C
from electrocalc.core import company as comp
from electrocalc.ui.scrollable_frame import ScrollableFrame


class CompanyTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.logo_img = None
        self.build_ui()
        self.load()

    def build_ui(self):
        p = self.inner

        ttk.Label(p, text="🏢  اطلاعات شرکت", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p, text="اطلاعات شرکت که در فاکتورها و PDFها استفاده می‌شود",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(
            anchor="w", pady=(0, 15))

        # ===== لوگو =====
        logo_frame = ttk.LabelFrame(p, text="لوگوی شرکت", padding=15)
        logo_frame.pack(fill="x", pady=(0, 15))

        self.logo_label = tk.Label(logo_frame, bg=C.COLOR_BG,
                                     text="بدون لوگو",
                                     font=C.FONT_BODY,
                                     fg=C.COLOR_MUTED,
                                     width=20, height=5)
        self.logo_label.pack(side="right", padx=(0, 15))

        logo_btns = ttk.Frame(logo_frame)
        logo_btns.pack(side="right", fill="y")

        ttk.Button(logo_btns, text="📁 انتخاب لوگو",
                   command=self._choose_logo).pack(fill="x", pady=3)
        ttk.Button(logo_btns, text="🗑 حذف لوگو",
                   command=self._remove_logo).pack(fill="x", pady=3)

        # ===== فرم اطلاعات =====
        form = ttk.LabelFrame(p, text="اطلاعات اصلی", padding=15)
        form.pack(fill="x", pady=(0, 15))

        self.vars = {}
        fields = [
            ("name", "نام شرکت *:"),
            ("address", "آدرس:"),
            ("phone", "تلفن:"),
            ("email", "ایمیل:"),
            ("website", "وب‌سایت:"),
            ("registration", "شماره ثبت:"),
            ("tax_id", "کد اقتصادی:"),
            ("economic_code", "شناسه ملی:"),
        ]

        for i, (key, label) in enumerate(fields):
            ttk.Label(form, text=label, font=C.FONT_BODY).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=6)
            var = StringVar()
            self.vars[key] = var
            ttk.Entry(form, textvariable=var, width=45).grid(
                row=i, column=1, pady=6, sticky="ew")

        form.columnconfigure(1, weight=1)

        # ===== دکمه‌ها =====
        btns = ttk.Frame(p)
        btns.pack(fill="x", pady=(0, 10))
        ttk.Button(btns, text="💾 ذخیره",
                   command=self._save).pack(side="left", ipadx=20)
        ttk.Button(btns, text="🔄 بازگردانی",
                   command=self.load).pack(side="left", padx=8)

    def load(self):
        """بارگذاری اطلاعات شرکت."""
        c = comp.get_company()
        if not c:
            return
        self.vars["name"].set(c["name"] or "")
        self.vars["address"].set(c["address"] or "")
        self.vars["phone"].set(c["phone"] or "")
        self.vars["email"].set(c["email"] or "")
        self.vars["website"].set(c["website"] or "")
        self.vars["registration"].set(c["registration"] or "")
        self.vars["tax_id"].set(c["tax_id"] or "")
        self.vars["economic_code"].set(c["economic_code"] or "")

        # لوگو
        if c["logo_path"] and Path(c["logo_path"]).exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(c["logo_path"])
                # تغییر سایز
                img.thumbnail((150, 100), Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                self.logo_label.config(image=self.logo_img, text="")
            except Exception:
                self.logo_label.config(text="خطا در بارگذاری", image="")
        else:
            self.logo_label.config(image="", text="بدون لوگو")

    def _choose_logo(self):
        path = filedialog.askopenfilename(
            title="انتخاب لوگو",
            filetypes=[("تصویر", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if not path:
            return
        try:
            comp.set_logo(path)
            self.load()
            messagebox.showinfo("موفق", "لوگو ذخیره شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _remove_logo(self):
        if not messagebox.askyesno("تأیید", "لوگو حذف شود؟"):
            return
        comp.remove_logo()
        self.load()

    def _save(self):
        try:
            name = self.vars["name"].get().strip()
            if not name:
                raise ValueError("نام شرکت الزامی است.")

            comp.save_company(
                name=name,
                address=self.vars["address"].get(),
                phone=self.vars["phone"].get(),
                email=self.vars["email"].get(),
                website=self.vars["website"].get(),
                registration=self.vars["registration"].get(),
                tax_id=self.vars["tax_id"].get(),
                economic_code=self.vars["economic_code"].get(),
            )
            messagebox.showinfo("موفق", "اطلاعات شرکت ذخیره شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))