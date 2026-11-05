# ui/views/login_view.py
"""Username and password sign-in view."""

import tkinter as tk
from tkinter import messagebox

from config.theme import BG_CARD, BG_MAIN, PRIMARY, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY
from core.exceptions import AuthenticationError
from ui.components.modern_card import ModernCard


class LoginView(tk.Frame):
    def __init__(self, master, font_family, auth_service, on_success):
        super().__init__(master, bg=BG_MAIN)
        self.font_family = font_family
        self.auth_service = auth_service
        self.on_success = on_success
        self.place(relwidth=1, relheight=1)
        self._build()

    def _build(self):
        card = ModernCard(self, width=390, height=430, radius=18, shadow=True)
        card.place(relx=0.5, rely=0.5, anchor="center")
        body = card.body
        tk.Label(body, text="⚡", bg=BG_CARD, fg=PRIMARY, font=(self.font_family, 32, "bold")).pack(
            pady=(15, 2)
        )
        tk.Label(
            body,
            text="Welcome back",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 20, "bold"),
        ).pack()
        tk.Label(
            body,
            text="Sign in to THE Eminence",
            bg=BG_CARD,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 10),
        ).pack(pady=(5, 24))

        tk.Label(
            body, text="Username", bg=BG_CARD, fg=TEXT_SECONDARY, font=(self.font_family, 9)
        ).pack(anchor="w", pady=(0, 5))
        self.username = tk.Entry(
            body,
            bg="#0b0f19",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 10),
        )
        self.username.pack(fill="x", ipady=10, pady=(0, 15))
        tk.Label(
            body, text="Password", bg=BG_CARD, fg=TEXT_SECONDARY, font=(self.font_family, 9)
        ).pack(anchor="w", pady=(0, 5))
        self.password = tk.Entry(
            body,
            show="•",
            bg="#0b0f19",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 10),
        )
        self.password.pack(fill="x", ipady=10)
        self.password.bind("<Return>", lambda _event: self._submit())
        button = tk.Button(
            body,
            text="Sign in",
            command=self._submit,
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            activebackground="#ea580c",
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            font=(self.font_family, 10, "bold"),
        )
        button.pack(fill="x", ipady=10, pady=(22, 0))
        tk.Label(
            body,
            text="Secure access · Local database",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=(self.font_family, 8),
        ).pack(pady=(18, 0))
        self.username.focus_set()

    def _submit(self):
        try:
            user = self.auth_service.authenticate(self.username.get(), self.password.get())
        except AuthenticationError:
            messagebox.showerror("Sign in failed", "Invalid username or password.", parent=self)
            self.password.delete(0, "end")
            return
        except Exception as exc:
            messagebox.showerror("Sign in failed", str(exc), parent=self)
            return
        self.on_success(user)
