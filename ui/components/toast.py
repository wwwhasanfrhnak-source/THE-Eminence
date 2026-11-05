# ui/components/toast.py
"""Transient, dark-themed application notification."""

import tkinter as tk

from config.theme import BG_HOVER, TEXT_PRIMARY


class Toast:
    @staticmethod
    def show(master, message: str, font_family: str, duration: int = 2600):
        window = tk.Toplevel(master)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        label = tk.Label(
            window,
            text=message,
            bg=BG_HOVER,
            fg=TEXT_PRIMARY,
            font=(font_family, 10),
            padx=18,
            pady=12,
        )
        label.pack()
        window.update_idletasks()
        x = master.winfo_rootx() + master.winfo_width() - window.winfo_width() - 24
        y = master.winfo_rooty() + 24
        window.geometry(f"+{max(0, x)}+{max(0, y)}")
        window.after(duration, window.destroy)
