"""تب تبدیل ستاره ↔ مثلث — با اسکرول."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import star_delta
from electrocalc.ui.scrollable_frame import ScrollableFrame


class StarDeltaTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app

        self.mode_var = StringVar(master=self, value="Y_to_D")
        self.r1_var = StringVar(master=self, value="")
        self.r2_var = StringVar(master=self, value="")
        self.r3_var = StringVar(master=self, value="")
        self.res1_var = StringVar(master=self, value="")
        self.res2_var = StringVar(master=self, value="")
        self.res3_var = StringVar(master=self, value="")

        self.build_ui()

    def build_ui(self):
        parent = self.inner

        ttk.Label(parent, text="🔺  تبدیل ستاره ↔ مثلث",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))

        ttk.Label(parent,
                  text="تبدیل مقاومت‌ها بین آرایش ستاره (Y) و مثلث (Δ)",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 18))

        # ===== حالت =====
        mode_box = ttk.LabelFrame(parent, text="حالت تبدیل", padding=14)
        mode_box.pack(fill="x", pady=(0, 14))

        ttk.Radiobutton(
            mode_box,
            text="🔺 ← ⭐   ستاره به مثلث   (Y → Δ)",
            value="Y_to_D",
            variable=self.mode_var,
            command=self._on_mode_change,
        ).pack(anchor="w", pady=4)

        ttk.Radiobutton(
            mode_box,
            text="⭐ ← 🔺   مثلث به ستاره   (Δ → Y)",
            value="D_to_Y",
            variable=self.mode_var,
            command=self._on_mode_change,
        ).pack(anchor="w", pady=4)

        # ===== ورودی‌ها =====
        self.input_box = ttk.LabelFrame(parent, text="ورودی‌ها", padding=14)
        self.input_box.pack(fill="x", pady=(0, 14))

        self.lbl1 = ttk.Label(self.input_box, text="R_A (Ω):",
                              font=C.FONT_BODY)
        self.lbl2 = ttk.Label(self.input_box, text="R_B (Ω):",
                              font=C.FONT_BODY)
        self.lbl3 = ttk.Label(self.input_box, text="R_C (Ω):",
                              font=C.FONT_BODY)

        ttk.Entry(self.input_box, textvariable=self.r1_var,
                  width=20).grid(row=0, column=1, sticky="w", pady=6)
        ttk.Entry(self.input_box, textvariable=self.r2_var,
                  width=20).grid(row=1, column=1, sticky="w", pady=6)
        ttk.Entry(self.input_box, textvariable=self.r3_var,
                  width=20).grid(row=2, column=1, sticky="w", pady=6)

        self.lbl1.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.lbl2.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        self.lbl3.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=6)

        # ===== دکمه‌ها =====
        btn = ttk.Frame(parent)
        btn.pack(fill="x", pady=(0, 14))
        ttk.Button(btn, text="محاسبه", command=self.calculate).pack(side="left")
        ttk.Button(btn, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        # ===== نتایج =====
        res_box = ttk.LabelFrame(parent, text="نتیجه", padding=14)
        res_box.pack(fill="x")

        ttk.Label(res_box, text="R₁:", font=C.FONT_BODY).grid(
            row=0, column=0, sticky="w", pady=6)
        ttk.Label(res_box, textvariable=self.res1_var,
                  font=C.FONT_RESULT, foreground=C.COLOR_SUCCESS).grid(
            row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(res_box, text="R₂:", font=C.FONT_BODY).grid(
            row=1, column=0, sticky="w", pady=6)
        ttk.Label(res_box, textvariable=self.res2_var,
                  font=C.FONT_RESULT, foreground=C.COLOR_ACCENT).grid(
            row=1, column=1, sticky="w", padx=(8, 0))

        ttk.Label(res_box, text="R₃:", font=C.FONT_BODY).grid(
            row=2, column=0, sticky="w", pady=6)
        ttk.Label(res_box, textvariable=self.res3_var,
                  font=C.FONT_RESULT, foreground=C.COLOR_HEADER_BG).grid(
            row=2, column=1, sticky="w", padx=(8, 0))

        # راهنما
        ttk.Label(parent,
                  text="ℹ️  در هر دو آرایش، سه مقاومت وجود دارد. "
                       "با این ابزار می‌توانید بینشان تبدیل کنید.",
                  font=C.FONT_SMALL,
                  foreground=C.COLOR_MUTED,
                  wraplength=700).pack(anchor="w", pady=(15, 0))

        self._on_mode_change()

    def _on_mode_change(self):
        mode = self.mode_var.get()
        if mode == "Y_to_D":
            self.lbl1.config(text="R_A (Ω):")
            self.lbl2.config(text="R_B (Ω):")
            self.lbl3.config(text="R_C (Ω):")
        else:
            self.lbl1.config(text="R_AB (Ω):")
            self.lbl2.config(text="R_BC (Ω):")
            self.lbl3.config(text="R_CA (Ω):")

        self.clear_results()

    def _read_float(self, var, name):
        text = var.get().strip()
        if not text:
            raise ValueError(f"مقدار «{name}» را وارد کن.")
        try:
            v = float(text.replace(",", ""))
        except ValueError:
            raise ValueError(f"مقدار «{name}» باید عدد باشد.")
        if v <= 0:
            raise ValueError(f"مقدار «{name}» باید بزرگ‌تر از صفر باشد.")
        return v

    def calculate(self):
        try:
            mode = self.mode_var.get()

            if mode == "Y_to_D":
                ra = self._read_float(self.r1_var, "R_A")
                rb = self._read_float(self.r2_var, "R_B")
                rc = self._read_float(self.r3_var, "R_C")

                result = star_delta.star_to_delta(ra, rb, rc)
                self.res1_var.set(f"R_AB = {result.r_ab:.4f}  Ω")
                self.res2_var.set(f"R_BC = {result.r_bc:.4f}  Ω")
                self.res3_var.set(f"R_CA = {result.r_ca:.4f}  Ω")
                self.app.set_status("تبدیل ستاره به مثلث انجام شد")
            else:
                rab = self._read_float(self.r1_var, "R_AB")
                rbc = self._read_float(self.r2_var, "R_BC")
                rca = self._read_float(self.r3_var, "R_CA")

                result = star_delta.delta_to_star(rab, rbc, rca)
                self.res1_var.set(f"R_A = {result.r_a:.4f}  Ω")
                self.res2_var.set(f"R_B = {result.r_b:.4f}  Ω")
                self.res3_var.set(f"R_C = {result.r_c:.4f}  Ω")
                self.app.set_status("تبدیل مثلث به ستاره انجام شد")

        except ValueError as e:
            self.clear_results()
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            self.clear_results()
            messagebox.showerror("خطای غیرمنتظره", str(e))

    def clear(self):
        self.r1_var.set("")
        self.r2_var.set("")
        self.r3_var.set("")
        self.clear_results()

    def clear_results(self):
        self.res1_var.set("")
        self.res2_var.set("")
        self.res3_var.set("")