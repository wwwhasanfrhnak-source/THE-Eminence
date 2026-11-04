"""تب قانون اهم — رابط کاربری."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import ohm


class OhmTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.mode_var = StringVar(master=self, value="V")
        self.f1_var = StringVar(master=self, value="")
        self.f2_var = StringVar(master=self, value="")
        self.result_var = StringVar(master=self, value="")
        self.build_ui()

    def build_ui(self) -> None:
        ttk.Label(
            self, text="⚡  قانون اهم  (V = I × R)",
            font=C.FONT_TITLE, foreground=C.COLOR_HEADER_BG,
        ).pack(anchor="w", pady=(0, 6))

        ttk.Label(
            self, text="حالت را انتخاب کن، دو مقدار را وارد کن، دکمه محاسبه را بزن.",
            font=C.FONT_BODY, foreground=C.COLOR_MUTED,
        ).pack(anchor="w", pady=(0, 18))

        mode_box = ttk.LabelFrame(self, text="حالت محاسبه", padding=14)
        mode_box.pack(fill="x", pady=(0, 14))

        for value, label in [
            ("V", "محاسبه ولتاژ (V) — می‌دانم I و R"),
            ("I", "محاسبه جریان (I) — می‌دانم V و R"),
            ("R", "محاسبه مقاومت (R) — می‌دانم V و I"),
        ]:
            ttk.Radiobutton(
                mode_box, text=label, value=value,
                variable=self.mode_var, command=self._on_mode_change,
            ).pack(anchor="w", pady=3)

        self.input_box = ttk.LabelFrame(self, text="ورودی‌ها", padding=14)
        self.input_box.pack(fill="x", pady=(0, 14))

        self.lbl1 = ttk.Label(self.input_box, text="جریان (A):", font=C.FONT_BODY)
        self.lbl2 = ttk.Label(self.input_box, text="مقاومت (Ω):", font=C.FONT_BODY)
        self.entry1 = ttk.Entry(self.input_box, textvariable=self.f1_var, width=20)
        self.entry2 = ttk.Entry(self.input_box, textvariable=self.f2_var, width=20)

        self.lbl1.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.entry1.grid(row=0, column=1, sticky="w", pady=6)
        self.lbl2.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        self.entry2.grid(row=1, column=1, sticky="w", pady=6)

        btn_box = ttk.Frame(self)
        btn_box.pack(fill="x", pady=(0, 14))

        ttk.Button(btn_box, text="محاسبه", command=self.calculate).pack(side="left")
        ttk.Button(btn_box, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        result_box = ttk.LabelFrame(self, text="نتیجه", padding=14)
        result_box.pack(fill="x")

        self.result_label = ttk.Label(
            result_box, textvariable=self.result_var,
            font=C.FONT_RESULT, foreground=C.COLOR_SUCCESS,
        )
        self.result_label.pack(anchor="w")

        self._on_mode_change()

    def _on_mode_change(self) -> None:
        mode = self.mode_var.get()
        if mode == "V":
            self.lbl1.config(text="جریان (A):")
            self.lbl2.config(text="مقاومت (Ω):")
        elif mode == "I":
            self.lbl1.config(text="ولتاژ (V):")
            self.lbl2.config(text="مقاومت (Ω):")
        else:
            self.lbl1.config(text="ولتاژ (V):")
            self.lbl2.config(text="جریان (A):")
        self.result_var.set("")
        self.entry1.focus_set()

    def _read_float(self, var, name: str) -> float:
        text = var.get().strip()
        if not text:
            raise ValueError(f"مقدار «{name}» را وارد کن.")
        try:
            return float(text.replace(",", ""))
        except ValueError:
            raise ValueError(f"مقدار «{name}» باید عدد باشد (مثلاً 12.5).")

    def calculate(self) -> None:
        try:
            mode = self.mode_var.get()
            if mode == "V":
                i = self._read_float(self.f1_var, "جریان")
                r = self._read_float(self.f2_var, "مقاومت")
                v = ohm.calc_voltage(i, r)
                self.result_var.set(f"V = {v:.2f}  ولت")
                self.app.set_status(f"ولتاژ محاسبه شد: {v:.2f} V")
            elif mode == "I":
                v = self._read_float(self.f1_var, "ولتاژ")
                r = self._read_float(self.f2_var, "مقاومت")
                i = ohm.calc_current(v, r)
                self.result_var.set(f"I = {i:.4f}  آمپر")
                self.app.set_status(f"جریان محاسبه شد: {i:.4f} A")
            else:
                v = self._read_float(self.f1_var, "ولتاژ")
                i = self._read_float(self.f2_var, "جریان")
                r = ohm.calc_resistance(v, i)
                self.result_var.set(f"R = {r:.2f}  اهم")
                self.app.set_status(f"مقاومت محاسبه شد: {r:.2f} Ω")
        except ValueError as e:
            self.result_var.set("")
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            self.result_var.set("")
            messagebox.showerror("خطای غیرمنتظره", str(e))

    def clear(self) -> None:
        self.f1_var.set("")
        self.f2_var.set("")
        self.result_var.set("")
        self.entry1.focus_set()