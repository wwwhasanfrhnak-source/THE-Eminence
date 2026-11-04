"""تب محاسبه موتور."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import motor


class MotorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.power_var = StringVar(master=self, value="")
        self.voltage_var = StringVar(master=self, value="380")
        self.cos_var = StringVar(master=self, value="0.85")
        self.eff_var = StringVar(master=self, value="0.9")
        self.phase_var = StringVar(master=self, value="3phase")
        self.result_nom = StringVar(master=self, value="")
        self.result_start = StringVar(master=self, value="")
        self.result_factor = StringVar(master=self, value="")
        self.build_ui()

    def build_ui(self) -> None:
        ttk.Label(self, text="⚡  محاسبه موتور", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(self, text="جریان نامی و راه‌انداز موتور را محاسبه کن",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 18))

        sys_box = ttk.LabelFrame(self, text="نوع موتور", padding=14)
        sys_box.pack(fill="x", pady=(0, 14))
        ttk.Radiobutton(sys_box, text="سه‌فاز", value="3phase",
                        variable=self.phase_var).pack(anchor="w", pady=3)
        ttk.Radiobutton(sys_box, text="تک‌فاز", value="1phase",
                        variable=self.phase_var).pack(anchor="w", pady=3)

        inp = ttk.LabelFrame(self, text="ورودی‌ها", padding=14)
        inp.pack(fill="x", pady=(0, 14))

        rows = [
            ("توان موتور (kW):", self.power_var),
            ("ولتاژ (V):", self.voltage_var),
            ("ضریب توان (cos φ):", self.cos_var),
            ("بازده (η):", self.eff_var),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(inp, text=label, font=C.FONT_BODY).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=6)
            ttk.Entry(inp, textvariable=var, width=20).grid(
                row=i, column=1, sticky="w", pady=6)

        ttk.Label(inp, text="مقادیر معمول: cos φ = 0.85 ، η = 0.9",
                  font=C.FONT_SMALL, foreground=C.COLOR_MUTED).grid(
            row=4, column=1, sticky="w")

        btn = ttk.Frame(self)
        btn.pack(fill="x", pady=(0, 14))
        ttk.Button(btn, text="محاسبه", command=self.calculate).pack(side="left")
        ttk.Button(btn, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        res = ttk.LabelFrame(self, text="نتیجه", padding=14)
        res.pack(fill="x")

        for i, (label, var, color) in enumerate([
            ("جریان نامی:", self.result_nom, C.COLOR_SUCCESS),
            ("جریان راه‌انداز:", self.result_start, C.COLOR_DANGER),
            ("ضریب راه‌انداز:", self.result_factor, C.COLOR_ACCENT),
        ]):
            ttk.Label(res, text=label, font=C.FONT_BODY).grid(
                row=i, column=0, sticky="w", pady=6)
            ttk.Label(res, textvariable=var, font=C.FONT_RESULT,
                      foreground=color).grid(row=i, column=1, sticky="w",
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
            power = self._read_float(self.power_var, "توان")
            v = self._read_float(self.voltage_var, "ولتاژ")
            cos_phi = self._read_float(self.cos_var, "ضریب توان")
            eff = self._read_float(self.eff_var, "بازده")

            three_phase = (self.phase_var.get() == "3phase")

            r = motor.calc_motor_current(
                power_kw=power, voltage=v,
                cos_phi=cos_phi, efficiency=eff,
                three_phase=three_phase,
            )

            self.result_nom.set(f"{r.nominal_current:.2f}  A")
            self.result_start.set(f"{r.starting_current:.2f}  A")
            self.result_factor.set(f"{r.starting_factor:.1f}  ×")
            self.app.set_status(f"جریان نامی موتور: {r.nominal_current:.2f} A")
        except ValueError as e:
            self.clear_results()
            messagebox.showerror("خطای ورودی", str(e))

    def clear(self) -> None:
        self.power_var.set("")
        self.voltage_var.set("380")
        self.cos_var.set("0.85")
        self.eff_var.set("0.9")
        self.clear_results()

    def clear_results(self) -> None:
        self.result_nom.set("")
        self.result_start.set("")
        self.result_factor.set("")