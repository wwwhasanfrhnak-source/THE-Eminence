# ui/app.py
"""Top-level application frame and authenticated navigation."""

import tkinter as tk

from auth.permissions import has_permission
from auth.session import Session
from config.constants import ROUTES
from config.theme import BG_MAIN
from core.services.auth_service import AuthService
from ui.router import Router
from ui.components.sidebar import Sidebar
from ui.views.login_view import LoginView
from utils.fonts import get_font_family
from utils.logger import get_logger


class TheEminenceApp(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_MAIN)
        self.master = master
        self.logger = get_logger()
        self.auth_service = AuthService()
        self.session = Session()
        self.font_family = get_font_family(master)
        self.pack(fill="both", expand=True)
        self.login_view = LoginView(master, self.font_family, self.auth_service, self._on_login)
        self.login_view.lift()
        self.master.after(30_000, self._check_session)

    def _on_login(self, user):
        self.session.start(user)
        self.login_view.destroy()
        routes = tuple(
            route for route in ROUTES if route[0] == "settings" or has_permission(user, route[0])
        )
        self.workspace = tk.Frame(self, bg=BG_MAIN)
        self.workspace.pack(fill="both", expand=True)
        self.sidebar = Sidebar(self.workspace, self.font_family, self._navigate, routes, user=user)
        self.sidebar.pack(side="left", fill="y")
        self.content = tk.Frame(self.workspace, bg=BG_MAIN)
        self.content.pack(side="right", fill="both", expand=True, padx=28, pady=24)
        self.router = Router(self.content, self.font_family, user, self.logout)
        self.sidebar._click("dashboard")

    def _navigate(self, key: str):
        if not self.session.is_authenticated:
            self.logout()
            return
        if self.session.user is None or not has_permission(self.session.user, key):
            raise PermissionError(f"Permission denied: {key}")
        try:
            self.router.navigate(key)
        except Exception:
            self.logger.exception("Unable to open route %s", key)
            raise

    def logout(self):
        user = self.session.clear()
        if user is not None:
            self.auth_service.logout(user)
        if hasattr(self, "workspace"):
            self.workspace.destroy()
        self.login_view = LoginView(
            self.master, self.font_family, self.auth_service, self._on_login
        )
        self.login_view.lift()

    def _check_session(self):
        if self.session.user is not None and not self.session.is_authenticated:
            self.logout()
        self.master.after(30_000, self._check_session)
