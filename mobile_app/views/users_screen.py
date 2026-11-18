"""Users tab: cached accounts, status and platform badges (read-only on mobile)."""

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

import database
from rtl import rtl


ROLE_LABELS = {
    "admin": "مدیر",
    "engineer": "مهندس",
    "viewer": "بازدیدکننده",
}


class UsersPanel(MDBoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", "8dp")
        kwargs.setdefault("padding", ("12dp", "10dp", "12dp", "8dp"))
        kwargs.setdefault("size_hint", (1, 1))
        super().__init__(**kwargs)
        app = App.get_running_app()
        self.colors = getattr(app, "colors", {})
        self._search_event = None

        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="44dp",
            spacing="8dp",
        )
        header.add_widget(
            MDIconButton(
                icon="refresh",
                theme_text_color="Custom",
                text_color=self.colors.get("accent"),
                on_release=lambda *_: self.refresh(),
            )
        )
        header.add_widget(MDLabel(text="", size_hint_x=1))
        title_box = MDBoxLayout(
            orientation="vertical",
            size_hint_x=None,
            width="150dp",
        )
        self.count_label = MDLabel(
            text=rtl("کاربران دستگاه"),
            font_name="Vazirmatn",
            font_style="Subtitle1",
            halign="right",
            theme_text_color="Custom",
            text_color=self.colors.get("text"),
            size_hint_y=None,
            height="24dp",
        )
        self.total_label = MDLabel(
            text="",
            font_name="Vazirmatn",
            font_style="Caption",
            halign="right",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="18dp",
        )
        title_box.add_widget(self.count_label)
        title_box.add_widget(self.total_label)
        header.add_widget(title_box)
        self.add_widget(header)

        self.search_field = MDTextField(
            hint_text=rtl("جست‌وجوی نام یا نام کاربری"),
            icon_left="magnify",
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            line_color_focus=self.colors.get("accent"),
            size_hint_y=None,
            height="48dp",
        )
        self.search_field.bind(on_text=self._schedule_search)
        self.add_widget(self.search_field)

        self.note = MDLabel(
            text=rtl(
                "تغییر مجوزها و مدیریت حساب‌ها از نسخه ویندوز انجام می‌شود."
            ),
            font_name="Vazirmatn",
            font_style="Caption",
            halign="right",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="36dp",
        )
        self.add_widget(self.note)

        self.scroll = ScrollView(bar_width="0dp", do_scroll_x=False)
        self.list_box = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            size_hint_y=None,
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)
        self.add_widget(self.scroll)

        self.refresh()

    def _allowed(self, permission):
        app = App.get_running_app()
        return bool(app and app.has_permission(permission))

    def _schedule_search(self, *_args):
        if self._search_event is not None:
            self._search_event.cancel()
        self._search_event = Clock.schedule_once(
            lambda _dt: self._load(), 0.35
        )

    def refresh(self):
        if not self._allowed("users.view"):
            self.search_field.disabled = True
            self.list_box.clear_widgets()
            self.total_label.text = ""
            self.list_box.add_widget(
                MDLabel(
                    text=rtl("دسترسی به بخش کاربران برای این حساب مجاز نیست."),
                    font_name="Vazirmatn",
                    halign="center",
                    theme_text_color="Secondary",
                )
            )
            return
        self.search_field.disabled = False
        self._load()

    def _load(self):
        self.list_box.clear_widgets()
        search = self.search_field.text if self.search_field else ""
        rows = database.list_users(search)
        self.total_label.text = rtl(f"{len(rows)} حساب کش‌شده")
        if not rows:
            self.list_box.add_widget(
                MDLabel(
                    text=rtl("کاربری روی این دستگاه کش نشده است."),
                    font_name="Vazirmatn",
                    halign="center",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height="60dp",
                )
            )
            return
        for row in rows:
            self.list_box.add_widget(self._user_card(row))

    def _user_card(self, row):
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height="104dp",
            padding=("12dp", "8dp", "12dp", "8dp"),
            spacing="2dp",
            radius=[12, 12, 12, 12],
            elevation=0,
            md_bg_color=self.colors.get("card", (1, 1, 1, 1)),
        )
        top = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="28dp",
        )
        username = row["username"] or ""
        full_name = row["full_name"] or username
        active = bool(row["active"]) if "active" in row.keys() else True
        status = (
            row["account_status"]
            if "account_status" in row.keys() and row["account_status"]
            else ("active" if active else "disabled")
        )
        status_label = "فعال" if status == "active" else (
            "مسدود" if status == "blocked" else "غیرفعال"
        )
        status_color = (
            self.colors.get("success")
            if status == "active"
            else self.colors.get("danger")
        )
        top.add_widget(
            MDLabel(
                text=rtl(str(full_name)),
                font_name="Vazirmatn",
                font_style="Subtitle2",
                halign="right",
                theme_text_color="Custom",
                text_color=self.colors.get("text"),
            )
        )
        top.add_widget(
            MDLabel(
                text=rtl(status_label),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="left",
                size_hint_x=0.3,
                theme_text_color="Custom",
                text_color=status_color,
            )
        )
        card.add_widget(top)
        role = ROLE_LABELS.get(str(row["role"] or ""), str(row["role"] or ""))
        superadmin = "is_superadmin" in row.keys() and bool(row["is_superadmin"])
        if superadmin:
            role = "مدیر اصلی"
        card.add_widget(
            MDLabel(
                text=rtl(f"@{username} — {role}"),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="right",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="20dp",
            )
        )
        platforms = []
        if "platform_windows" in row.keys() and row["platform_windows"]:
            platforms.append("ویندوز")
        if "platform_android" in row.keys() and row["platform_android"]:
            platforms.append("اندروید")
        platform_text = "، ".join(platforms) if platforms else "بدون پلتفرم"
        last_login = ""
        if "last_login" in row.keys() and row["last_login"]:
            last_login = str(row["last_login"])[:16].replace("T", " ")
        detail = f"پلتفرم: {platform_text}"
        if last_login:
            detail += f" — آخرین ورود: {last_login}"
        card.add_widget(
            MDLabel(
                text=rtl(detail),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="right",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="20dp",
            )
        )
        return card
