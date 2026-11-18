"""ElectroCalc — Android entry point (KivyMD, Persian RTL, light theme)."""

import threading
from pathlib import Path

from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.resources import resource_add_path
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

import api
import permissions as perm_module
from auth import (
    authenticate_local,
    cache_online_profile,
    cache_online_session,
)
from database import initialize_database
from rtl import rtl
from views.dashboard_screen import DashboardScreen
from views.login_screen import LoginScreen


APP_DIR = Path(__file__).resolve().parent
ASSET_DIR = APP_DIR / "assets"
FONT_PATH = ASSET_DIR / "Vazirmatn-Regular.ttf"

COLORS = {
    "bg": (0.957, 0.969, 0.988, 1),
    "card": (1.0, 1.0, 1.0, 1),
    "accent": (0.220, 0.404, 0.910, 1),
    "accent_soft": (0.898, 0.925, 0.996, 1),
    "text": (0.122, 0.161, 0.216, 1),
    "muted": (0.420, 0.455, 0.529, 1),
    "border": (0.878, 0.906, 0.957, 1),
    "success": (0.086, 0.639, 0.404, 1),
    "danger": (0.859, 0.196, 0.251, 1),
    "warning": (0.851, 0.467, 0.024, 1),
}


class ElectroCalcApp(MDApp):
    def build(self):
        self.title = "ElectroCalc"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Indigo"
        self.colors = dict(COLORS)

        self.current_user = None
        self.current_permissions = set()
        self.current_server = ""
        self.current_token = ""
        self.online = False
        try:
            Window.softinput_mode = "below_target"
        except Exception:
            pass

        resource_add_path(str(ASSET_DIR))
        if FONT_PATH.is_file():
            LabelBase.register(name="Vazirmatn", fn_regular=str(FONT_PATH))

        initialize_database()

        manager = MDScreenManager()
        manager.add_widget(LoginScreen(name="login"))
        manager.add_widget(DashboardScreen(name="dashboard"))
        return manager

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def authenticate(self, username: str, password: str, server: str = ""):
        """ورود آنلاین (سرور LAN) یا آفلاین (حساب کش‌شده)."""
        return self._apply_auth(self._auth_result(username, password, server))

    def authenticate_async(self, username, password, server, callback):
        """Run the network login off the UI thread, then resume on it."""

        def worker():
            try:
                result = self._auth_result(username, password, server)
            except Exception:
                result = {
                    "ok": False,
                    "message": "خطای غیرمنتظره در ورود؛ دوباره تلاش کنید.",
                }
            Clock.schedule_once(
                lambda _dt: self._finish_async(result, callback), 0
            )

        threading.Thread(
            target=worker, name="mobile-login", daemon=True
        ).start()

    def _finish_async(self, result, callback):
        ok, message = self._apply_auth(result)
        if callback:
            callback(ok, message)

    def _auth_result(self, username, password, server=""):
        server = (server or "").strip()
        if server:
            try:
                data = api.login(server, username, password)
            except api.ApiError as exc:
                return {"ok": False, "message": str(exc)}
            user = dict(data.get("user") or {})
            if not user.get("username"):
                return {"ok": False, "message": "پاسخ سرور معتبر نیست."}
            permissions = list(data.get("permissions") or [])
            try:
                cache_online_session(user, password, permissions)
            except Exception:
                pass
            return {
                "ok": True,
                "user": user,
                "permissions": permissions,
                "server": api.normalize_server(server),
                "token": data.get("token", ""),
                "online": True,
            }

        user, effective, error = authenticate_local(username, password)
        if user is None:
            return {
                "ok": False,
                "message": error or "نام کاربری یا رمز عبور نادرست است.",
            }
        return {
            "ok": True,
            "user": dict(user),
            "permissions": sorted(effective),
            "server": "",
            "token": "",
            "online": False,
        }

    def _apply_auth(self, result):
        if not result.get("ok"):
            return False, result.get("message", "")
        self._enter_dashboard(
            result["user"],
            result["permissions"],
            server=result["server"],
            token=result["token"],
            online=result["online"],
        )
        return True, ""

    def restore_session(self):
        """بازیابی نشست ذخیره‌شده و اعتبارسنجی دوباره با سرور."""
        session = api.load_session()
        if not session:
            return False
        server = session.get("server", "")
        token = session.get("token", "")
        try:
            data = api.me(server, token)
        except api.ApiError:
            api.clear_session()
            return False
        user = dict(data.get("user") or {})
        if not user.get("username"):
            api.clear_session()
            return False
        permissions = list(data.get("permissions") or [])
        try:
            cache_online_profile(user, permissions)
        except Exception:
            pass
        self._enter_dashboard(
            user,
            permissions,
            server=server,
            token=token,
            online=True,
        )
        return True

    def restore_session_async(self):
        """اعتبارسنجی نشست در نخ کارگر تا رابط کاربری قفل نشود."""
        if getattr(self, "_restoring", False) or self.current_user:
            return
        session = api.load_session()
        if not session:
            return
        self._restoring = True
        server = session.get("server", "")
        token = session.get("token", "")

        def worker():
            data = None
            try:
                data = api.me(server, token)
            except api.ApiError:
                api.clear_session()
            Clock.schedule_once(
                lambda _dt: self._apply_restore(session, data), 0
            )

        threading.Thread(
            target=worker, name="session-restore", daemon=True
        ).start()

    def _apply_restore(self, session, data):
        self._restoring = False
        if not data or not isinstance(data.get("user"), dict):
            return
        user = data["user"]
        if not user.get("username"):
            return
        permissions = list(data.get("permissions") or [])
        try:
            cache_online_profile(user, permissions)
        except Exception:
            pass
        self._enter_dashboard(
            user,
            permissions,
            server=session.get("server", ""),
            token=session.get("token", ""),
            online=True,
        )

    def on_pause(self):
        return True

    def on_resume(self):
        """Revalidate the session so revoked grants do not linger."""
        if not (self.online and self.current_server and self.current_token):
            return
        server = self.current_server
        token = self.current_token

        def worker():
            try:
                data = api.me(server, token)
            except api.ApiError:
                Clock.schedule_once(lambda _dt: self._session_expired(), 0)
                return
            Clock.schedule_once(lambda _dt: self._apply_profile(data), 0)

        threading.Thread(
            target=worker, name="session-refresh", daemon=True
        ).start()

    def _apply_profile(self, data):
        user = dict((data or {}).get("user") or {})
        if not user.get("username") or not self.current_token:
            return
        permissions = list(data.get("permissions") or [])
        self.current_user = user
        self.current_permissions = set(permissions)
        try:
            cache_online_profile(user, permissions)
        except Exception:
            pass
        dashboard = self.root.get_screen("dashboard")
        dashboard.set_user(user, self.current_permissions)
        dashboard.refresh_panels()

    def _session_expired(self):
        self.current_user = None
        self.current_permissions = set()
        self.current_server = ""
        self.current_token = ""
        self.online = False
        api.clear_session()
        self.root.current = "login"
        login = self.root.get_screen("login")
        login.message.text = rtl("نشست شما منقضی شده است؛ دوباره وارد شوید.")

    def _enter_dashboard(self, user, permissions, server="", token="",
                         online=False):
        self.current_user = user
        self.current_permissions = set(permissions or [])
        self.current_server = server
        self.current_token = token
        self.online = online
        dashboard = self.root.get_screen("dashboard")
        dashboard.set_user(user, self.current_permissions)
        self.root.current = "dashboard"

    def logout(self) -> None:
        if self.online and self.current_server and self.current_token:
            api.logout(self.current_server, self.current_token)
        self.current_user = None
        self.current_permissions = set()
        self.current_server = ""
        self.current_token = ""
        self.online = False
        login = self.root.get_screen("login")
        login.password_field.text = ""
        login.message.text = ""
        self.root.current = "login"

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------
    def summary_counts(self):
        from database import dashboard_counts

        return dashboard_counts(self.current_permissions)

    def remote_summary_counts(self):
        if not (self.online and self.current_token):
            return self.summary_counts()
        data = api.summary(self.current_server, self.current_token)
        return data.get("counts") or {}

    def has_permission(self, permission):
        if self.current_user is None:
            return False
        if perm_module.is_superadmin(self.current_user):
            return True
        key = perm_module.LEGACY_ALIASES.get(permission, permission)
        effective = self.current_permissions
        if key in effective:
            return True
        if key.endswith(".export") and "exports.data" in effective:
            return True
        return f"{key.split('.', 1)[0]}.manage" in effective


if __name__ == "__main__":
    ElectroCalcApp().run()
