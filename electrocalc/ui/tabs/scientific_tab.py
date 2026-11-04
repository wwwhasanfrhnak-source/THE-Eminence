"""ماشین حساب مهندسی کامل — سبک CASIO fx."""

import math
import tkinter as tk
from tkinter import ttk

from electrocalc.config import constants as C


class ScientificTab(ttk.Frame):
    """ماشین حساب مهندسی با همه امکانات CASIO."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.palette = app.palette

        # وضعیت
        self.expression = ""
        self.last_answer = 0
        self.memory = 0
        self.angle_mode = "DEG"     # DEG | RAD | GRAD
        self.shift = False
        self.alpha = False
        self.variables = {"A": 0, "B": 0, "C": 0, "D": 0, "X": 0, "Y": 0}

        self._buttons = {}
        self._button_data = []      # (btn, normal_label, shift_label, normal_cmd, shift_cmd, kind)

        self.build_ui()
        self._bind_keys()

    # ========================================================
    # ساخت UI
    # ========================================================
    def build_ui(self):
        p = self.palette

        # ========== هدر ==========
        header = tk.Frame(self, bg=p["bg"])
        header.pack(fill="x", padx=15, pady=(15, 8))

        tk.Label(header, text="🔬  ماشین حساب مهندسی",
                 font=("Segoe UI", 16, "bold"),
                 bg=p["bg"], fg=p["h_start"],
                 anchor="e").pack(side="right")

        # اندیکاتور حالت
        ind_frame = tk.Frame(header, bg=p["bg"])
        ind_frame.pack(side="left")

        self.mode_ind = tk.Label(
            ind_frame, text="DEG",
            font=("Consolas", 9, "bold"),
            bg=p["accent"], fg="white",
            padx=8, pady=3,
        )
        self.mode_ind.pack(side="right", padx=2)

        self.shift_ind = tk.Label(
            ind_frame, text="SHIFT",
            font=("Consolas", 9, "bold"),
            bg=p["bg"], fg=p["muted"],
            padx=8, pady=3,
        )
        self.shift_ind.pack(side="right", padx=2)

        self.alpha_ind = tk.Label(
            ind_frame, text="ALPHA",
            font=("Consolas", 9, "bold"),
            bg=p["bg"], fg=p["muted"],
            padx=8, pady=3,
        )
        self.alpha_ind.pack(side="right", padx=2)

        self.mem_ind = tk.Label(
            ind_frame, text="M",
            font=("Consolas", 9, "bold"),
            bg=p["bg"], fg=p["muted"],
            padx=8, pady=3,
        )
        self.mem_ind.pack(side="right", padx=2)

        # ========== نمایشگر ==========
        disp_frame = tk.Frame(
            self, bg=p["card"],
            highlightbackground=p["border"],
            highlightthickness=2,
        )
        disp_frame.pack(fill="x", padx=15, pady=(0, 12))

        # خط وضعیت بالا
        status_row = tk.Frame(disp_frame, bg=p["card"])
        status_row.pack(fill="x", padx=15, pady=(10, 0))

        self.status_var = tk.StringVar(value="")
        tk.Label(status_row, textvariable=self.status_var,
                 font=("Consolas", 9),
                 bg=p["card"], fg=p["muted"],
                 anchor="w").pack(side="left")

        self.mem_display = tk.StringVar(value="")
        tk.Label(status_row, textvariable=self.mem_display,
                 font=("Consolas", 9, "bold"),
                 bg=p["card"], fg=p["accent"],
                 anchor="e").pack(side="right")

        # نمایشگر اصلی
        self.display_var = tk.StringVar(value="0")
        disp = tk.Entry(
            disp_frame, textvariable=self.display_var,
            font=("Consolas", 20, "bold"),
            bg=p["card"], fg=p["text"],
            relief="flat", bd=0, justify="right",
            insertbackground=p["text"],
            state="readonly", readonlybackground=p["card"],
        )
        disp.pack(fill="x", padx=15, pady=(5, 5))

        # پیش‌نمایش
        self.result_var = tk.StringVar(value="")
        tk.Label(disp_frame, textvariable=self.result_var,
                 font=("Consolas", 14),
                 bg=p["card"], fg=p["success"],
                 anchor="e", height=1).pack(fill="x", padx=15, pady=(0, 12))

        # ========== دکمه‌ها ==========
        btn_container = tk.Frame(self, bg=p["bg"])
        btn_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 7 ستون
        for c in range(7):
            btn_container.columnconfigure(c, weight=1, uniform="btn")

        self._build_buttons(btn_container)

    # ========================================================
    # دکمه‌ها
    # ========================================================
    def _build_buttons(self, parent):
        p = self.palette

        # تعریف دکمه‌ها: (row, col, normal_label, shift_label,
        #                normal_action, shift_action, kind, span)
        layout = [
            # ===== Row 0: SHIFT / ALPHA / MODE / ناوبری / DEL / AC =====
            (0, 0, "SHIFT", "SHIFT", "_shift", "_shift", "shift", 1),
            (0, 1, "ALPHA", "ALPHA", "_alpha", "_alpha", "alpha", 1),
            (0, 2, "MODE", "MODE", "_mode", "_mode", "sci", 1),
            (0, 3, "◄", "◄", "_left", "_left", "sci", 1),
            (0, 4, "►", "►", "_right", "_right", "sci", 1),
            (0, 5, "DEL", "INS", "_del", "_del", "danger", 1),
            (0, 6, "AC", "OFF", "_ac", "_ac", "danger", 1),

            # ===== Row 1: توان‌ها =====
            (1, 0, "x²", "x³", "**2", "**3", "sci", 1),
            (1, 1, "xʸ", "ˣ√y", "**", "root", "sci", 1),
            (1, 2, "√", "∛", "sqrt(", "cbrt(", "sci", 1),
            (1, 3, "1/x", "x⁻¹", "inv", "inv", "sci", 1),
            (1, 4, "x!", "Γ", "fact", "fact", "sci", 1),
            (1, 5, "log", "10ˣ", "log(", "10**", "sci", 1),
            (1, 6, "ln", "eˣ", "ln(", "e**", "sci", 1),

            # ===== Row 2: توابع مثلثاتی و ثابت‌ها =====
            (2, 0, "sin", "sin⁻¹", "sin(", "asin(", "sci", 1),
            (2, 1, "cos", "cos⁻¹", "cos(", "acos(", "sci", 1),
            (2, 2, "tan", "tan⁻¹", "tan(", "atan(", "sci", 1),
            (2, 3, "π", "e", "π", "e", "sci", 1),
            (2, 4, "(", "(", "(", "(", "sci", 1),
            (2, 5, ")", ")", ")", ")", "sci", 1),
            (2, 6, "%", "‰", "%", "%", "sci", 1),

            # ===== Row 3: حافظه + اعداد + عملیات =====
            (3, 0, "STO", "RCL", "_sto", "_rcl", "sci", 1),
            (3, 1, "EXP", "π", "E", "π", "sci", 1),
            (3, 2, ",", ",", ",", ",", "sci", 1),
            (3, 3, "7", "7", "7", "7", "num", 1),
            (3, 4, "8", "8", "8", "8", "num", 1),
            (3, 5, "9", "9", "9", "9", "num", 1),
            (3, 6, "÷", "÷", "÷", "÷", "op", 1),

            # ===== Row 4 =====
            (4, 0, "M+", "M-", "_mplus", "_mminus", "sci", 1),
            (4, 1, "MR", "MC", "_mr", "_mc", "sci", 1),
            (4, 2, "±", "(-)", "_neg", "_neg", "sci", 1),
            (4, 3, "4", "4", "4", "4", "num", 1),
            (4, 4, "5", "5", "5", "5", "num", 1),
            (4, 5, "6", "6", "6", "6", "num", 1),
            (4, 6, "×", "×", "×", "×", "op", 1),

            # ===== Row 5 =====
            (5, 0, "Ans", "Ans", "_ans", "_ans", "sci", 1),
            (5, 1, "Ran#", "π", "_rand", "π", "sci", 1),
            (5, 2, "abs", "|x|", "abs(", "abs(", "sci", 1),
            (5, 3, "1", "1", "1", "1", "num", 1),
            (5, 4, "2", "2", "2", "2", "num", 1),
            (5, 5, "3", "3", "3", "3", "num", 1),
            (5, 6, "−", "−", "−", "−", "op", 1),

            # ===== Row 6 =====
            (6, 0, "A", "D", "_varA", "_varD", "var", 1),
            (6, 1, "B", "E", "_varB", "_varE", "var", 1),
            (6, 2, "C", "F", "_varC", "_varF", "var", 1),
            (6, 3, "0", "0", "0", "0", "num", 1),
            (6, 4, ".", ".", ".", ".", "num", 1),
            (6, 5, "×10ˣ", "EXP", "E", "E", "sci", 1),
            (6, 6, "+", "+", "+", "+", "op", 1),
        ]

        for row, col, label, shift_label, action, shift_action, kind, span in layout:
            self._make_button(parent, row, col, label, shift_label,
                                action, shift_action, kind, span)

        # ===== دکمه = بزرگ (span 7) =====
        btn_frame = tk.Frame(parent, bg=p["bg"])
        btn_frame.grid(row=7, column=0, columnspan=7,
                        sticky="nsew", padx=2, pady=2)
        btn_frame.columnconfigure(0, weight=1)

        eq_btn = tk.Button(
            btn_frame, text="=",
            font=("Segoe UI", 18, "bold"),
            bg=p["success"], fg="white",
            activebackground="#0d9668",
            relief="flat", bd=0, cursor="hand2",
            command=self._evaluate,
        )
        eq_btn.pack(fill="both", expand=True, ipady=14)
        eq_btn.bind("<Enter>", lambda e: eq_btn.config(bg="#0d9668"))
        eq_btn.bind("<Leave>", lambda e: eq_btn.config(bg=p["success"]))

    def _make_button(self, parent, row, col, label, shift_label,
                     action, shift_action, kind, span=1):
        p = self.palette

        # رنگ بر اساس نوع
        if kind == "num":
            bg, fg, hover = p["card"], p["text"], p["border"]
        elif kind == "op":
            bg, fg, hover = p["accent"], "white", p["h_end"]
        elif kind == "sci":
            bg, fg, hover = p["bg"], p["text"], p["border"]
        elif kind == "shift":
            bg, fg, hover = "#f59e0b", "white", "#d97706"
        elif kind == "alpha":
            bg, fg, hover = p["danger"], "white", "#a0281c"
        elif kind == "var":
            bg, fg, hover = "#8b5cf6", "white", "#7c3aed"
        elif kind == "danger":
            bg, fg, hover = p["danger"], "white", "#a0281c"
        else:
            bg, fg, hover = p["card"], p["text"], p["border"]

        btn = tk.Button(
            parent, text=label,
            font=("Segoe UI", 10, "bold"),
            bg=bg, fg=fg,
            activebackground=hover, activeforeground=fg,
            relief="flat", bd=0, cursor="hand2",
            command=lambda: self._handle(action, shift_action),
        )
        btn.grid(row=row, column=col, columnspan=span,
                  sticky="nsew", padx=2, pady=2, ipadx=5, ipady=8)

        btn.bind("<Enter>", lambda e, b=btn, h=hover: b.config(bg=h))
        btn.bind("<Leave>", lambda e, b=btn, c=bg: b.config(bg=c))

        self._button_data.append({
            "widget": btn, "normal": label, "shift": shift_label,
            "normal_action": action, "shift_action": shift_action,
            "bg": bg,
        })

    # ========================================================
    # مدیریت دکمه
    # ========================================================
    def _handle(self, normal_action, shift_action):
        action = shift_action if self.shift else normal_action
        self._execute(action)

        # ریست SHIFT و ALPHA بعد از هر استفاده (به‌جز خودشون)
        if action not in ("_shift", "_alpha"):
            if self.shift:
                self.shift = False
                self._update_shift_display()
            if self.alpha:
                self.alpha = False
                self._update_alpha_display()

    def _execute(self, action):
        # ===== ویژه =====
        if action == "_shift":
            self.shift = not self.shift
            self._update_shift_display()
            return

        if action == "_alpha":
            self.alpha = not self.alpha
            self._update_alpha_display()
            return

        if action == "_mode":
            self._cycle_mode()
            return

        if action == "_ac":
            self.expression = ""
            self.result_var.set("")
            self._update_display()
            return

        if action == "_del":
            self.expression = self.expression[:-1]
            self._update_display()
            self._preview()
            return

        if action == "_left":
            # جابجایی: فقط حذف آخر (ساده)
            return

        if action == "_right":
            return

        if action == "_ans":
            self.expression += self._fmt(self.last_answer)
            self._refresh()
            return

        if action == "_rand":
            import random
            self.expression += str(random.randint(1, 999))
            self._refresh()
            return

        if action == "_neg":
            if self.expression:
                if self.expression.startswith("(-"):
                    self.expression = self.expression[2:]
                else:
                    self.expression = "(-" + self.expression
            self._refresh()
            return

        # ===== حافظه =====
        if action == "_mplus":
            try:
                val = self._evaluate_expr(self.expression) if self.expression else 0
                self.memory += val
                self._update_memory_display()
            except Exception:
                pass
            return

        if action == "_mminus":
            try:
                val = self._evaluate_expr(self.expression) if self.expression else 0
                self.memory -= val
                self._update_memory_display()
            except Exception:
                pass
            return

        if action == "_mr":
            self.expression += self._fmt(self.memory)
            self._refresh()
            return

        if action == "_mc":
            self.memory = 0
            self._update_memory_display()
            return

        if action == "_sto":
            try:
                val = self._evaluate_expr(self.expression) if self.expression else 0
                self.variables["A"] = val
                self._update_memory_display()
            except Exception:
                pass
            return

        if action == "_rcl":
            self.expression += self._fmt(self.variables["A"])
            self._refresh()
            return

        # ===== متغیرها =====
        if action.startswith("_var"):
            name = action[4:]
            if self.alpha:
                # ذخیره
                try:
                    val = self._evaluate_expr(self.expression) if self.expression else 0
                    self.variables[name] = val
                    self._update_memory_display()
                except Exception:
                    pass
            else:
                # خوندن
                self.expression += self._fmt(self.variables.get(name, 0))
                self._refresh()
            return

        # ===== فرمول‌ها =====
        if action == "inv":
            if self.expression:
                self.expression = f"1/({self.expression})"
            else:
                self.expression = "1/"
            self._refresh()
            return

        if action == "fact":
            self.expression += "!"
            self._refresh()
            return

        if action == "root":
            # ریشه n‌ام — ساده: x^(1/y)
            self.expression += "**(1/"
            self._refresh()
            return

        # ===== اعداد و سایر =====
        self.expression += action
        self._refresh()

    # ========================================================
    # ابزارها
    # ========================================================
    def _refresh(self):
        self._update_display()
        self._preview()

    def _update_display(self):
        # جایگزینی نمادها برای نمایش قشنگ‌تر
        disp = self.expression or "0"
        # حذف ستاره‌های نمایشی
        disp = disp.replace("**2", "²").replace("**3", "³")
        disp = disp.replace("**", "^").replace("sqrt(", "√(")
        disp = disp.replace("cbrt(", "∛(").replace("asin(", "sin⁻¹(")
        disp = disp.replace("acos(", "cos⁻¹(").replace("atan(", "tan⁻¹(")
        self.display_var.set(disp)

    def _preview(self):
        if not self.expression:
            self.result_var.set("")
            self.status_var.set("")
            return
        try:
            result = self._evaluate_expr(self.expression)
            self.result_var.set(f"=  {self._fmt(result)}")
            self.status_var.set("")
        except ZeroDivisionError:
            self.result_var.set("")
            self.status_var.set("⚠️ تقسیم بر صفر")
        except Exception:
            self.result_var.set("")
            self.status_var.set("")

    def _evaluate(self):
        if not self.expression:
            return
        try:
            result = self._evaluate_expr(self.expression)
            self.last_answer = result
            formatted = self._fmt(result)
            self.expression = formatted
            self.display_var.set(formatted)
            self.result_var.set("")
            self.status_var.set("")
        except ZeroDivisionError:
            self.display_var.set("خطا: تقسیم بر صفر")
            self.expression = ""
        except Exception:
            self.display_var.set("خطای عبارت")
            self.expression = ""

    def _fmt(self, value):
        if isinstance(value, float):
            if value.is_integer() and abs(value) < 1e15:
                return str(int(value))
            return f"{value:.10g}"
        return str(value)

    # ========================================================
    # مفسر عبارت (Safe Eval)
    # ========================================================
    def _evaluate_expr(self, expr):
        # تبدیل نمادها
        s = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
        s = s.replace("^", "**")

        # π و e
        s = s.replace("π", "PI_VAL")
        # e به‌عنوان ثابت ریاضی — فقط وقتی تنهاست
        s = self._replace_e(s)
        s = s.replace("PI_VAL", "pi")

        # فاکتوریل: جایگزینی با تابع
        s = self._replace_factorial(s)

        # توابع مثلثاتی با تبدیل درجه
        if self.angle_mode == "DEG":
            sin_f = lambda x: math.sin(math.radians(x))
            cos_f = lambda x: math.cos(math.radians(x))
            tan_f = lambda x: math.tan(math.radians(x))
            asin_f = lambda x: math.degrees(math.asin(x))
            acos_f = lambda x: math.degrees(math.acos(x))
            atan_f = lambda x: math.degrees(math.atan(x))
        elif self.angle_mode == "RAD":
            sin_f = math.sin
            cos_f = math.cos
            tan_f = math.tan
            asin_f = math.asin
            acos_f = math.acos
            atan_f = math.atan
        else:  # GRAD
            sin_f = lambda x: math.sin(x * math.pi / 200)
            cos_f = lambda x: math.cos(x * math.pi / 200)
            tan_f = lambda x: math.tan(x * math.pi / 200)
            asin_f = lambda x: math.asin(x) * 200 / math.pi
            acos_f = lambda x: math.acos(x) * 200 / math.pi
            atan_f = lambda x: math.atan(x) * 200 / math.pi

        safe = {
            "__builtins__": None,
            "pi": math.pi,
            "e_const": math.e,
            "sin": sin_f,
            "cos": cos_f,
            "tan": tan_f,
            "asin": asin_f,
            "acos": acos_f,
            "atan": atan_f,
            "ln": lambda x: math.log(x) if x > 0 else float('nan'),
            "log": lambda x: math.log10(x) if x > 0 else float('nan'),
            "sqrt": lambda x: math.sqrt(x) if x >= 0 else float('nan'),
            "cbrt": lambda x: x ** (1/3) if x >= 0 else -((-x) ** (1/3)),
            "abs": abs,
            "fact": self._factorial,
        }

        # E → e_const (اعداد مثل 1E3 را نگه دار)
        s = self._replace_sci_e(s)

        result = eval(s, safe, {})
        return result

    def _replace_e(self, s):
        # فقط e که تنهاست (نه در EXP و نه در توابع)
        # ساده: اگه e بعدش عدد نبود، تبدیل کن
        out = []
        i = 0
        while i < len(s):
            if s[i] == "e" or s[i] == "E":
                # چک کن کاراکتر قبل عدد نیست (یعنی e بخشی از عدد نیست)
                if i > 0 and (s[i-1].isdigit() or s[i-1] == '.'):
                    out.append(s[i])
                elif i + 1 < len(s) and (s[i+1].isdigit() or s[i+1] == '-'):
                    # احتمالاً EXP
                    out.append(s[i])
                else:
                    out.append("e_const")
            else:
                out.append(s[i])
            i += 1
        return "".join(out)

    def _replace_sci_e(self, s):
        # E → e_const فقط اگه E تنهاست
        # در واقع در `_replace_e` انجام دادیم
        return s

    def _replace_factorial(self, s):
        # x! → fact(x)
        out = []
        i = 0
        while i < len(s):
            if s[i] == "!":
                # آخرین عنصر (عدد یا پرانتز) رو بگیر
                # ساده‌سازی: فرض کن قبلش یه عدد یا ) هست
                # حذف و بجاش fact
                # بیایم سراغ آخرین توکن
                # برای سادگی، فقط وقتی قبلی عدد باشه
                if out and out[-1].isdigit():
                    # همه رقم‌های پشت سرهم
                    num = ""
                    while out and (out[-1].isdigit() or out[-1] == "."):
                        num = out.pop() + num
                    out.append(f"fact({num})")
                elif out and out[-1] == ")":
                    # پرانتز بسته — سخت‌تر. فعلاً رها می‌کنیم
                    pass
            else:
                out.append(s[i])
            i += 1
        return "".join(out)

    def _factorial(self, n):
        n_int = int(n)
        if n_int < 0:
            raise ValueError("فاکتوریل منفی")
        if n_int > 170:
            return float('inf')
        return math.factorial(n_int)

    # ========================================================
    # مدیریت حالت‌ها
    # ========================================================
    def _cycle_mode(self):
        modes = ["DEG", "RAD", "GRAD"]
        idx = modes.index(self.angle_mode)
        self.angle_mode = modes[(idx + 1) % 3]
        self._update_mode_display()
        self._preview()

    def _update_mode_display(self):
        p = self.palette
        colors = {"DEG": p["accent"], "RAD": p["success"], "GRAD": "#8b5cf6"}
        self.mode_ind.config(text=self.angle_mode,
                              bg=colors.get(self.angle_mode, p["accent"]))

    def _update_shift_display(self):
        p = self.palette
        if self.shift:
            self.shift_ind.config(bg="#f59e0b", fg="white")
        else:
            self.shift_ind.config(bg=p["bg"], fg=p["muted"])
        self._update_button_labels()

    def _update_alpha_display(self):
        p = self.palette
        if self.alpha:
            self.alpha_ind.config(bg=p["danger"], fg="white")
        else:
            self.alpha_ind.config(bg=p["bg"], fg=p["muted"])

    def _update_memory_display(self):
        p = self.palette
        if self.memory != 0:
            self.mem_ind.config(bg=p["accent"], fg="white")
        else:
            self.mem_ind.config(bg=p["bg"], fg=p["muted"])

        # نمایش متغیرها
        non_zero = {k: v for k, v in self.variables.items() if v != 0}
        if non_zero:
            txt = " ".join(f"{k}={self._fmt(v)}" for k, v in non_zero.items())
            self.mem_display.set(txt)
        else:
            self.mem_display.set(f"M={self._fmt(self.memory)}" if self.memory else "")

    def _update_button_labels(self):
        """تغییر متن دکمه‌ها بر اساس SHIFT."""
        for item in self._button_data:
            btn = item["widget"]
            if self.shift:
                btn.config(text=item["shift"])
            else:
                btn.config(text=item["normal"])

    # ========================================================
    # کیبورد
    # ========================================================
    def _bind_keys(self):
        self.app.root.bind("<Key>", self._on_key, add="+")

    def _on_key(self, event):
        # فقط وقتی تب فعاله
        if not self.winfo_ismapped():
            return

        key = event.keysym
        char = event.char

        # اعداد
        if char.isdigit():
            self.expression += char
            self._refresh()
            return

        if char == ".":
            self.expression += "."
            self._refresh()
            return

        # عملیات
        mapping = {
            "plus": "+",
            "minus": "−",
            "asterisk": "×",
            "slash": "÷",
            "asciicircum": "**",
            "parenleft": "(",
            "parenright": ")",
            "percent": "%",
        }

        if key in mapping:
            self.expression += mapping[key]
            self._refresh()
            return

        if key in ("Return", "KP_Enter"):
            self._evaluate()
            return

        if key == "BackSpace":
            self.expression = self.expression[:-1]
            self._refresh()
            return

        if key == "Escape":
            self.expression = ""
            self._refresh()
            return