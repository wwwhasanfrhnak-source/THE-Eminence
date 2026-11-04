"""تب موتور پیشرفته — با اسکرول."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import motor_advanced as ma
from electrocalc.ui.scrollable_frame import ScrollableFrame


class MotorAdvancedTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app

        # متغیرها
        self.freq_var = StringVar(master=self, value="50")
        self.poles_var = StringVar(master=self, value="4")
        self.rpm_var = StringVar(master=self, value="")
        self.nominal_var = StringVar(master=self, value="")
        self.starter_var = StringVar(master=self, value="DOL")
        self._starter_key = "DOL"

        # نتیجه
        self.res_ns_var = StringVar(master=self, value="")
        self.res_rpm_var = StringVar(master=self, value="")
        self.res_slip_var = StringVar(master=self, value="")
        self.res_i_start_var = StringVar(master=self, value="")
        self.res_factor_var = StringVar(master=self, value="")
        self.res_torque_var = StringVar(master=self, value="")

        self.build_ui()

    def build_ui(self):
        parent = self.inner

        # عنوان
        ttk.Label(parent, text="⚙️  محاسبات پیشرفته موتور",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))

        ttk.Label(parent,
                  text="سرعت سنکرون، لغزش، دور و جریان راه‌انداز",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 18))

        # ===== بخش ۱: سرعت و لغزش =====
        sec1 = ttk.LabelFrame(parent, text="🔵  ۱)  سرعت سنکرون و لغزش",
                              padding=14)
        sec1.pack(fill="x", pady=(0, 12))

        # فرکانس
        ttk.Label(sec1, text="فرکانس (Hz):",
                  font=C.FONT_BODY).grid(row=0, column=0,
                                          sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(sec1, textvariable=self.freq_var, width=15).grid(
            row=0, column=1, sticky="w", pady=5)

        # تعداد قطب
        ttk.Label(sec1, text="تعداد قطب:",
                  font=C.FONT_BODY).grid(row=1, column=0,
                                          sticky="w", padx=(0, 8), pady=5)
        poles_combo = ttk.Combobox(
            sec1, textvariable=self.poles_var,
            values=[str(p) for p in ma.POLES],
            state="readonly", width=13,
        )
        poles_combo.grid(row=1, column=1, sticky="w", pady=5)
        poles_combo.current(1)

        # دور واقعی
        ttk.Label(sec1, text="دور واقعی (RPM) — اختیاری:",
                  font=C.FONT_BODY).grid(row=2, column=0,
                                          sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(sec1, textvariable=self.rpm_var, width=15).grid(
            row=2, column=1, sticky="w", pady=5)

        ttk.Label(sec1,
                  text="(اگه دور واقعی رو بدی، لغزش دقیق حساب می‌شه — "
                       "وگرنه لغزش معمول ۳٪ فرض می‌شه)",
                  font=C.FONT_SMALL,
                  foreground=C.COLOR_MUTED).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(3, 8))

        ttk.Button(sec1, text="محاسبه سرعت",
                   command=self.calc_speed).grid(
            row=4, column=0, columnspan=2, sticky="w", ipadx=15)

        # نتایج سرعت
        res1 = ttk.Frame(sec1)
        res1.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

        ttk.Label(res1, text="سرعت سنکرون:",
                  font=C.FONT_BODY).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Label(res1, textvariable=self.res_ns_var,
                  font=C.FONT_RESULT,
                  foreground=C.COLOR_SUCCESS).grid(row=0, column=1,
                                                    sticky="w", padx=(8, 0))

        ttk.Label(res1, text="دور واقعی:",
                  font=C.FONT_BODY).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Label(res1, textvariable=self.res_rpm_var,
                  font=C.FONT_RESULT,
                  foreground=C.COLOR_ACCENT).grid(row=1, column=1,
                                                   sticky="w", padx=(8, 0))

        ttk.Label(res1, text="لغزش:",
                  font=C.FONT_BODY).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Label(res1, textvariable=self.res_slip_var,
                  font=C.FONT_RESULT,
                  foreground=C.COLOR_HEADER_BG).grid(row=2, column=1,
                                                      sticky="w",
                                                      padx=(8, 0))

        # ===== بخش ۲: راه‌انداز =====
        sec2 = ttk.LabelFrame(parent, text="🟠  ۲)  جریان راه‌انداز",
                              padding=14)
        sec2.pack(fill="x", pady=(0, 12))

        ttk.Label(sec2, text="جریان نامی موتور (A):",
                  font=C.FONT_BODY).grid(row=0, column=0,
                                          sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(sec2, textvariable=self.nominal_var, width=15).grid(
            row=0, column=1, sticky="w", pady=5)

        ttk.Label(sec2, text="روش راه‌انداز:",
                  font=C.FONT_BODY).grid(row=1, column=0,
                                          sticky="w", padx=(0, 8), pady=5)

        starter_display = [v["name"] for v in ma.STARTER_FACTORS.values()]
        self._starter_map = {v["name"]: k
                              for k, v in ma.STARTER_FACTORS.items()}
        starter_combo = ttk.Combobox(
            sec2, textvariable=self.starter_var,
            values=starter_display, state="readonly", width=25,
        )
        starter_combo.grid(row=1, column=1, sticky="w", pady=5)
        starter_combo.current(0)
        starter_combo.bind("<<ComboboxSelected>>",
                            lambda e: self._set_starter_key())

        ttk.Button(sec2, text="محاسبه راه‌انداز",
                   command=self.calc_starter).grid(
            row=2, column=0, columnspan=2, sticky="w",
            pady=(10, 5), ipadx=15)

        # نتایج راه‌انداز
        res2 = ttk.Frame(sec2)
        res2.grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 0))

        ttk.Label(res2, text="جریان راه‌انداز:",
                  font=C.FONT_BODY).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Label(res2, textvariable=self.res_i_start_var,
                  font=C.FONT_RESULT,
                  foreground=C.COLOR_DANGER).grid(row=0, column=1,
                                                   sticky="w", padx=(8, 0))

        ttk.Label(res2, text="ضریب راه‌انداز:",
                  font=C.FONT_BODY).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Label(res2, textvariable=self.res_factor_var,
                  font=C.FONT_RESULT,
                  foreground=C.COLOR_ACCENT).grid(row=1, column=1,
                                                   sticky="w", padx=(8, 0))

        ttk.Label(res2, text="گشتاور راه‌انداز:",
                  font=C.FONT_BODY).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Label(res2, textvariable=self.res_torque_var,
                  font=C.FONT_RESULT,
                  foreground=C.COLOR_SUCCESS).grid(row=2, column=1,
                                                    sticky="w", padx=(8, 0))

        # ===== دکمه پاک کردن =====
        btn_box = ttk.Frame(parent)
        btn_box.pack(fill="x", pady=(0, 10))
        ttk.Button(btn_box, text="پاک کردن همه",
                   command=self.clear).pack(side="left", ipadx=15)

        # راهنما
        ttk.Label(parent,
                  text="ℹ️  فرمول سرعت سنکرون:  Ns = 120 × f / P\n"
                       "ℹ️  فرمول لغزش:  s = (Ns − Nr) / Ns × 100\n"
                       "ℹ️  ضریب راه‌انداز:  DOL = ۶ ، ستاره-مثلث = ۲",
                  font=C.FONT_SMALL,
                  foreground=C.COLOR_MUTED,
                  justify="right").pack(anchor="w", pady=(10, 0))

    def _set_starter_key(self):
        display = self.starter_var.get()
        if display in self._starter_map:
            self._starter_key = self._starter_map[display]
        else:
            self._starter_key = "DOL"

    def calc_speed(self):
        try:
            freq = self._read_float(self.freq_var, "فرکانس")
            poles = int(self.poles_var.get())

            rpm_text = self.rpm_var.get().strip()
            actual_rpm = None
            if rpm_text:
                actual_rpm = self._read_float(self.rpm_var, "دور واقعی")

            r = ma.calculate_sync_speed(freq, poles, actual_rpm)

            self.res_ns_var.set(f"{r.sync_rpm:,.2f}  RPM")
            self.res_rpm_var.set(f"{r.actual_rpm:,.2f}  RPM")
            self.res_slip_var.set(f"{r.slip_percent:.2f}  %")

            self.app.set_status(f"سرعت سنکرون: {r.sync_rpm:.0f} RPM")
        except ValueError as e:
            self._clear_speed_results()
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            self._clear_speed_results()
            messagebox.showerror("خطای غیرمنتظره", str(e))

    def calc_starter(self):
        try:
            nominal = self._read_float(self.nominal_var, "جریان نامی")
            starter_key = getattr(self, "_starter_key", "DOL")

            r = ma.calc_starting_current(nominal, starter_key)

            self.res_i_start_var.set(f"{r.starting_current:,.2f}  A")
            self.res_factor_var.set(f"{r.starting_factor:.1f}  ×")
            self.res_torque_var.set(f"{r.starting_torque_percent:.0f}  %")

            self.app.set_status(
                f"جریان راه‌انداز ({r.starter_name}): "
                f"{r.starting_current:.1f} A")
        except ValueError as e:
            self._clear_starter_results()
            messagebox.showerror("خطای ورودی", str(e))
        except Exception as e:
            self._clear_starter_results()
            messagebox.showerror("خطای غیرمنتظره", str(e))

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

    def _clear_speed_results(self):
        self.res_ns_var.set("")
        self.res_rpm_var.set("")
        self.res_slip_var.set("")

    def _clear_starter_results(self):
        self.res_i_start_var.set("")
        self.res_factor_var.set("")
        self.res_torque_var.set("")

    def clear(self):
        self.freq_var.set("50")
        self.poles_var.set("4")
        self.rpm_var.set("")
        self.nominal_var.set("")
        self.starter_var.set(ma.STARTER_FACTORS["DOL"]["name"])
        self._clear_speed_results()
        self._clear_starter_results()