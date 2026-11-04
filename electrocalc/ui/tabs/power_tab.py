"""تب محاسبه توان — رابط کاربری."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import power


class PowerTab(ttk.Frame):
    """
    تب محاسبه توان.

    کاربر این‌ها را وارد می‌کند:
      - ولتاژ (V)
      - جریان (A)
      - ضریب توان cos φ
      - نوع سیستم: تک‌فاز یا سه‌فاز

    خروجی:
      - توان اکتیو P (وات)
      - توان ظاهری S (ولت‌آمپر)
      - توان راکتیو Q (وار)
    """

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.voltage_var = StringVar(master=self, value="")
        self.current_var = StringVar(master=self, value="")
        self.cos_phi_var = StringVar(master=self, value="0.9")
        self.system_var = StringVar(master=self, value="1phase")
        self.result_p = StringVar(master=self, value="")
        self.result_s = StringVar(master=self, value="")
        self.result_q = StringVar(master=self, value="")
        self.build_ui()

    def build_ui(self) -> None:
        # ---------- عنوان ----------
        ttk.Label(
            self,
            text="⚡  محاسبه توان",
            font=C.FONT_TITLE,
            foreground=C.COLOR_HEADER_BG,
        ).pack(anchor="w", pady=(0, 6))

        ttk.Label(
            self,
            text="ولتاژ، جریان و ضریب توان را وارد کن تا هر سه نوع توان محاسبه شود.",
            font=C.FONT_BODY,
            foreground=C.COLOR_MUTED,
        ).pack(anchor="w", pady=(0, 18))

        # ---------- نوع سیستم ----------
        system_box = ttk.LabelFrame(self, text="نوع سیستم", padding=14)
        system_box.pack(fill="x", pady=(0, 14))

        ttk.Radiobutton(
            system_box,
            text="تک‌فاز  (P = V × I × cos φ)",
            value="1phase",
            variable=self.system_var,
        ).pack(anchor="w", pady=3)

        ttk.Radiobutton(
            system_box,
            text="سه‌فاز  (P = √3 × V × I × cos φ)",
            value="3phase",
            variable=self.system_var,
        ).pack(anchor="w", pady=3)

        # ---------- ورودی‌ها ----------
        input_box = ttk.LabelFrame(self, text="ورودی‌ها", padding=14)
        input_box.pack(fill="x", pady=(0, 14))

        # ولتاژ
        ttk.Label(input_box, text="ولتاژ (V):", font=C.FONT_BODY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(input_box, textvariable=self.voltage_var, width=20).grid(
            row=0, column=1, sticky="w", pady=6)

        # جریان
        ttk.Label(input_box, text="جریان (A):", font=C.FONT_BODY).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(input_box, textvariable=self.current_var, width=20).grid(
            row=1, column=1, sticky="w", pady=6)

        # cos φ
        ttk.Label(input_box, text="ضریب توان (cos φ):", font=C.FONT_BODY).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(input_box, textvariable=self.cos_phi_var, width=20).grid(
            row=2, column=1, sticky="w", pady=6)

        ttk.Label(
            input_box,
            text="مثال: 0.85 (مقدار معمول بین ۰.۸ تا ۱)",
            font=C.FONT_SMALL,
            foreground=C.COLOR_MUTED,
        ).grid(row=3, column=1, sticky="w", pady=(0, 4))

        # ---------- دکمه‌ها ----------
        btn_box = ttk.Frame(self)
        btn_box.pack(fill="x", pady=(0, 14))

        ttk.Button(btn_box, text="محاسبه", command=self.calculate).pack(side="left")
        ttk.Button(btn_box, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        # ---------- نتایج ----------
        result_box = ttk.LabelFrame(self, text="نتیجه", padding=14)
        result_box.pack(fill="x")

        # P
        ttk.Label(result_box, text="توان اکتیو (P):", font=C.FONT_BODY).grid(
            row=0, column=0, sticky="w", pady=6)
        ttk.Label(result_box, textvariable=self.result_p,
                  font=C.FONT_RESULT, foreground=C.COLOR_SUCCESS).grid(
            row=0, column=1, sticky="w", padx=(8, 0), pady=6)

        # S
        ttk.Label(result_box, text="توان ظاهری (S):", font=C.FONT_BODY).grid(
            row=1, column=0, sticky="w", pady=6)
        ttk.Label(result_box, textvariable=self.result_s,
                  font=C.FONT_RESULT, foreground=C.COLOR_HEADER_BG).grid(
            row=1, column=1, sticky="w", padx=(8, 0), pady=6)

        # Q
        ttk.Label(result_box, text="توان راکتیو (Q):", font=C.FONT_BODY).grid(
            row=2, column=0, sticky="w", pady=6)
        ttk.Label(result_box, textvariable=self.result_q,
                  font=C.FONT_RESULT, foreground=C.COLOR_ACCENT).grid(
            row=2, column=1, sticky="w", padx=(8, 0), pady=6)

    # ------------------------------------------------------------------
    def _read_float(self, var, name: str) -> float:
        text = var.get().strip()
        if not text:
            raise ValueError(f"مقدار «{name}» را وارد کن.")
        try:
            return float(text.replace(",", ""))
        except ValueError:
            raise ValueError(f"مقدار «{name}» باید عدد باشد (مثلاً 12.5).")

    # ------------------------------------------------------------------
    def calculate(self) -> None:
        try:
            v = self._read_float(self.voltage_var, "ولتاژ")
            i = self._read_float(self.current_var, "جریان")
            cos_phi = self._read_float(self.cos_phi_var, "ضریب توان")

            three_phase = (self.system_var.get() == "3phase")

            result = power.calc_power(v, i, cos_phi, three_phase)

            self.result_p.set(f"{result.p:,.2f}  W")
            self.result_s.set(f"{result.s:,.2f}  VA")
            self.result_q.set(f"{result.q:,.2f}  VAR")

            phase_text = "سه‌فاز" if three_phase else "تک‌فاز"
            self.app.set_status(
                f"توان {phase_text} محاسبه شد: P = {result.p:,.2f} W"
            )

        except ValueError as e:
            self.clear_results()
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            self.clear_results()
            messagebox.showerror("خطای غیرمنتظره", str(e))

    # ------------------------------------------------------------------
    def clear(self) -> None:
        self.voltage_var.set("")
        self.current_var.set("")
        self.cos_phi_var.set("0.9")
        self.clear_results()

    def clear_results(self) -> None:
        self.result_p.set("")
        self.result_s.set("")
        self.result_q.set("")