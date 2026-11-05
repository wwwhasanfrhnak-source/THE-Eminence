# ui/components/toast.py
"""Transient, dark-themed application notification."""

import tkinter as tk

from ui.theme import BG_HOVER, DANGER, SUCCESS, TEXT_PRIMARY


class Toast:
    @staticmethod
    def show(
        master,
        message: str,
        font_family: str,
        duration: int = 2600,
        kind: str = "info",
    ):
        window = tk.Toplevel(master)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        color = SUCCESS if kind == "success" else DANGER if kind == "error" else BG_HOVER
        label = tk.Label(
            window,
            text=message,
            bg=color,
            fg=TEXT_PRIMARY,
            font=(font_family, 10),
            padx=18,
            pady=12,
        )
        label.pack()
        window.update_idletasks()
        x = master.winfo_rootx() + master.winfo_width() - window.winfo_width() - 24
        y = master.winfo_rooty() + master.winfo_height() - window.winfo_height() - 24
        window.geometry(f"+{max(0, x)}+{max(0, y)}")
        window.after(duration, window.destroy)
