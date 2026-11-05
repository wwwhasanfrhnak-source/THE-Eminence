"""Authenticated application shell, workspace router, and global interactions."""

import tkinter as tk
from tkinter import messagebox

from auth.permissions import has_permission
from auth.session import Session
from config.constants import ROUTES
from core.database import Database
from core.services.auth_service import AuthService
from core.services.project_service import ProjectService
from ui.components.sidebar import Sidebar
from ui.components.toast import Toast
from ui.components.topbar import TopBar
from ui.router import Router
from ui.theme import BG_MAIN, BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY
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
        self.master.report_callback_exception = self._report_callback_exception
        self.master.bind_all("<Control-k>", self._open_search_palette, add="+")
        self.master.bind_all("<Control-K>", self._open_search_palette, add="+")
        self.master.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.master.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.master.bind_all("<Button-5>", self._on_mousewheel, add="+")
        self.login_view = LoginView(master, self.font_family, self.auth_service, self._on_login)
        self.login_view.lift()
        self.master.after(30_000, self._check_session)

    def _on_login(self, user):
        self.session.start(user)
        self.login_view.destroy()
        routes = tuple(
            route for route in ROUTES if route[0] == "settings" or has_permission(user, route[0])
        )

        self.topbar = TopBar(
            self,
            self.font_family,
            user=user,
            on_search=self._perform_search,
            on_notifications=self._show_notifications,
            on_logout=self.logout,
        )
        self.topbar.pack(fill="x", side="top")

        self.workspace = tk.Frame(self, bg=BG_MAIN)
        self.workspace.pack(fill="both", expand=True)
        self.sidebar = Sidebar(self.workspace, self.font_family, self._navigate, routes, user=user)
        self.sidebar.pack(side="right", fill="y")
        self._build_scrollable_content()
        self.router = Router(self.content, self.font_family, user, self.logout)
        self.sidebar._click("dashboard")

    def _build_scrollable_content(self):
        self.content_shell = tk.Frame(self.workspace, bg=BG_MAIN)
        self.content_shell.pack(side="left", fill="both", expand=True)
        self.content_canvas = tk.Canvas(
            self.content_shell,
            bg=BG_MAIN,
            highlightthickness=0,
            borderwidth=0,
        )
        self.content_canvas.pack(fill="both", expand=True)
        self.content = tk.Frame(self.content_canvas, bg=BG_MAIN)
        self._content_window = self.content_canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind("<Configure>", self._update_scroll_region)
        self.content_canvas.bind("<Configure>", self._resize_content)

    def _update_scroll_region(self, _event=None):
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

    def _resize_content(self, event):
        self.content_canvas.itemconfigure(self._content_window, width=event.width)

    def _on_mousewheel(self, event):
        widget = event.widget
        while widget is not None and widget is not self.content_canvas:
            widget = getattr(widget, "master", None)
        if widget is not self.content_canvas:
            return
        if getattr(event, "num", None) == 4:
            direction = -1
        elif getattr(event, "num", None) == 5:
            direction = 1
        else:
            direction = -1 if event.delta > 0 else 1
        self.content_canvas.yview_scroll(direction * 2, "units")

    def _navigate(self, key: str):
        if not self.session.is_authenticated:
            self.logout()
            return
        user = self.session.current_user
        if user is None or not has_permission(user, key):
            Toast.show(
                self.master,
                "You do not have permission to open this page.",
                self.font_family,
                kind="error",
            )
            return
        try:
            self.session.touch()
            self.router.navigate(key)
            self.sidebar.set_active(key)
            self._update_scroll_region()
        except Exception as exc:
            self.logger.exception("Unable to open route %s", key)
            Toast.show(
                self.master,
                f"Unable to open this page: {exc}",
                self.font_family,
                kind="error",
            )

    def _perform_search(self, query: str = ""):
        normalized = query.strip().casefold()
        if not normalized:
            return
        route_matches = [
            (key, title)
            for key, title in ROUTES
            if normalized in key.casefold() or normalized in title.casefold()
            if self.session.user is not None
            and (key == "settings" or has_permission(self.session.user, key))
        ]
        if len(route_matches) == 1:
            self._navigate(route_matches[0][0])
            return
        if len(route_matches) > 1:
            self._open_search_palette(initial_query=query)
            return
        try:
            project_matches = [
                row
                for row in ProjectService().list()
                if normalized in str(row.get("title") or "").casefold()
            ]
        except Exception as exc:
            self.logger.exception("Global search failed")
            Toast.show(self.master, f"Search failed: {exc}", self.font_family, kind="error")
            return
        if project_matches:
            self._navigate("projects")
            view = self.router.current_view
            if hasattr(view, "search"):
                view.search.set(query)
            Toast.show(
                self.master,
                f"Found {len(project_matches)} project(s).",
                self.font_family,
            )
            return
        Toast.show(self.master, "No matching pages or projects.", self.font_family)

    def _open_search_palette(self, _event=None, initial_query=""):
        if self.session.user is None:
            return "break"
        dialog = tk.Toplevel(self)
        dialog.title("Search")
        dialog.configure(bg=BG_SURFACE)
        dialog.transient(self.winfo_toplevel())
        dialog.resizable(False, False)
        dialog.geometry("520x410")
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Quick navigation",
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 13, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 8))
        query = tk.StringVar(value=initial_query)
        entry = tk.Entry(
            dialog,
            textvariable=query,
            bg=BG_MAIN,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 10),
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        entry.pack(fill="x", padx=18, pady=(0, 12), ipady=9)
        results = tk.Listbox(
            dialog,
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY,
            selectbackground="#28364A",
            selectforeground=TEXT_PRIMARY,
            relief="flat",
            highlightthickness=0,
            font=(self.font_family, 10),
            activestyle="none",
        )
        results.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        available = [
            (key, title)
            for key, title in ROUTES
            if self.session.user is not None
            and (key == "settings" or has_permission(self.session.user, key))
        ]
        displayed = []

        def update_results(*_args):
            term = query.get().strip().casefold()
            displayed[:] = [
                route
                for route in available
                if not term or term in route[0].casefold() or term in route[1].casefold()
            ]
            results.delete(0, "end")
            for _key, title in displayed:
                results.insert("end", title)
            if displayed:
                results.selection_set(0)
                results.activate(0)

        def choose(_event=None):
            selection = results.curselection()
            if selection and selection[0] < len(displayed):
                key = displayed[selection[0]][0]
                dialog.destroy()
                self._navigate(key)
            return "break"

        query.trace_add("write", update_results)
        results.bind("<Double-Button-1>", choose)
        results.bind("<Return>", choose)
        entry.bind("<Return>", choose)
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        update_results()
        entry.focus_set()
        return "break"

    def _show_notifications(self):
        user = self.session.user
        if user is None:
            return
        try:
            rows = Database().fetch_all(
                "SELECT title, message, created_at FROM notifications "
                "WHERE user_id = ? OR user_id IS NULL ORDER BY id DESC LIMIT ?",
                (user.id, 12),
            )
        except Exception as exc:
            self.logger.exception("Unable to load notifications")
            Toast.show(
                self.master,
                f"Unable to load notifications: {exc}",
                self.font_family,
                kind="error",
            )
            return

        panel = tk.Toplevel(self)
        panel.title("Notifications")
        panel.configure(bg=BG_SURFACE)
        panel.transient(self.winfo_toplevel())
        panel.geometry("430x420")
        tk.Label(
            panel,
            text="Notifications",
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 13, "bold"),
        ).pack(anchor="w", padx=18, pady=16)
        if not rows:
            tk.Label(
                panel,
                text="You're all caught up.",
                bg=BG_SURFACE,
                fg=TEXT_SECONDARY,
                font=(self.font_family, 9),
            ).pack(anchor="w", padx=18)
            return
        for row in rows:
            item = tk.Frame(panel, bg=BG_SURFACE, highlightthickness=1)
            item.configure(highlightbackground=BORDER)
            item.pack(fill="x", padx=14, pady=5)
            tk.Label(
                item,
                text=row["title"],
                bg=BG_SURFACE,
                fg=TEXT_PRIMARY,
                font=(self.font_family, 9, "bold"),
                anchor="w",
            ).pack(fill="x", padx=10, pady=(8, 2))
            tk.Label(
                item,
                text=row["message"],
                bg=BG_SURFACE,
                fg=TEXT_SECONDARY,
                font=(self.font_family, 8),
                anchor="w",
                justify="left",
                wraplength=380,
            ).pack(fill="x", padx=10, pady=(0, 5))
            tk.Label(
                item,
                text=row["created_at"],
                bg=BG_SURFACE,
                fg=TEXT_SECONDARY,
                font=(self.font_family, 7),
                anchor="e",
            ).pack(fill="x", padx=10, pady=(0, 7))

    def _report_callback_exception(self, exc_type, exc_value, exc_traceback):
        self.logger.error(
            "Unhandled Tk callback exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        if self.winfo_exists():
            Toast.show(
                self.master,
                f"Something went wrong: {exc_value}",
                self.font_family,
                duration=4000,
                kind="error",
            )
        else:
            messagebox.showerror("THE Eminence", "An unexpected application error occurred.")

    def logout(self):
        user = self.session.clear()
        if user is not None:
            try:
                self.auth_service.logout(user)
            except Exception:
                self.logger.exception("Failed to record user logout")
        if hasattr(self, "workspace"):
            self.workspace.destroy()
        if hasattr(self, "topbar"):
            self.topbar.destroy()
        self.login_view = LoginView(
            self.master, self.font_family, self.auth_service, self._on_login
        )
        self.login_view.lift()

    def _check_session(self):
        if self.session.user is not None and not self.session.is_authenticated:
            self.logout()
        self.master.after(30_000, self._check_session)
