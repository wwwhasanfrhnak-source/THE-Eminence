"""تب ماشین حساب — همه محاسبات برق در یک جا."""

import tkinter as tk
from tkinter import ttk

from electrocalc.config import constants as C


CALCULATIONS = [
    ("⚡", "قانون اهم", "electrocalc.ui.tabs.ohm_tab", "OhmTab"),
    ("💡", "توان", "electrocalc.ui.tabs.power_tab", "PowerTab"),
    ("📉", "افت ولتاژ", "electrocalc.ui.tabs.voltage_drop_tab", "VoltageDropTab"),
    ("🔌", "جریان کابل", "electrocalc.ui.tabs.ampacity_tab", "AmpacityTab"),
    ("🔒", "فیوز", "electrocalc.ui.tabs.fuse_tab", "FuseTab"),
    ("⚙️", "موتور", "electrocalc.ui.tabs.motor_tab", "MotorTab"),
    ("⚙️", "موتور پیشرفته", "electrocalc.ui.tabs.motor_advanced_tab", "MotorAdvancedTab"),
        ("⚡", "مدار RLC", "electrocalc.ui.tabs.rlc_tab", "RLCTab"),
    ("🔺", "ستاره/مثلث", "electrocalc.ui.tabs.star_delta_tab", "StarDeltaTab"),
    ("🔄", "تبدیل واحد", "electrocalc.ui.tabs.units_tab", "UnitsTab"),
]


class CalculatorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.palette = app.palette
        self._current_idx = -1
        self._pages = []
        self._buttons = []
        self._build_ui()
        self._select(0)

    def _build_ui(self):
        p = self.palette

        container = tk.Frame(self, bg=p["bg"])
        container.pack(fill="both", expand=True)

        # ===== منوی داخلی سمت راست =====
        menu = tk.Frame(container, bg=p["sidebar"], width=200)
        menu.pack(side="right", fill="y")
        menu.pack_propagate(False)

        # عنوان منو
        tk.Label(menu, text="🧮  محاسبات برق",
                 font=("Segoe UI", 13, "bold"),
                 bg=p["sidebar"], fg=p["h_start"],
                 pady=15).pack(fill="x")

        tk.Frame(menu, bg=p["border"], height=1).pack(fill="x", padx=10)

        # دکمه‌های منو
        for idx, (icon, label, _, _) in enumerate(CALCULATIONS):
            btn = tk.Label(
                menu, text=f"{label}   {icon}",
                font=("Segoe UI", 11),
                bg=p["sidebar"], fg=p["muted"],
                anchor="e", padx=18, pady=14, cursor="hand2",
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn, i=idx: self._on_hover(b, i, True))
            btn.bind("<Leave>", lambda e, b=btn, i=idx: self._on_hover(b, i, False))
            btn.bind("<Button-1>", lambda e, i=idx: self._select(i))
            self._buttons.append(btn)

        # جداکننده پایین
        tk.Frame(menu, bg=p["border"], height=1).pack(
            fill="x", padx=10, side="bottom", pady=15)

        tk.Label(menu, text="💡 محاسبه رو انتخاب کن",
                 font=("Segoe UI", 8),
                 bg=p["sidebar"], fg=p["muted"],
                 pady=10).pack(side="bottom", fill="x")

        # ===== محتوای اصلی =====
        self._content = tk.Frame(container, bg=p["bg"])
        self._content.pack(side="right", fill="both", expand=True)

        # ساخت همه صفحات
        for icon, label, module_path, class_name in CALCULATIONS:
            page = None
            try:
                mod = __import__(module_path, fromlist=[class_name])
                TabCls = getattr(mod, class_name)
                page = TabCls(self._content, self.app)
            except Exception as e:
                page = self._placeholder(label, str(e))
            self._pages.append(page)

    def _on_hover(self, btn, idx, entering):
        p = self.palette
        if idx == self._current_idx:
            return
        if entering:
            btn.config(bg=p["card"], fg=p["text"])
        else:
            btn.config(bg=p["sidebar"], fg=p["muted"])

    def _select(self, idx):
        if idx < 0 or idx >= len(self._pages):
            return
        if idx == self._current_idx:
            return

        p = self.palette

        # مخفی کردن قبلی
        if self._current_idx >= 0:
            try:
                self._pages[self._current_idx].pack_forget()
                self._buttons[self._current_idx].config(
                    bg=p["sidebar"], fg=p["muted"],
                    font=("Segoe UI", 11),
                )
            except Exception:
                pass

        # نمایش جدید
        try:
            self._pages[idx].pack(fill="both", expand=True)
            self._buttons[idx].config(
                bg=p["card"], fg=p["h_start"],
                font=("Segoe UI", 11, "bold"),
            )
            self._current_idx = idx
        except Exception:
            pass

    def _placeholder(self, title, error):
        p = self.palette
        frame = tk.Frame(self._content, bg=p["bg"], padx=20, pady=20)
        tk.Label(frame, text=f"⚠️ {title}",
                 font=("Segoe UI", 14, "bold"),
                 bg=p["bg"], fg=p["danger"],
                 anchor="e").pack(anchor="e")
        tk.Label(frame, text=error, font=("Consolas", 9),
                 bg=p["bg"], fg=p["muted"],
                 wraplength=600, justify="right",
                 anchor="e").pack(anchor="e", pady=20)
        return frame