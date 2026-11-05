# ui/views/users_view.py
"""User administration page."""

import tkinter as tk
from tkinter import messagebox

from config.theme import BG_CARD, BG_MAIN, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY
from core.repository import Repository
from core.services.auth_service import AuthService
from ui.components.data_table import DataTable
from ui.components.modern_card import ModernCard


class UsersView(tk.Frame):
    def __init__(self, master, font_family, user):
        super().__init__(master, bg=BG_MAIN)
        self.font_family, self.user = font_family, user
        self.repository = Repository()
        self.auth_service = AuthService()
        tk.Label(
            self, text="Users", bg=BG_MAIN, fg=TEXT_PRIMARY, font=(font_family, 20, "bold")
        ).pack(anchor="w")
        tk.Label(
            self,
            text="Manage team accounts and access roles",
            bg=BG_MAIN,
            fg=TEXT_SECONDARY,
            font=(font_family, 9),
        ).pack(anchor="w", pady=(4, 18))
        tk.Button(
            self,
            text="+ Add user",
            command=self.add_user,
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            padx=14,
            pady=8,
            font=(font_family, 9, "bold"),
        ).pack(anchor="w", pady=(0, 12))
        card = ModernCard(self, width=900, height=560)
        card.pack(fill="both", expand=True)
        self.table = DataTable(
            card.body,
            (
                "id",
                "username",
                "full_name",
                "role",
                "email",
                "phone",
                "is_active",
                "created_at",
                "last_login",
            ),
            (
                "ID",
                "Username",
                "Full name",
                "Role",
                "Email",
                "Phone",
                "Active",
                "Created",
                "Last login",
            ),
            font_family,
        )
        self.table.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        rows = self.repository.list_users()
        self.table.set_rows(
            [
                tuple(
                    row.get(column) or ""
                    for column in (
                        "id",
                        "username",
                        "full_name",
                        "role",
                        "email",
                        "phone",
                        "is_active",
                        "created_at",
                        "last_login",
                    )
                )
                for row in rows
            ]
        )

    def add_user(self):
        dialog = tk.Toplevel(self)
        dialog.title("Create user")
        dialog.configure(bg=BG_CARD)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        labels = ("Username", "Password", "Full name", "Role", "Email", "Phone")
        entries = {}
        for row, label in enumerate(labels):
            tk.Label(
                dialog, text=label, bg=BG_CARD, fg=TEXT_SECONDARY, font=(self.font_family, 9)
            ).grid(row=row, column=0, padx=12, pady=7, sticky="w")
            entry = tk.Entry(
                dialog,
                bg="#0b0f19",
                fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY,
                relief="flat",
                width=32,
                show="•" if label == "Password" else "",
            )
            entry.grid(row=row, column=1, padx=12, pady=7, ipady=5)
            entries[label] = entry
        entries["Role"].insert(0, "user")
        result = {}

        def save():
            try:
                result["id"] = self.auth_service.create_user(
                    entries["Username"].get(),
                    entries["Password"].get(),
                    entries["Full name"].get(),
                    entries["Role"].get().strip() or "user",
                    entries["Email"].get().strip() or None,
                    entries["Phone"].get().strip() or None,
                    self.user.id,
                )
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror("Unable to create user", str(exc), parent=dialog)

        tk.Button(
            dialog,
            text="Create account",
            command=save,
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 9, "bold"),
        ).grid(row=len(labels), column=0, columnspan=2, padx=12, pady=14, sticky="ew")
        self.wait_window(dialog)
        if result:
            self.refresh()
