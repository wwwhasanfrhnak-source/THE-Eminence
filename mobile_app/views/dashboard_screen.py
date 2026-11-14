"""Dashboard with bottom navigation."""

from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from database import dashboard_counts
from rtl import rtl


class DashboardScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = (0.055, 0.075, 0.08, 1)
        layout = MDBoxLayout(orientation="vertical")
        self.toolbar = MDTopAppBar(
            title="THE Eminence",
            elevation=0,
            right_action_items=[["logout", self._logout]],
        )
        layout.add_widget(self.toolbar)

        self.navigation = MDBottomNavigation(
            panel_color=(0.075, 0.1, 0.105, 1),
            selected_color_background=(0.0, 0.38, 0.36, 1),
            text_color_active=(0.75, 0.9, 0.84, 1),
        )
        self.summary_labels = {}
        self.navigation.add_widget(self._home_tab())
        self.navigation.add_widget(self._projects_tab())
        self.navigation.add_widget(self._invoices_tab())
        layout.add_widget(self.navigation)
        self.add_widget(layout)

    def _home_tab(self):
        tab = MDBottomNavigationItem(name="home", text=rtl("خانه"), icon="view-dashboard")
        body = MDBoxLayout(
            orientation="vertical",
            spacing="14dp",
            padding=("20dp", "24dp", "20dp", "20dp"),
        )
        self.welcome_label = MDLabel(
            text=rtl("خوش آمدید"),
            font_name="Vazirmatn",
            font_style="H5",
            halign="right",
            size_hint_y=None,
            height="52dp",
        )
        body.add_widget(self.welcome_label)
        body.add_widget(
            MDLabel(
                text=rtl("نمای کلی"),
                font_name="Vazirmatn",
                font_style="Subtitle1",
                halign="right",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="34dp",
            )
        )
        for key, label in (
            ("projects", "پروژه‌ها"),
            ("invoices", "فاکتورها"),
            ("tasks", "وظایف"),
        ):
            row = MDBoxLayout(size_hint_y=None, height="62dp", spacing="12dp")
            row.add_widget(
                MDLabel(
                    text=rtl(label),
                    font_name="Vazirmatn",
                    halign="right",
                )
            )
            value_label = MDLabel(
                text="0",
                font_style="H6",
                halign="left",
                size_hint_x=0.3,
                theme_text_color="Custom",
                text_color=(0.45, 0.85, 0.74, 1),
            )
            self.summary_labels[key] = value_label
            row.add_widget(value_label)
            body.add_widget(row)
        body.add_widget(MDLabel(text="", size_hint_y=1))
        tab.add_widget(body)
        return tab

    def _projects_tab(self):
        tab = MDBottomNavigationItem(name="projects", text=rtl("پروژه‌ها"), icon="briefcase-outline")
        tab.add_widget(
            MDLabel(
                text=rtl("تعداد پروژه‌ها: ۰"),
                font_name="Vazirmatn",
                halign="center",
            )
        )
        self.project_tab = tab
        return tab

    def _invoices_tab(self):
        tab = MDBottomNavigationItem(name="invoices", text=rtl("فاکتورها"), icon="receipt-text-outline")
        tab.add_widget(
            MDLabel(
                text=rtl("تعداد فاکتورها: ۰"),
                font_name="Vazirmatn",
                halign="center",
            )
        )
        self.invoice_tab = tab
        return tab

    def set_user(self, user) -> None:
        display_name = user["full_name"] or user["username"]
        self.welcome_label.text = rtl(f"{display_name}، خوش آمدید")
        counts = dashboard_counts()
        for key, value in counts.items():
            self.summary_labels[key].text = str(value)
        self.project_tab.children[0].text = rtl(
            f"تعداد پروژه‌ها: {counts['projects']}"
        )
        self.invoice_tab.children[0].text = rtl(
            f"تعداد فاکتورها: {counts['invoices']}"
        )

    def _logout(self, *_args):
        from kivy.app import App

        App.get_running_app().logout()