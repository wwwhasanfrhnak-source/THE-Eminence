"""تب جریان مجاز کابل."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import ampacity


class AmpacityTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.cross_var = StringVar(master=self, value="")
        self.voltage_var = StringVar(master=self, value="")
        self.cos_var = StringVar(master=self, value="1.0")
        self.phase_var = StringVar(master=self, value="1phase")
        self.result_amp = StringVar(master=self, value="")
        self.result_pow = StringVar(master=self, value="")
        self.build_ui()

    def build_ui(self) -> None:
        ttk.Label(self, text="⚡  جریان مجاز کابل", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(self, text="بر اساس جدول IEC 60364 برای کابل مسی داخل لوله",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 18))

        sys_box = ttk.LabelFrame(self, text="نوع سیستم", padding=14)
        sys_box.pack(fill="x", pady=(0, 14))
        ttk.Radiobutton(sys_box, text="تک‌فاز", value="1phase",
                        variable=self.phase_var).pack(anchor="w", pady=3)
        ttk.Radiobutton(sys_box, text="سه‌فاز", value="3phase",
                        variable=self.phase_var).pack(anchor="w", pady=3)

        inp = ttk.LabelFrame(self, text="ورودی‌ها", padding=14)
        inp.pack(fill="x", pady=(0, 14))

        ttk.Label(inp, text="سطح مقطع (mm²):", font=C.FONT_BODY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(inp, textvariable=self.cross_var, width=20).grid(
            row=0, column=1, sticky="w", pady=6)

        ttk.Label(inp, text="ولتاژ (V):", font=C.FONT_BODY).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(inp, textvariable=self.voltage_var, width=20).grid(
            row=1, column=1, sticky="w", pady=6)

        ttk.Label(inp, text="ضریب توان (cos φ):", font=C.FONT_BODY).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(inp, textvariable=self.cos_var, width=20).grid(
            row=2, column=1, sticky="w", pady=6)

        ttk.Label(inp, text="سطح‌های رایج: 1.5، 2.5، 4، 6، 10، 16، 25، 35",
                  font=C.FONT_SMALL, foreground=C.COLOR_MUTED).grid(
            row=3, column=1, sticky="w", pady=(0, 4))

        btn = ttk.Frame(self)
        btn.pack(fill="x", pady=(0, 14))
        ttk.Button(btn, text="محاسبه", command=self.calculate).pack(side="left")
        ttk.Button(btn, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        res = ttk.LabelFrame(self, text="نتیجه", padding=14)
        res.pack(fill="x")

        ttk.Label(res, text="جریان مجاز:", font=C.FONT_BODY).grid(
            row=0, column=0, sticky="w", pady=6)
        ttk.Label(res, textvariable=self.result_amp, font=C.FONT_RESULT,
                  foreground=C.COLOR_SUCCESS).grid(row=0, column=1, sticky="w",
                                                    padx=(8, 0), pady=6)

        ttk.Label(res, text="حداکثر توان:", font=C.FONT_BODY).grid(
            row=1, column=0, sticky="w", pady=6)
        ttk.Label(res, textvariable=self.result_pow, font=C.FONT_RESULT,
                  foreground=C.COLOR_ACCENT).grid(row=1, column=1, sticky="w",
                                                   padx=(8, 0), pady=6)

    def _read_float(self, var, name: str) -> float:
        text = var.get().strip()
        if not text:
            raise ValueError(f"مقدار «{name}» را وارد کن.")
        try:
            return float(text.replace(",", ""))
        except ValueError:
            raise ValueError(f"مقدار «{name}» باید عدد باشد.")

    def calculate(self) -> None:
        try:
            cross = self._read_float(self.cross_var, "سطح مقطع")
            v = self._read_float(self.voltage_var, "ولتاژ")
            cos_phi = self._read_float(self.cos_var, "ضریب توان")
            three_phase = (self.phase_var.get() == "3phase")

            amp = ampacity.get_ampacity(cross)
            pow_w = ampacity.max_power(cross, v, cos_phi, three_phase)

            self.result_amp.set(f"{amp:.1f}  A")
            self.result_pow.set(f"{pow_w:,.0f}  W  ({pow_w/1000:.2f} kW)")
            self.app.set_status(f"جریان مجاز: {amp} A")
        except ValueError as e:
            self.clear_results()
            messagebox.showerror("خطای ورودی", str(e))

    def clear(self) -> None:
        self.cross_var.set("")
        self.voltage_var.set("")
        self.cos_var.set("1.0")
        self.clear_results()

    def clear_results(self) -> None:
        self.result_amp.set("")
        self.result_pow.set("")