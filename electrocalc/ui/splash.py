"""Splash Screen — صفحه لودینگ."""

import tkinter as tk
from pathlib import Path


class SplashScreen:
    def __init__(self, duration=2500):
        self.duration = duration
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        w, h = 500, 400
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.canvas = tk.Canvas(self.root, width=w, height=h,
                                 highlightthickness=0, bg="#7c3aed")
        self.canvas.pack(fill="both", expand=True)

        for i in range(h):
            r1, g1, b1 = 124, 58, 237
            r2, g2, b2 = 6, 182, 212
            ratio = i / h
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.canvas.create_line(0, i, w, i, fill=color)

        self._img = None
        icon_path = Path(__file__).resolve().parents[2] / "assets" / "icon.png"
        if icon_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(icon_path).convert("RGBA")
                img = img.resize((120, 120), Image.LANCZOS)
                self._img = ImageTk.PhotoImage(img)
                self.canvas.create_image(w // 2, 110, image=self._img)
            except Exception:
                self.canvas.create_text(w // 2, 110, text="⚡",
                                         fill="white",
                                         font=("Segoe UI", 72))
        else:
            self.canvas.create_text(w // 2, 110, text="⚡",
                                     fill="white",
                                     font=("Segoe UI", 72))

        self.canvas.create_text(w // 2, 220, text="THE Eminence",
                                 fill="white",
                                 font=("Segoe UI", 28, "bold"))
        self.canvas.create_text(w // 2, 255,
                                 text="Professional Electrical Calculator",
                                 fill="#e0e7ff",
                                 font=("Segoe UI", 11))

        self.canvas.create_rectangle(80, 310, 420, 320,
                                       fill="#4c1d95", outline="")
        self.progress_bar = self.canvas.create_rectangle(
            80, 310, 80, 320, fill="#10b981", outline="")

        self.loading_text = self.canvas.create_text(
            w // 2, 345, text="در حال بارگذاری...",
            fill="#e0e7ff", font=("Segoe UI", 10))

        self._progress = 0
        self.root.after(50, self._animate)

    def _animate(self):
        if self._progress >= 100:
            self.root.after(self.duration, self._close)
            return

        self._progress += 2
        bar_width = int(340 * self._progress / 100)
        self.canvas.coords(self.progress_bar,
                            80, 310, 80 + bar_width, 320)

        if self._progress < 40:
            text = "در حال راه‌اندازی..."
        elif self._progress < 70:
            text = "در حال بارگذاری ماژول‌ها..."
        elif self._progress < 95:
            text = "در حال آماده‌سازی UI..."
        else:
            text = "آماده!"

        self.canvas.itemconfig(self.loading_text, text=text)
        self.root.after(30, self._animate)

    def _close(self):
        self.root.destroy()

    def show(self):
        self.root.mainloop()


def show_splash(duration=2500):
    splash = SplashScreen(duration)
    splash.show()