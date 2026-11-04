"""تب تنظیمات — فقط مدیر."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.config import themes as themes_module
from electrocalc.core import settings as st
from electrocalc.core import audit as audit_module
from electrocalc.ui.scrollable_frame import ScrollableFrame


class SettingsTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.vars = {}
        self.scroll_speed_var = tk.DoubleVar(value=0.5)
        self.scroll_speed_label = StringVar(value="0.50")
        self.build_ui()
        self.load()

    def build_ui(self):
        p = self.inner

        ttk.Label(p, text="⚙️  تنظیمات برنامه",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p, text="تنظیمات کلی نرم‌افزار",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # ===== تم =====
        appear = ttk.LabelFrame(p, text="🎨 تم", padding=15)
        appear.pack(fill="x", pady=(0, 12))

        ttk.Label(appear, text="انتخاب تم:",
                  font=C.FONT_BODY).grid(row=0, column=0,
                                          sticky="w", padx=(0, 8), pady=6)
        theme_names = [themes_module.THEMES[k]["name"]
                        for k in themes_module.get_names()]
        self.theme_var = StringVar()
        combo = ttk.Combobox(appear, textvariable=self.theme_var,
                              values=theme_names, state="readonly", width=22)
        combo.grid(row=0, column=1, sticky="w", pady=6)
        combo.bind("<<ComboboxSelected>>",
                    lambda e: self._apply_theme_now())

        ttk.Button(appear, text="🎨 اعمال تم",
                   command=self._apply_theme_now).grid(
            row=1, column=0, columnspan=2, sticky="w",
            pady=(8, 0), ipadx=15)

        # ===== حالت اسکرول =====
        scroll_box = ttk.LabelFrame(p, text="📜 حالت اسکرول‌بار", padding=15)
        scroll_box.pack(fill="x", pady=(0, 12))

        ttk.Label(scroll_box, text="حالت:",
                  font=C.FONT_BODY).grid(row=0, column=0,
                                          sticky="w", padx=(0, 8), pady=6)
        self.scroll_var = StringVar()
        scroll_combo = ttk.Combobox(
            scroll_box, textvariable=self.scroll_var,
            values=["همیشه نمایان", "مخفی (فقط چرخ ماوس)",
                    "نازک", "هوشمند (خودکار)",
                    "لمسی (فلش‌دار + کشیدن انگشت)"],
            state="readonly", width=28,
        )
        scroll_combo.grid(row=0, column=1, sticky="w", pady=6)
        scroll_combo.bind("<<ComboboxSelected>>",
                           lambda e: self._apply_scroll())

        ttk.Label(scroll_box, text="🎚️  سرعت اسکرول:",
                  font=C.FONT_BODY).grid(row=1, column=0,
                                          sticky="w", padx=(0, 8), pady=(12, 6))

        speed_frame = ttk.Frame(scroll_box)
        speed_frame.grid(row=1, column=1, sticky="ew", pady=(12, 6))

        self.speed_scale = tk.Scale(
            speed_frame,
            from_=0.1, to=2.0,
            resolution=0.1,
            orient="horizontal",
            length=250,
            variable=self.scroll_speed_var,
            command=self._on_speed_change,
            showvalue=False,
            bg=C.COLOR_BG,
            highlightthickness=0,
            troughcolor=C.COLOR_TAB_BG,
            activebackground=C.COLOR_HEADER_BG,
        )
        self.speed_scale.pack(side="right", fill="x", expand=True)

        ttk.Label(speed_frame, textvariable=self.scroll_speed_label,
                  font=("Consolas", 11, "bold"),
                  foreground=C.COLOR_HEADER_BG,
                  width=6).pack(side="left", padx=8)

        ttk.Label(scroll_box,
                  text="🐢  نرم (0.3)   |   🚶  معمولی (0.5)   |   "
                       "🏃  سریع (1.0)   |   🚀  خیلی سریع (2.0)",
                  font=C.FONT_SMALL,
                  foreground=C.COLOR_MUTED).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

        tk.Label(scroll_box,
                  text="ℹ️ تغییرات به‌صورت زنده اعمال می‌شوند",
                  font=C.FONT_SMALL, bg=C.COLOR_BG,
                  fg=C.COLOR_SUCCESS, anchor="e").grid(
            row=3, column=0, columnspan=2, sticky="e", pady=(5, 0))

        # ===== زبان =====
        lang = ttk.LabelFrame(p, text="🌐 زبان", padding=15)
        lang.pack(fill="x", pady=(0, 12))

        ttk.Label(lang, text="زبان:", font=C.FONT_BODY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.lang_var = StringVar()
        combo2 = ttk.Combobox(lang, textvariable=self.lang_var,
                               values=["فارسی", "English"],
                               state="readonly", width=22)
        combo2.grid(row=0, column=1, sticky="w", pady=6)

        # ===== محاسبات =====
        calc = ttk.LabelFrame(p, text="🧮 پیش‌فرض‌های محاسبات", padding=15)
        calc.pack(fill="x", pady=(0, 12))

        self._add_entry(calc, 0, "decimal_places", "تعداد اعشار:")
        self._add_entry(calc, 1, "default_cos_phi", "cos φ پیش‌فرض:")
        self._add_entry(calc, 2, "default_voltage", "ولتاژ تک‌فاز (V):")
        self._add_entry(calc, 3, "default_voltage_3ph", "ولتاژ سه‌فاز (V):")
        self._add_entry(calc, 4, "default_efficiency", "بازده موتور پیش‌فرض:")

        # ===== پشتیبان‌گیری =====
        backup = ttk.LabelFrame(p, text="💾 پشتیبان‌گیری", padding=15)
        backup.pack(fill="x", pady=(0, 12))
        self._add_check(backup, 0, "backup_on_start",
                        "پشتیبان‌گیری خودکار هنگام باز شدن برنامه")

        # ===== امنیت =====
        security = ttk.LabelFrame(p, text="🔒 امنیت", padding=15)
        security.pack(fill="x", pady=(0, 12))
        self._add_entry(security, 0, "auto_lock_minutes",
                        "قفل خودکار بعد از (دقیقه — ۰ = غیرفعال):")

        # ===== اعلان‌ها =====
        notify = ttk.LabelFrame(p, text="🔔 اعلان‌ها", padding=15)
        notify.pack(fill="x", pady=(0, 12))
        self._add_check(notify, 0, "notify_new_reports",
                        "اعلان برای گزارش‌های جدید")
        self._add_check(notify, 1, "notify_new_expenses",
                        "اعلان برای هزینه‌های جدید")
        self._add_check(notify, 2, "notify_low_stock",
                        "اعلان برای کمبود موجودی انبار")

        # ===== دکمه‌ها =====
        btns = ttk.Frame(p)
        btns.pack(fill="x", pady=(15, 0))

        ttk.Button(btns, text="💾 ذخیره تنظیمات",
                   command=self._save).pack(side="left", ipadx=20)
        ttk.Button(btns, text="🔄 بازگردانی",
                   command=self.load).pack(side="left", padx=8)
        ttk.Button(btns, text="⚠️ پیش‌فرض‌ها",
                   command=self._reset).pack(side="left")

    def _add_entry(self, parent, row, key, label):
        ttk.Label(parent, text=label, font=C.FONT_BODY).grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=6)
        var = StringVar()
        self.vars[key] = ("entry", var)
        ttk.Entry(parent, textvariable=var, width=22).grid(
            row=row, column=1, sticky="w", pady=6)

    def _add_check(self, parent, row, key, label):
        var = tk.BooleanVar()
        self.vars[key] = ("check", var)
        tk.Checkbutton(parent, text=label, variable=var,
                       bg=C.COLOR_BG, fg=C.COLOR_TEXT,
                       activebackground=C.COLOR_BG,
                       font=C.FONT_BODY, anchor="e").grid(
            row=row, column=0, columnspan=2, sticky="e", pady=6)

    def load(self):
        data = st.get_all()
        for key, tup in self.vars.items():
            kind = tup[0]
            value = data.get(key, "")
            if kind == "entry":
                tup[1].set(str(value))
            elif kind == "check":
                tup[1].set(str(value) == "1")

        theme_key = data.get("app_theme", "light")
        theme_names = themes_module.get_names()
        if theme_key in theme_names:
            self.theme_var.set(themes_module.THEMES[theme_key]["name"])
        else:
            self.theme_var.set(themes_module.THEMES["light"]["name"])

        lang = data.get("app_language", "fa")
        self.lang_var.set("فارسی" if lang == "fa" else "English")

        scroll_map_rev = {
            "always": "همیشه نمایان",
            "hidden": "مخفی (فقط چرخ ماوس)",
            "thin": "نازک",
            "smart": "هوشمند (خودکار)",
            "touch": "لمسی (فلش‌دار + کشیدن انگشت)",
        }
        scroll_val = data.get("scroll_mode", "always")
        self.scroll_var.set(scroll_map_rev.get(scroll_val, "همیشه نمایان"))

        try:
            speed = float(data.get("scroll_speed", "0.5"))
        except Exception:
            speed = 0.5
        self.scroll_speed_var.set(speed)
        self._update_speed_label(speed)

    def _on_speed_change(self, value):
        try:
            v = float(value)
            self._update_speed_label(v)
            # ⭐ اعمال زنده
            try:
                from electrocalc.ui.scrollable_frame import set_scroll_speed
                set_scroll_speed(v)
            except Exception:
                pass
        except Exception:
            pass

    def _update_speed_label(self, value):
        self.scroll_speed_label.set(f"{value:.2f}")

    def _apply_theme_now(self):
        selected_name = self.theme_var.get()
        selected_key = None
        for k in themes_module.get_names():
            if themes_module.THEMES[k]["name"] == selected_name:
                selected_key = k
                break
        if not selected_key:
            return
        try:
            st.set_setting("app_theme", selected_key)
            self.app.set_theme(selected_key)
            messagebox.showinfo("موفق",
                                 f"تم «{selected_name}» اعمال شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _apply_scroll(self):
        mapping = {
            "همیشه نمایان": "always",
            "مخفی (فقط چرخ ماوس)": "hidden",
            "نازک": "thin",
            "هوشمند (خودکار)": "smart",
            "لمسی (فلش‌دار + کشیدن انگشت)": "touch",
        }
        value = mapping.get(self.scroll_var.get(), "always")
        st.set_setting("scroll_mode", value)

        try:
            from electrocalc.ui.scrollable_frame import set_scroll_mode
            set_scroll_mode(value)
        except Exception:
            pass

        # بازسازی UI
        try:
            if hasattr(self.app, "reload_ui"):
                self.app.reload_ui()
        except Exception:
            pass

    def _save(self):
        try:
            for key, tup in self.vars.items():
                kind = tup[0]
                if kind == "entry":
                    st.set_setting(key, tup[1].get().strip())
                elif kind == "check":
                    st.set_setting(key, "1" if tup[1].get() else "0")

            st.set_setting("app_language",
                            "fa" if self.lang_var.get() == "فارسی" else "en")

            mapping = {
                "همیشه نمایان": "always",
                "مخفی (فقط چرخ ماوس)": "hidden",
                "نازک": "thin",
                "هوشمند (خودکار)": "smart",
                "لمسی (فلش‌دار + کشیدن انگشت)": "touch",
            }
            new_mode = mapping.get(self.scroll_var.get(), "always")
            new_speed = self.scroll_speed_var.get()

            st.set_setting("scroll_mode", new_mode)
            st.set_setting("scroll_speed", f"{new_speed:.2f}")

            # ⭐ اعمال زنده
            try:
                from electrocalc.ui.scrollable_frame import (
                    set_scroll_speed, set_scroll_mode
                )
                set_scroll_speed(new_speed)
                set_scroll_mode(new_mode)
            except Exception:
                pass

            try:
                audit_module.log_action(
                    username=(self.app.current_user["username"]
                              if self.app.current_user else "?"),
                    action="update",
                    object_type="settings",
                    description="ذخیره تنظیمات برنامه",
                )
            except Exception:
                pass

            messagebox.showinfo("موفق", "تنظیمات ذخیره و اعمال شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _reset(self):
        if not messagebox.askyesno(
            "⚠️ بازگشت به پیش‌فرض",
            "همه تنظیمات به حالت پیش‌فرض برگردند؟"
        ):
            return
        st.reset_all()
        self.load()

        # اعمال زنده
        try:
            from electrocalc.ui.scrollable_frame import (
                set_scroll_speed, set_scroll_mode
            )
            set_scroll_speed(0.5)
            set_scroll_mode("always")
        except Exception:
            pass

        messagebox.showinfo("موفق", "تنظیمات به پیش‌فرض برگشت.")