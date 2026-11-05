# ui/views/settings_view.py
"""Application settings, backup, and logout actions."""

import tkinter as tk
from tkinter import filedialog, messagebox

from config.theme import BG_CARD, BG_MAIN, DANGER, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY
from core.exceptions import AuthenticationError
from core.services.auth_service import AuthService
from core.services.backup_service import BackupService
from ui.components.modern_card import ModernCard


class SettingsView(tk.Frame):
    def __init__(self, master, font_family, on_logout, user):
        super().__init__(master, bg=BG_MAIN)
        self.font_family = font_family
        self.on_logout = on_logout
        self.user = user
        tk.Label(
            self, text="Settings", bg=BG_MAIN, fg=TEXT_PRIMARY, font=(font_family, 20, "bold")
        ).pack(anchor="w")
        tk.Label(
            self,
            text="Manage local data and your current session",
            bg=BG_MAIN,
            fg=TEXT_SECONDARY,
            font=(font_family, 9),
        ).pack(anchor="w", pady=(4, 18))
        card = ModernCard(self, width=600, height=260)
        card.pack(anchor="nw")
        tk.Label(
            card.body,
            text="Database backup",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=(font_family, 12, "bold"),
        ).pack(anchor="w", pady=(12, 4))
        tk.Label(
            card.body,
            text="Create a consistent copy of the local SQLite database.",
            bg=BG_CARD,
            fg=TEXT_SECONDARY,
            font=(font_family, 9),
        ).pack(anchor="w", pady=(0, 16))
        tk.Button(
            card.body,
            text="Create backup",
            command=self.backup,
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            padx=14,
            pady=9,
            font=(font_family, 9, "bold"),
        ).pack(anchor="w")
        tk.Button(
            card.body,
            text="Change password",
            command=self.change_password,
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            relief="flat",
            padx=14,
            pady=9,
            font=(font_family, 9, "bold"),
        ).pack(anchor="w", pady=(14, 0))
        tk.Button(
            card.body,
            text="Sign out",
            command=self.on_logout,
            bg=DANGER,
            fg=TEXT_PRIMARY,
            relief="flat",
            padx=14,
            pady=9,
            font=(font_family, 9, "bold"),
        ).pack(anchor="w", pady=(22, 0))

    def backup(self):
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".sqlite", filetypes=[("SQLite database", "*.sqlite")]
        )
        if path:
            try:
                saved = BackupService().create_backup(path)
                messagebox.showinfo("Backup complete", f"Backup saved to:\n{saved}", parent=self)
            except Exception as exc:
                messagebox.showerror("Backup failed", str(exc), parent=self)

    def change_password(self):
        dialog = tk.Toplevel(self)
        dialog.title("Change password")
        dialog.configure(bg=BG_CARD)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        fields = {}
        for row, label in enumerate(("Current password", "New password", "Confirm new password")):
            tk.Label(
                dialog, text=label, bg=BG_CARD, fg=TEXT_SECONDARY, font=(self.font_family, 9)
            ).grid(row=row, column=0, padx=14, pady=8, sticky="w")
            entry = tk.Entry(
                dialog,
                show="•",
                bg="#0b0f19",
                fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY,
                relief="flat",
                width=30,
            )
            entry.grid(row=row, column=1, padx=14, pady=8, ipady=5)
            fields[label] = entry

        def save():
            new_password = fields["New password"].get()
            if new_password != fields["Confirm new password"].get():
                messagebox.showerror(
                    "Password mismatch", "The new passwords do not match.", parent=dialog
                )
                return
            try:
                AuthService().change_password(
                    self.user.id, fields["Current password"].get(), new_password
                )
            except (AuthenticationError, ValueError) as exc:
                messagebox.showerror("Unable to change password", str(exc), parent=dialog)
                return
            except Exception as exc:
                messagebox.showerror("Unable to change password", str(exc), parent=dialog)
                return
            dialog.destroy()
            messagebox.showinfo("Password changed", "Your password was updated.", parent=self)

        tk.Button(
            dialog,
            text="Update password",
            command=save,
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 9, "bold"),
        ).grid(row=3, column=0, columnspan=2, padx=12, pady=14, sticky="ew")
        self.wait_window(dialog)
