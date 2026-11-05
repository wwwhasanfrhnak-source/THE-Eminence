# main.py
"""Application entry point for THE Eminence desktop manager."""

import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from config.constants import APP_NAME
from config.theme import BG_MAIN
from core.database import Database
from ui.app import TheEminenceApp
from utils.logger import get_logger


def main() -> None:
    logger = get_logger()
    try:
        Database()
        window = ttk.Window(themename="darkly")
        window.title(APP_NAME)
        window.geometry("1400x850")
        window.minsize(1180, 760)
        window.configure(bg=BG_MAIN)
        TheEminenceApp(window)
        window.mainloop()
    except Exception as exc:
        logger.exception("Application startup failed")
        try:
            messagebox.showerror("THE Eminence", f"Unable to start the application:\n{exc}")
        except tk.TclError:
            raise
        raise


if __name__ == "__main__":
    main()
