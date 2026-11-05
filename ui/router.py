# ui/router.py
"""Simple route-to-view controller."""

from ui.views.customers_view import CustomersView
from ui.views.dashboard_view import DashboardView
from ui.views.projects_view import ProjectsView
from ui.views.reports_view import ReportsView
from ui.views.settings_view import SettingsView
from ui.views.users_view import UsersView


class Router:
    def __init__(self, content, font_family, user, on_logout):
        self.content = content
        self.font_family = font_family
        self.user = user
        self.on_logout = on_logout
        self.current_view = None

    def navigate(self, key: str):
        views = {
            "dashboard": lambda: DashboardView(self.content, self.font_family),
            "customers": lambda: CustomersView(self.content, self.font_family, self.user),
            "projects": lambda: ProjectsView(self.content, self.font_family, self.user),
            "reports": lambda: ReportsView(self.content, self.font_family, self.user),
            "users": lambda: UsersView(self.content, self.font_family, self.user),
            "settings": lambda: SettingsView(
                self.content, self.font_family, self.on_logout, self.user
            ),
        }
        factory = views.get(key)
        if factory is None:
            raise ValueError(f"Unknown route: {key}")
        if self.current_view is not None:
            self.current_view.destroy()
        self.current_view = factory()
        self.current_view.pack(fill="both", expand=True)
