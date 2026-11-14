"""Android entry point for THE Eminence."""

from pathlib import Path

from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from auth import verify_login
from database import initialize_database
from rtl import rtl
from views.dashboard_screen import DashboardScreen
from views.login_screen import LoginScreen


APP_DIR = Path(__file__).resolve().parent
ASSET_DIR = APP_DIR / "assets"
FONT_PATH = ASSET_DIR / "Vazirmatn-Regular.ttf"


class EminenceApp(MDApp):
    def build(self):
        self.title = "THE Eminence"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Amber"

        resource_add_path(str(ASSET_DIR))
        if FONT_PATH.is_file():
            LabelBase.register(name="Vazirmatn", fn_regular=str(FONT_PATH))

        initialize_database()

        manager = MDScreenManager()
        manager.add_widget(LoginScreen(name="login"))
        manager.add_widget(DashboardScreen(name="dashboard"))
        return manager

    def authenticate(self, username: str, password: str) -> bool:
        user = verify_login(username, password)
        if user is None:
            return False

        self.current_user = user
        dashboard = self.root.get_screen("dashboard")
        dashboard.set_user(user)
        self.root.current = "dashboard"
        return True

    def logout(self) -> None:
        self.current_user = None
        self.root.current = "login"


if __name__ == "__main__":
    EminenceApp().run()