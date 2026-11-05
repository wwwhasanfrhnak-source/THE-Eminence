"""Reusable polished confirmation/status dialogs for THE Eminence."""

from tkinter import messagebox


def show_success(title, message, parent=None):
    messagebox.showinfo(title, message, parent=parent)


def show_error(title, message, parent=None):
    messagebox.showerror(title, message, parent=parent)


def confirm(title, message, parent=None):
    return messagebox.askyesno(title, message, parent=parent)
