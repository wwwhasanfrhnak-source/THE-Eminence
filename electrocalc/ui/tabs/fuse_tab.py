"""تب انتخاب فیوز."""

from tkinter import ttk, messagebox, StringVar

from electrocalc.config import constants as C
from electrocalc.core import fuse


class FuseTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.current_var = StringVar(master=self, value="")
        self.factor_var = StringVar(master=self, value="1.25")
        self.result_var = StringVar(master=self, value="")
        self.build_ui()

    def build_ui(self) -> None:
        ttk.Label(self, text="⚡  انتخاب فیوز", font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(self, text="با وارد کردن جریان مدار، فیوز استاندارد پیشنهاد می‌شود",
                  font=C.FONT_BODY, foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 18))

        inp = ttk.LabelFrame(self, text="ورودی", padding=14)
        inp.pack(fill="x", pady=(0, 14))

        ttk.Label(inp, text="جریان مدار (A):", font=C.FONT_BODY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(inp, textvariable=self.current_var, width=20).grid(
            row=0, column=1, sticky="w", pady=6)

        ttk.Label(inp, text="ضریب اطمینان:", font=C.FONT_BODY).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=6)
        ttk.Entry(inp, textvariable=self.factor_var, width=20).grid(
            row=1, column=1, sticky="w", pady=6)

        ttk.Label(inp, text="مقدار معمول: 1.25", font=C.FONT_SMALL,
                  foreground=C.COLOR_MUTED).grid(row=2, column=1, sticky="w")

        btn = ttk.Frame(self)
        btn.pack(fill="x", pady=(0, 14))
        ttk.Button(btn, text="محاسبه", command=self.calculate).pack(side="left")
        ttk.Button(btn, text="پاک کردن", command=self.clear).pack(side="left", padx=8)

        res = ttk.LabelFrame(self, text="فیوز پیشنهادی", padding=14)
        res.pack(fill="x")
        ttk.Label(res, textvariable=self.result_var, font=C.FONT_RESULT,
                  foreground=C.COLOR_SUCCESS).pack(anchor="w")

    def calculate(self) -> None:
        try:
            text = self.current_var.get().strip()
            if not text:
                raise ValueError("جریان مدار را وارد کن.")
            current = float(text.replace(",", ""))

            ftext = self.factor_var.get().strip()
            factor = float(ftext.replace(",", "")) if ftext else 1.25

            fuse_amp = fuse.select_fuse(current, factor)
            self.result_var.set(f"{fuse_amp}  آمپر")
            self.app.set_status(f"فیوز پیشنهادی: {fuse_amp} A")
        except ValueError as e:
            self.result_var.set("")
            messagebox.showerror("خطای ورودی", str(e))

    def clear(self) -> None:
        self.current_var.set("")
        self.factor_var.set("1.25")
        self.result_var.set("")