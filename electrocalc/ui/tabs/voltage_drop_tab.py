"""تب افت ولتاژ کابل — با اسکرول."""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import voltage_drop


class VoltageDropTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.voltage_var = StringVar(master=self, value="220")
        self.current_var = StringVar(master=self, value="")
        self.length_var = StringVar(master=self, value="")
        self.cross_var = StringVar(master=self, value="")
        self.material_var = StringVar(master=self, value="copper")
        self.phase_var = StringVar(master=self, value="1phase")
        self.cos_var = StringVar(master=self, value="1.0")
        self.result_drop = StringVar(master=self, value="")
        self.result_percent = StringVar(master=self, value="")
        self.result_end = StringVar(master=self, value="")
        self._build_scrollable()
        self.build_ui()

    def _build_scrollable(self):
        """ساخت قاب قابل اسکرول."""
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                   command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas, padding=20)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_config)
        self.canvas.bind("<Configure>", self._on_canvas_config)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_config(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_config(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def build_ui(self) -> None:
        parent = self.inner

        ttk.Label(parent, text="⚡  افت ولتاژ کابل", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 4))
        ttk.Label(parent, text="محاسبه افت ولتاژ در طول کابل",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 12))

        # نوع سیستم و جنس هادی کنار هم
        top_row = ttk.Frame(parent)
        top_row.pack(fill="x", pady=(0, 10))

        sys_box = ttk.LabelFrame(top_row, text="نوع سیستم", padding=10)
        sys_box.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ttk.Radiobutton(sys_box, text="تک‌فاز", value="1phase",
                        variable=self.phase_var).pack(anchor="w", pady=2)
        ttk.Radiobutton(sys_box, text="سه‌فاز", value="3phase",
                        variable=self.phase_var).pack(anchor="w", pady=2)

        mat_box = ttk.LabelFrame(top_row, text="جنس هادی", padding=10)
        mat_box.pack(side="right", fill="both", expand=True, padx=(0, 5))
        ttk.Radiobutton(mat_box, text="مس (Copper)", value="copper",
                        variable=self.material_var).pack(anchor="w", pady=2)
        ttk.Radiobutton(mat_box, text="آلومینیوم", value="aluminum",
                        variable=self.material_var).pack(anchor="w", pady=2)

        # ورودی‌ها
        inp = ttk.LabelFrame(parent, text="ورودی‌ها", padding=10)
        inp.pack(fill="x", pady=(0, 10))

        rows = [
            ("ولتاژ (V):", self.voltage_var),
            ("جریان (A):", self.current_var),
            ("طول کابل (m):", self.length_var),
            ("سطح مقطع (mm²):", self.cross_var),
            ("ضریب توان (cos φ):", self.cos_var),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(inp, text=label, font=C.FONT_BODY).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=4)
            ttk.Entry(inp, textvariable=var, width=20).grid(
                row=i, column=1, sticky="w", pady=4)

        # دکمه‌ها
        btn = ttk.Frame(parent)
        btn.pack(fill="x", pady=(0, 10))
        ttk.Button(btn, text="محاسبه", command=self.calculate).pack(side="left")
        ttk.Button(btn, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        # نتایج
        res = ttk.LabelFrame(parent, text="نتیجه", padding=10)
        res.pack(fill="x")

        for i, (label, var, color) in enumerate([
            ("افت ولتاژ:", self.result_drop, C.COLOR_DANGER),
            ("درصد افت:", self.result_percent, C.COLOR_ACCENT),
            ("ولتاژ انتهای خط:", self.result_end, C.COLOR_SUCCESS),
        ]):
            ttk.Label(res, text=label, font=C.FONT_BODY).grid(
                row=i, column=0, sticky="w", pady=4)
            ttk.Label(res, textvariable=var, font=C.FONT_RESULT,
                      foreground=color).grid(row=i, column=1, sticky="w",
                                              padx=(8, 0), pady=4)

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
            v = self._read_float(self.voltage_var, "ولتاژ")
            i = self._read_float(self.current_var, "جریان")
            length = self._read_float(self.length_var, "طول")
            cross = self._read_float(self.cross_var, "سطح مقطع")
            cos_phi = self._read_float(self.cos_var, "ضریب توان")

            res = voltage_drop.calc_voltage_drop(
                voltage=v, current=i, length=length, cross_section=cross,
                material=self.material_var.get(),
                three_phase=(self.phase_var.get() == "3phase"),
                cos_phi=cos_phi,
            )

            self.result_drop.set(f"{res.drop_v:.2f}  V")
            self.result_percent.set(f"{res.drop_percent:.2f}  %")
            self.result_end.set(f"{res.end_voltage:.2f}  V")
            self.app.set_status(
                f"افت ولتاژ: {res.drop_v:.2f} V ({res.drop_percent:.2f}%)")
        except ValueError as e:
            self.clear_results()
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            self.clear_results()
            messagebox.showerror("خطای غیرمنتظره", str(e))

    def clear(self) -> None:
        self.voltage_var.set("220")
        self.current_var.set("")
        self.length_var.set("")
        self.cross_var.set("")
        self.cos_var.set("1.0")
        self.clear_results()

    def clear_results(self) -> None:
        self.result_drop.set("")
        self.result_percent.set("")
        self.result_end.set("")