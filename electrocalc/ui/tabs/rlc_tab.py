"""تب جامع مدارهای RLC — همه ۸ مدار."""

from tkinter import ttk, messagebox, StringVar
import tkinter as tk

from electrocalc.config import constants as C
from electrocalc.core import rlc
from electrocalc.ui.scrollable_frame import ScrollableFrame


UNITS = {
    "H": 1.0, "mH": 1e-3, "µH": 1e-6,
    "F": 1.0, "mF": 1e-3, "µF": 1e-6, "nF": 1e-9, "pF": 1e-12,
    "Hz": 1.0, "kHz": 1e3,
}


CIRCUITS = [
    ("RL_s", "RL سری", "مقاومت + سلف"),
    ("RC_s", "RC سری", "مقاومت + خازن"),
    ("LC_s", "LC سری", "سلف + خازن"),
    ("RLC_s", "RLC سری", "مقاومت + سلف + خازن"),
    ("RL_p", "RL موازی", "مقاومت + سلف موازی"),
    ("RC_p", "RC موازی", "مقاومت + خازن موازی"),
    ("LC_p", "LC موازی", "سلف + خازن موازی"),
    ("RLC_p", "RLC موازی", "مقاومت + سلف + خازن موازی"),
]


class RLCTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.circuit = StringVar(master=self, value="RLC_s")

        # ورودی‌ها
        self.voltage_var = StringVar(master=self, value="220")
        self.resistance_var = StringVar(master=self, value="")
        self.inductance_var = StringVar(master=self, value="")
        self.l_unit = StringVar(master=self, value="mH")
        self.capacitance_var = StringVar(master=self, value="")
        self.c_unit = StringVar(master=self, value="µF")
        self.frequency_var = StringVar(master=self, value="50")
        self.f_unit = StringVar(master=self, value="Hz")

        # نتایج
        self.res_xl = StringVar(master=self, value="")
        self.res_xc = StringVar(master=self, value="")
        self.res_z = StringVar(master=self, value="")
        self.res_phase = StringVar(master=self, value="")
        self.res_pf = StringVar(master=self, value="")
        self.res_sin = StringVar(master=self, value="")
        self.res_tan = StringVar(master=self, value="")
        self.res_it = StringVar(master=self, value="")
        self.res_ir = StringVar(master=self, value="")
        self.res_il = StringVar(master=self, value="")
        self.res_ic = StringVar(master=self, value="")
        self.res_vr = StringVar(master=self, value="")
        self.res_vl = StringVar(master=self, value="")
        self.res_vc = StringVar(master=self, value="")
        self.res_p = StringVar(master=self, value="")
        self.res_q = StringVar(master=self, value="")
        self.res_s = StringVar(master=self, value="")
        self.res_nature = StringVar(master=self, value="")
        self.res_note = StringVar(master=self, value="")

        # رزونانس
        self.f0_res = StringVar(master=self, value="")
        self.q_res = StringVar(master=self, value="")
        self.bw_res = StringVar(master=self, value="")

        self.build_ui()

    def build_ui(self):
        p = self.inner

        ttk.Label(p, text="⚡  ماشین حساب جامع RLC",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p,
                  text="همه مدارهای RL، RC، LC، RLC — سری و موازی",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 18))

        # ===== انتخاب مدار =====
        type_box = ttk.LabelFrame(p, text="🎯  نوع مدار", padding=14)
        type_box.pack(fill="x", pady=(0, 14))

        grid_frame = ttk.Frame(type_box)
        grid_frame.pack(fill="x")

        for i, (key, name, desc) in enumerate(CIRCUITS):
            row = i // 4
            col = i % 4
            rb = ttk.Radiobutton(
                grid_frame, text=f"{name}",
                value=key, variable=self.circuit,
                command=self._on_circuit_change,
            )
            rb.grid(row=row, column=col, sticky="w", padx=5, pady=5)

        # ===== ورودی‌ها =====
        self.input_box = ttk.LabelFrame(p, text="📥  ورودی‌ها", padding=14)
        self.input_box.pack(fill="x", pady=(0, 14))

        # ولتاژ
        ttk.Label(self.input_box, text="ولتاژ (V):",
                  font=C.FONT_BODY).grid(row=0, column=0,
                                          sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(self.input_box, textvariable=self.voltage_var,
                  width=15).grid(row=0, column=1, sticky="w", pady=5)

        # مقاومت
        self.lbl_r = ttk.Label(self.input_box, text="مقاومت R (Ω):",
                                font=C.FONT_BODY)
        self.lbl_r.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)
        self.ent_r = ttk.Entry(self.input_box, textvariable=self.resistance_var,
                                width=15)
        self.ent_r.grid(row=1, column=1, sticky="w", pady=5)

        # سلف
        self.lbl_l = ttk.Label(self.input_box, text="سلف L:",
                                font=C.FONT_BODY)
        self.lbl_l.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        self.frame_l = ttk.Frame(self.input_box)
        self.frame_l.grid(row=2, column=1, sticky="w", pady=5)
        self.ent_l = ttk.Entry(self.frame_l, textvariable=self.inductance_var,
                                width=10)
        self.ent_l.pack(side="right", padx=(0, 5))
        ttk.Combobox(self.frame_l, textvariable=self.l_unit,
                      values=["H", "mH", "µH"],
                      state="readonly", width=5).pack(side="right")

        # خازن
        self.lbl_c = ttk.Label(self.input_box, text="خازن C:",
                                font=C.FONT_BODY)
        self.lbl_c.grid(row=3, column=0, sticky="w", padx=(0, 8), pady=5)
        self.frame_c = ttk.Frame(self.input_box)
        self.frame_c.grid(row=3, column=1, sticky="w", pady=5)
        self.ent_c = ttk.Entry(self.frame_c, textvariable=self.capacitance_var,
                                width=10)
        self.ent_c.pack(side="right", padx=(0, 5))
        ttk.Combobox(self.frame_c, textvariable=self.c_unit,
                      values=["F", "mF", "µF", "nF", "pF"],
                      state="readonly", width=5).pack(side="right")

        # فرکانس
        ttk.Label(self.input_box, text="فرکانس f:",
                  font=C.FONT_BODY).grid(row=4, column=0,
                                          sticky="w", padx=(0, 8), pady=5)
        f_frame = ttk.Frame(self.input_box)
        f_frame.grid(row=4, column=1, sticky="w", pady=5)
        ttk.Entry(f_frame, textvariable=self.frequency_var,
                  width=10).pack(side="right", padx=(0, 5))
        ttk.Combobox(f_frame, textvariable=self.f_unit,
                      values=["Hz", "kHz"],
                      state="readonly", width=5).pack(side="right")

        # دکمه‌ها
        btn_box = ttk.Frame(p)
        btn_box.pack(fill="x", pady=(0, 14))
        ttk.Button(btn_box, text="🧮 محاسبه",
                   command=self.calculate).pack(side="left", ipadx=20)
        ttk.Button(btn_box, text="🗑 پاک کردن",
                   command=self.clear).pack(side="left", padx=8)
        ttk.Button(btn_box, text="⚡ محاسبه رزونانس",
                   command=self.calc_resonance).pack(side="left")

        # ===== نتایج =====
        res_box = ttk.LabelFrame(p, text="📊  نتایج", padding=14)
        res_box.pack(fill="x", pady=(0, 14))

        right_col = ttk.Frame(res_box)
        right_col.pack(side="right", fill="both", expand=True, padx=5)

        left_col = ttk.Frame(res_box)
        left_col.pack(side="right", fill="both", expand=True, padx=5)

        # --- ستون راست ---
        ttk.Label(right_col, text="🎯  امپدانس و جریان",
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="e", pady=(0, 8))

        right_items = [
            ("راکتانس سلفی XL:", self.res_xl, C.COLOR_ACCENT),
            ("راکتانس خازنی XC:", self.res_xc, C.COLOR_HEADER_BG),
            ("امپدانس Z:", self.res_z, C.COLOR_SUCCESS),
            ("زاویه فاز φ:", self.res_phase, C.COLOR_TEXT),
            ("cos φ:", self.res_pf, C.COLOR_ACCENT),
            ("sin φ:", self.res_sin, C.COLOR_ACCENT),
            ("tan φ:", self.res_tan, C.COLOR_ACCENT),
            ("— جریان‌ها —", None, None),
            ("جریان کل I:", self.res_it, C.COLOR_DANGER),
            ("جریان R (IR):", self.res_ir, C.COLOR_TEXT),
            ("جریان L (IL):", self.res_il, C.COLOR_TEXT),
            ("جریان C (IC):", self.res_ic, C.COLOR_TEXT),
        ]

        for label, var, color in right_items:
            if var is None:
                ttk.Label(right_col, text=label,
                          font=C.FONT_SMALL,
                          foreground=C.COLOR_MUTED).pack(anchor="e",
                                                          pady=(8, 2))
                continue
            row = ttk.Frame(right_col)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, font=C.FONT_BODY,
                      anchor="e").pack(side="right")
            ttk.Label(row, textvariable=var,
                      font=C.FONT_RESULT,
                      foreground=color).pack(side="right", padx=(0, 8))

        # --- ستون چپ ---
        ttk.Label(left_col, text="⚡  ولتاژ و توان",
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="e", pady=(0, 8))

        left_items = [
            ("ولتاژ R (VR):", self.res_vr, C.COLOR_TEXT),
            ("ولتاژ L (VL):", self.res_vl, C.COLOR_TEXT),
            ("ولتاژ C (VC):", self.res_vc, C.COLOR_TEXT),
            ("— توان‌ها —", None, None),
            ("توان اکتیو P:", self.res_p, C.COLOR_SUCCESS),
            ("توان راکتیو Q:", self.res_q, C.COLOR_ACCENT),
            ("توان ظاهری S:", self.res_s, C.COLOR_HEADER_BG),
            ("— وضعیت —", None, None),
            ("نوع مدار:", self.res_nature, C.COLOR_MUTED),
        ]

        for label, var, color in left_items:
            if var is None:
                ttk.Label(left_col, text=label,
                          font=C.FONT_SMALL,
                          foreground=C.COLOR_MUTED).pack(anchor="e",
                                                          pady=(8, 2))
                continue
            row = ttk.Frame(left_col)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, font=C.FONT_BODY,
                      anchor="e").pack(side="right")
            ttk.Label(row, textvariable=var,
                      font=C.FONT_RESULT,
                      foreground=color).pack(side="right", padx=(0, 8))

        # یادداشت
        note_frame = ttk.Frame(res_box)
        note_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(note_frame, textvariable=self.res_note,
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_DANGER,
                  anchor="e").pack(fill="x")

        # ===== رزونانس =====
        res_box2 = ttk.LabelFrame(p, text="🎯  محاسبات رزونانس", padding=14)
        res_box2.pack(fill="x", pady=(0, 14))

        ttk.Label(res_box2,
                  text="(از L و C فعلی استفاده می‌کند)",
                  font=C.FONT_SMALL,
                  foreground=C.COLOR_MUTED,
                  anchor="e").pack(anchor="e", pady=(0, 8))

        for label, var, color in [
            ("فرکانس رزونانس f₀:", self.f0_res, C.COLOR_SUCCESS),
            ("ضریب کیفیت Q:", self.q_res, C.COLOR_ACCENT),
            ("پهنای باند BW:", self.bw_res, C.COLOR_HEADER_BG),
        ]:
            row = ttk.Frame(res_box2)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, font=C.FONT_BODY,
                      anchor="e").pack(side="right")
            ttk.Label(row, textvariable=var,
                      font=C.FONT_RESULT,
                      foreground=color).pack(side="right", padx=(0, 8))

        # ===== فرمول‌ها =====
        formulas = ttk.LabelFrame(p, text="📐  فرمول‌ها", padding=12)
        formulas.pack(fill="x")

        text = (
            "🔹  XL = 2πfL\n"
            "🔹  XC = 1/(2πfC)\n"
            "🔹  سری:  Z = √(R² + (XL−XC)²)\n"
            "🔹  موازی:  Z = V / √(IR² + (IL−IC)²)\n"
            "🔹  فاز:  φ = atan((XL−XC)/R)\n"
            "🔹  رزونانس سری:  f₀ = 1/(2π√LC) ، Z = R\n"
            "🔹  رزونانس موازی:  Z = ∞ ، جریان کل = 0\n"
            "🔹  ضریب کیفیت:  Q = (1/R)·√(L/C)\n"
            "🔹  پهنای باند:  BW = f₀/Q"
        )
        ttk.Label(formulas, text=text,
                  font=("Consolas", 9),
                  foreground=C.COLOR_MUTED,
                  justify="right").pack(anchor="e", fill="x")

        self._on_circuit_change()

    def _on_circuit_change(self):
        c = self.circuit.get()

        needs_r = c.startswith("RL") or c.startswith("RC") or c.startswith("RLC")
        needs_l = "L" in c
        needs_c = "C" in c

        if needs_r:
            self.ent_r.config(state="normal")
            self.lbl_r.config(foreground=C.COLOR_TEXT)
        else:
            self.resistance_var.set("")
            self.ent_r.config(state="disabled")
            self.lbl_r.config(foreground=C.COLOR_MUTED)

        if needs_l:
            self.ent_l.config(state="normal")
            self.lbl_l.config(foreground=C.COLOR_TEXT)
        else:
            self.inductance_var.set("")
            self.ent_l.config(state="disabled")
            self.lbl_l.config(foreground=C.COLOR_MUTED)

        if needs_c:
            self.ent_c.config(state="normal")
            self.lbl_c.config(foreground=C.COLOR_TEXT)
        else:
            self.capacitance_var.set("")
            self.ent_c.config(state="disabled")
            self.lbl_c.config(foreground=C.COLOR_MUTED)

        self.clear_results()

    def _read_float(self, var, name, allow_zero=False):
        text = var.get().strip()
        if not text:
            if allow_zero:
                return 0.0
            raise ValueError(f"مقدار «{name}» را وارد کن.")
        try:
            v = float(text.replace(",", ""))
            if v < 0 or (v == 0 and not allow_zero):
                raise ValueError
            return v
        except ValueError:
            raise ValueError(f"مقدار «{name}» باید عدد مثبت باشد.")

    def _to_base(self, value, unit):
        return value * UNITS.get(unit, 1.0)

    def calculate(self):
        try:
            c = self.circuit.get()
            voltage = self._read_float(self.voltage_var, "ولتاژ")

            resistance = 0
            if not self.ent_r.cget("state") == "disabled":
                resistance = self._read_float(self.resistance_var,
                                               "مقاومت", allow_zero=True)

            inductance = 0
            if not self.ent_l.cget("state") == "disabled":
                l_val = self._read_float(self.inductance_var, "سلف",
                                           allow_zero=True)
                inductance = self._to_base(l_val, self.l_unit.get())

            capacitance = 0
            if not self.ent_c.cget("state") == "disabled":
                c_val = self._read_float(self.capacitance_var, "خازن",
                                           allow_zero=True)
                capacitance = self._to_base(c_val, self.c_unit.get())

            freq_val = self._read_float(self.frequency_var, "فرکانس")
            frequency = self._to_base(freq_val, self.f_unit.get())

            if c == "RL_s":
                r = rlc.calc_series_rl(voltage, resistance,
                                         inductance, frequency)
            elif c == "RC_s":
                r = rlc.calc_series_rc(voltage, resistance,
                                         capacitance, frequency)
            elif c == "LC_s":
                r = rlc.calc_series_lc(voltage, inductance,
                                         capacitance, frequency)
            elif c == "RLC_s":
                r = rlc.calc_series_rlc(voltage, resistance,
                                          inductance, capacitance, frequency)
            elif c == "RL_p":
                r = rlc.calc_parallel_rl(voltage, resistance,
                                           inductance, frequency)
            elif c == "RC_p":
                r = rlc.calc_parallel_rc(voltage, resistance,
                                           capacitance, frequency)
            elif c == "LC_p":
                r = rlc.calc_parallel_lc(voltage, inductance,
                                           capacitance, frequency)
            elif c == "RLC_p":
                r = rlc.calc_parallel_rlc(voltage, resistance,
                                            inductance, capacitance, frequency)
            else:
                raise ValueError("نوع مدار نامعتبر")

            self._show_result(r)
            self.app.set_status(f"محاسبه {r.circuit_type} {r.topology} انجام شد")

        except ValueError as e:
            self.clear_results()
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            self.clear_results()
            messagebox.showerror("خطای غیرمنتظره", str(e))

    def _show_result(self, r):
        self.res_xl.set(f"{r.xl:,.4f}  Ω" if r.xl > 0 else "—")
        self.res_xc.set(f"{r.xc:,.4f}  Ω" if r.xc > 0 else "—")

        if r.z == float('inf'):
            self.res_z.set("∞  (باز)")
        elif r.z == 0:
            self.res_z.set("0  (اتصال کوتاه)")
        else:
            self.res_z.set(f"{r.z:,.4f}  Ω")

        self.res_phase.set(f"{r.phase_deg:+.2f}°")
        self.res_pf.set(f"{r.power_factor:.4f}")
        self.res_sin.set(f"{r.sin_phi:+.4f}")
        self.res_tan.set(f"{r.tan_phi:+.4f}")

        if r.total_current == float('inf'):
            self.res_it.set("∞  A")
        else:
            self.res_it.set(f"{r.total_current:,.4f}  A")
        self.res_ir.set(f"{r.current_r:,.4f}  A" if r.current_r > 0 else "—")
        self.res_il.set(f"{r.current_l:,.4f}  A" if r.current_l > 0 else "—")
        self.res_ic.set(f"{r.current_c:,.4f}  A" if r.current_c > 0 else "—")

        self.res_vr.set(f"{r.voltage_r:,.4f}  V" if r.voltage_r > 0 else "—")
        self.res_vl.set(f"{r.voltage_l:,.4f}  V" if r.voltage_l > 0 else "—")
        self.res_vc.set(f"{r.voltage_c:,.4f}  V" if r.voltage_c > 0 else "—")

        self.res_p.set(f"{r.p:,.4f}  W")
        self.res_q.set(f"{r.q:,.4f}  VAR")
        self.res_s.set(f"{r.s:,.4f}  VA")

        topo_fa = "سری" if r.topology == "series" else "موازی"
        nature = "القایی" if r.is_inductive else "خازنی"
        if abs(r.power_factor) < 0.01:
            nature = "راکتیو خالص"

        if r.is_resonance:
            nature = "🎯 رزونانس"
        self.res_nature.set(f"{r.circuit_type} {topo_fa} — {nature}")
        self.res_note.set(r.note)

    def calc_resonance(self):
        try:
            l_val = self._read_float(self.inductance_var, "سلف")
            inductance = self._to_base(l_val, self.l_unit.get())

            c_val = self._read_float(self.capacitance_var, "خازن")
            capacitance = self._to_base(c_val, self.c_unit.get())

            f0 = rlc.calc_resonance_frequency(inductance, capacitance)
            self.f0_res.set(f"{f0:,.4f}  Hz")

            r_text = self.resistance_var.get().strip()
            if r_text:
                try:
                    resistance = float(r_text.replace(",", ""))
                    if resistance > 0:
                        q = rlc.calc_quality_factor(inductance,
                                                      capacitance, resistance)
                        bw = rlc.calc_bandwidth(f0, q)
                        self.q_res.set(f"{q:,.4f}")
                        self.bw_res.set(f"{bw:,.4f}  Hz")
                    else:
                        self.q_res.set("—")
                        self.bw_res.set("—")
                except Exception:
                    self.q_res.set("—")
                    self.bw_res.set("—")
            else:
                self.q_res.set("—")
                self.bw_res.set("—")

            self.app.set_status(f"رزونانس در {f0:.2f} Hz")

        except ValueError as e:
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            messagebox.showerror("خطای غیرمنتظره", str(e))

    def clear(self):
        if not self.ent_r.cget("state") == "disabled":
            self.resistance_var.set("")
        if not self.ent_l.cget("state") == "disabled":
            self.inductance_var.set("")
        if not self.ent_c.cget("state") == "disabled":
            self.capacitance_var.set("")
        self.clear_results()

    def clear_results(self):
        for var in (self.res_xl, self.res_xc, self.res_z,
                     self.res_phase, self.res_pf, self.res_sin, self.res_tan,
                     self.res_it, self.res_ir, self.res_il, self.res_ic,
                     self.res_vr, self.res_vl, self.res_vc,
                     self.res_p, self.res_q, self.res_s,
                     self.res_nature, self.res_note,
                     self.f0_res, self.q_res, self.bw_res):
            var.set("")