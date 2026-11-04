"""تب تبدیل واحد."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import units


class UnitsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.mode_var = StringVar(master=self, value="kw_hp")
        self.input_var = StringVar(master=self, value="")
        self.result_var = StringVar(master=self, value="")
        self.build_ui()

    def build_ui(self) -> None:
        ttk.Label(self, text="⚡  تبدیل واحد", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(self, text="تبدیل سریع واحدهای پرکاربرد برق",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 18))

        mode_box = ttk.LabelFrame(self, text="نوع تبدیل", padding=14)
        mode_box.pack(fill="x", pady=(0, 14))

        options = [
            ("kw_hp", "کیلووات (kW) → اسب بخار (HP)"),
            ("hp_kw", "اسب بخار (HP) → کیلووات (kW)"),
            ("mm_awg", "سطح مقطع (mm²) → AWG"),
            ("c_f", "سلسیوس (°C) → فارنهایت (°F)"),
            ("f_c", "فارنهایت (°F) → سلسیوس (°C)"),
        ]
        for value, label in options:
            ttk.Radiobutton(mode_box, text=label, value=value,
                            variable=self.mode_var,
                            command=self._on_change).pack(anchor="w", pady=3)

        inp = ttk.LabelFrame(self, text="ورودی", padding=14)
        inp.pack(fill="x", pady=(0, 14))
        self.input_label = ttk.Label(inp, text="کیلووات (kW):", font=C.FONT_BODY)
        self.input_label.pack(side="left", padx=(0, 8))
        ttk.Entry(inp, textvariable=self.input_var, width=20).pack(side="left")

        btn = ttk.Frame(self)
        btn.pack(fill="x", pady=(0, 14))
        ttk.Button(btn, text="تبدیل", command=self.calculate).pack(side="left")
        ttk.Button(btn, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        res = ttk.LabelFrame(self, text="نتیجه", padding=14)
        res.pack(fill="x")
        ttk.Label(res, textvariable=self.result_var, font=C.FONT_RESULT,
                  foreground=C.COLOR_SUCCESS).pack(anchor="w")

    def _on_change(self) -> None:
        labels = {
            "kw_hp": "کیلووات (kW):",
            "hp_kw": "اسب بخار (HP):",
            "mm_awg": "سطح مقطع (mm²):",
            "c_f": "سلسیوس (°C):",
            "f_c": "فارنهایت (°F):",
        }
        self.input_label.config(text=labels.get(self.mode_var.get(), "مقدار:"))
        self.result_var.set("")

    def calculate(self) -> None:
        try:
            text = self.input_var.get().strip()
            if not text:
                raise ValueError("مقدار را وارد کن.")
            value = float(text.replace(",", ""))

            mode = self.mode_var.get()
            if mode == "kw_hp":
                r = units.kw_to_hp(value)
                self.result_var.set(f"{r:.4f}  HP")
            elif mode == "hp_kw":
                r = units.hp_to_kw(value)
                self.result_var.set(f"{r:.4f}  kW")
            elif mode == "mm_awg":
                r = units.mm2_to_awg(value)
                self.result_var.set(f"AWG {r}")
            elif mode == "c_f":
                r = units.celsius_to_fahrenheit(value)
                self.result_var.set(f"{r:.2f}  °F")
            else:
                r = units.fahrenheit_to_celsius(value)
                self.result_var.set(f"{r:.2f}  °C")
            self.app.set_status("تبدیل انجام شد")
        except ValueError as e:
            self.result_var.set("")
            messagebox.showerror("خطای ورودی", str(e))

    def clear(self) -> None:
        self.input_var.set("")
        self.result_var.set("")