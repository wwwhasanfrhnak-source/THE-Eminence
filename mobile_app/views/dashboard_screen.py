"""Dashboard with KPI cards, a compact chart, and bottom navigation."""

import threading

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon, MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from rtl import rtl
from views.projects_screen import ProjectsPanel
from views.users_screen import UsersPanel


KPI_ROWS = (
    ("projects", "پروژه‌ها", "projects.view", "briefcase-outline"),
    ("invoices", "فاکتورها", "invoices.view", "receipt-text-outline"),
    ("tasks", "وظایف", "tasks.view", "checkbox-marked-outline"),
    ("reports", "گزارش‌ها", "reports.view", "file-chart-outline"),
    ("timesheets", "ساعات کار", "timesheets.view", "clock-outline"),
    ("materials", "مصالح", "materials.view", "package-variant-closed"),
    ("customers", "مشتریان", "customers.view", "account-group-outline"),
)


class BarChart(Widget):
    """Small dependency-free bar chart drawn on the Kivy canvas."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.values = []
        self.bind(pos=self._redraw, size=self._redraw)

    def set_values(self, values):
        self.values = list(values or [])
        self._redraw()

    def _redraw(self, *_args):
        self.canvas.clear()
        if not self.values or self.width <= 0 or self.height <= 0:
            return
        maximum = max(self.values) or 1
        count = len(self.values)
        padding = 10
        gap = 6
        bar_width = max(
            4.0,
            (self.width - 2 * padding - gap * (count - 1)) / count,
        )
        with self.canvas:
            Color(0.878, 0.906, 0.957, 1)
            Rectangle(
                pos=(self.x + padding, self.y + 6),
                size=(self.width - 2 * padding, 1),
            )
            for index, value in enumerate(reversed(self.values)):
                height = max(5.0, (self.height - 18) * value / maximum)
                Color(0.220, 0.404, 0.910, 1)
                Rectangle(
                    pos=(
                        self.x + padding + index * (bar_width + gap),
                        self.y + 7,
                    ),
                    size=(bar_width, height),
                )


class DashboardScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.app import App

        app = App.get_running_app()
        self.colors = getattr(app, "colors", {})
        self.md_bg_color = self.colors.get("bg", (0.957, 0.969, 0.988, 1))
        self.permissions = set()
        self.summary_labels = {}
        self.kpi_order = []
        self.welcome_label = None
        self.status_label = None
        self.chart = None

        layout = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title="ElectroCalc",
            elevation=0,
            md_bg_color=self.colors.get("card", (1, 1, 1, 1)),
            specific_text_color=self.colors.get("text", (0.12, 0.16, 0.22, 1)),
            right_action_items=[["refresh", self._manual_refresh],
                                ["logout", self._logout]],
        )
        layout.add_widget(self.toolbar)

        self.navigation = MDBottomNavigation(
            panel_color=self.colors.get("card", (1, 1, 1, 1)),
            selected_color_background=self.colors.get("accent_soft"),
            text_color_active=self.colors.get("accent"),
        )
        self.home_tab = self._home_tab()
        self.projects_panel = ProjectsPanel()
        self.projects_tab = MDBottomNavigationItem(
            name="projects", text=rtl("پروژه‌ها"), icon="briefcase-outline"
        )
        self.projects_tab.add_widget(self.projects_panel)
        self.users_panel = UsersPanel()
        self.users_tab = MDBottomNavigationItem(
            name="users", text=rtl("کاربران"), icon="account-cog-outline"
        )
        self.users_tab.add_widget(self.users_panel)

        self.navigation.add_widget(self.home_tab)
        self.navigation.add_widget(self.projects_tab)
        self.navigation.add_widget(self.users_tab)
        # KivyMD 1.2.0 resolves text_color_normal through ids.tab_bar, which
        # does not exist yet during __init__, so it must be set afterwards.
        self.navigation.text_color_normal = self.colors.get("muted")
        layout.add_widget(self.navigation)
        self.add_widget(layout)

    # ------------------------------------------------------------------
    def _allowed(self, permission):
        from kivy.app import App

        app = App.get_running_app()
        if app is not None and hasattr(app, "has_permission"):
            return app.has_permission(permission)
        return False

    def _home_tab(self):
        tab = MDBottomNavigationItem(
            name="home", text=rtl("خانه"), icon="view-dashboard"
        )
        scroll = ScrollView(bar_width="0dp", do_scroll_x=False)
        self.home_body = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            padding=("14dp", "12dp", "14dp", "22dp"),
            size_hint_y=None,
        )
        self.home_body.bind(minimum_height=self.home_body.setter("height"))
        scroll.add_widget(self.home_body)
        tab.add_widget(scroll)
        return tab

    def _kpi_card(self, label, icon, value=0):
        card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height="96dp",
            padding=("10dp", "8dp", "10dp", "8dp"),
            spacing="2dp",
            radius=[14, 14, 14, 14],
            elevation=0,
            md_bg_color=self.colors.get("card", (1, 1, 1, 1)),
        )
        card.add_widget(
            MDIcon(
                icon=icon,
                font_size="22sp",
                theme_text_color="Custom",
                text_color=self.colors.get("accent"),
                size_hint_y=None,
                height="24dp",
            )
        )
        value_label = MDLabel(
            text=str(value),
            font_style="H6",
            halign="right",
            theme_text_color="Custom",
            text_color=self.colors.get("text"),
            size_hint_y=None,
            height="28dp",
        )
        card.add_widget(value_label)
        card.add_widget(
            MDLabel(
                text=rtl(label),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="right",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="20dp",
            )
        )
        return card, value_label

    def _populate_home(self):
        self.home_body.clear_widgets()
        self.summary_labels = {}
        self.kpi_order = []
        self.welcome_label = MDLabel(
            text=rtl("خوش آمدید"),
            font_name="Vazirmatn",
            font_style="H5",
            halign="right",
            theme_text_color="Custom",
            text_color=self.colors.get("text"),
            size_hint_y=None,
            height="46dp",
        )
        self.home_body.add_widget(self.welcome_label)
        self.status_label = MDLabel(
            text="",
            font_name="Vazirmatn",
            font_style="Caption",
            halign="right",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="24dp",
        )
        self.home_body.add_widget(self.status_label)
        self.home_body.add_widget(
            MDLabel(
                text=rtl("نمای کلی"),
                font_name="Vazirmatn",
                font_style="Subtitle1",
                halign="right",
                theme_text_color="Custom",
                text_color=self.colors.get("text"),
                size_hint_y=None,
                height="32dp",
            )
        )

        from kivy.app import App

        app = App.get_running_app()
        counts = app.summary_counts() if app is not None else {}
        visible = []
        for key, label, permission, icon in KPI_ROWS:
            if self._allowed(permission):
                visible.append((key, label, permission, icon))

        row = None
        for index, (key, label, _permission, icon) in enumerate(visible):
            if index % 2 == 0:
                row = MDBoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height="96dp",
                    spacing="10dp",
                )
                self.home_body.add_widget(row)
            card, value_label = self._kpi_card(
                label, icon, counts.get(key, 0)
            )
            self.summary_labels[key] = value_label
            self.kpi_order.append(key)
            row.add_widget(card)
            if index % 2 == 1:
                row = None

        if visible:
            chart_card = MDCard(
                orientation="vertical",
                size_hint=(1, None),
                height="154dp",
                padding=("12dp", "10dp", "12dp", "8dp"),
                spacing="4dp",
                radius=[14, 14, 14, 14],
                elevation=0,
                md_bg_color=self.colors.get("card", (1, 1, 1, 1)),
            )
            chart_card.add_widget(
                MDLabel(
                    text=rtl("توزیع رکوردها"),
                    font_name="Vazirmatn",
                    font_style="Subtitle2",
                    halign="right",
                    theme_text_color="Custom",
                    text_color=self.colors.get("text"),
                    size_hint_y=None,
                    height="26dp",
                )
            )
            self.chart = BarChart(size_hint_y=None, height="100dp")
            chart_card.add_widget(self.chart)
            self.home_body.add_widget(chart_card)
        else:
            self.chart = None
            self.home_body.add_widget(
                MDLabel(
                    text=rtl("هیچ بخشی برای نمایش مجاز نیست."),
                    font_name="Vazirmatn",
                    halign="center",
                    theme_text_color="Secondary",
                )
            )

    def _apply_tab_permissions(self):
        for tab, permission in (
            (self.projects_tab, "projects.view"),
            (self.users_tab, "users.view"),
        ):
            allowed = self._allowed(permission)
            attached = tab.parent is not None
            if allowed and not attached:
                self.navigation.add_widget(tab)
            elif not allowed and attached:
                self.navigation.remove_widget(tab)

    def set_user(self, user, permissions=None) -> None:
        self.permissions = set(permissions or ())
        try:
            display_name = user["full_name"] or user["username"]
        except (KeyError, IndexError, TypeError):
            display_name = "کاربر"
        self._apply_tab_permissions()
        self._populate_home()
        self.welcome_label.text = rtl(f"{display_name}، خوش آمدید")

        from kivy.app import App

        app = App.get_running_app()
        if app is not None and getattr(app, "online", False):
            self.status_label.text = rtl(
                f"آنلاین — {getattr(app, 'current_server', '')}"
            )
        else:
            self.status_label.text = rtl("آفلاین — حساب کش‌شده")
        self._refresh_counts(app)
        self.refresh_panels()

    def _refresh_counts(self, app):
        if app is None:
            return
        if not getattr(app, "online", False):
            self._apply_counts(app.summary_counts())
            return

        def worker():
            try:
                counts = app.remote_summary_counts()
            except Exception:
                counts = None
            if counts is not None:
                Clock.schedule_once(
                    lambda _dt: self._apply_counts(counts), 0
                )

        threading.Thread(
            target=worker, name="summary-refresh", daemon=True
        ).start()

    def _apply_counts(self, counts):
        counts = counts or {}
        values = []
        for key in self.kpi_order:
            value = int(counts.get(key, 0) or 0)
            values.append(value)
            label = self.summary_labels.get(key)
            if label is not None:
                label.text = str(value)
        if self.chart is not None:
            self.chart.set_values(values)

    def refresh_panels(self):
        if self.projects_tab.parent is not None:
            self.projects_panel.refresh()
        if self.users_tab.parent is not None:
            self.users_panel.refresh()

    def _manual_refresh(self, *_args):
        from kivy.app import App

        app = App.get_running_app()
        self._refresh_counts(app)
        self.refresh_panels()

    def on_pre_enter(self, *_args):
        try:
            self.navigation.switch_tab("home")
        except Exception:
            pass
        if self.welcome_label is not None:
            self._manual_refresh()

    def _logout(self, *_args):
        from kivy.app import App

        App.get_running_app().logout()
