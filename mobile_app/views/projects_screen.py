"""Projects tab: permission-aware list, search, local creation and LAN sync."""

import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

import api
import database
from rtl import rtl


STATUS_COLORS = {
    "planned": (0.851, 0.467, 0.024, 1),
    "in_progress": (0.220, 0.404, 0.910, 1),
    "done": (0.086, 0.639, 0.404, 1),
    "cancelled": (0.859, 0.196, 0.251, 1),
}


class ProjectsPanel(MDBoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", "8dp")
        kwargs.setdefault("padding", ("12dp", "10dp", "12dp", "8dp"))
        kwargs.setdefault("size_hint", (1, 1))
        super().__init__(**kwargs)
        app = App.get_running_app()
        self.colors = getattr(app, "colors", {})
        self._syncing = False
        self._search_event = None
        self._dialog = None

        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="44dp",
            spacing="8dp",
        )
        self.add_button = MDRaisedButton(
            text=rtl("پروژه جدید"),
            font_name="Vazirmatn",
            font_style="Caption",
            icon="plus",
            size_hint=(None, None),
            width="132dp",
            height="38dp",
            md_bg_color=self.colors.get("accent"),
            text_color=(1, 1, 1, 1),
            on_release=self._open_add_dialog,
        )
        self.sync_button = MDIconButton(
            icon="cloud-download-outline",
            theme_text_color="Custom",
            text_color=self.colors.get("accent"),
            on_release=lambda *_: self.refresh(sync=True),
        )
        header.add_widget(self.add_button)
        header.add_widget(self.sync_button)
        header.add_widget(MDLabel(text="", size_hint_x=1))
        title_box = MDBoxLayout(
            orientation="vertical",
            size_hint_x=None,
            width="150dp",
        )
        self.count_label = MDLabel(
            text=rtl("پروژه‌ها"),
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
            hint_text=rtl("جست‌وجوی پروژه یا مشتری"),
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

        self.message = MDLabel(
            text="",
            font_name="Vazirmatn",
            font_style="Caption",
            halign="right",
            theme_text_color="Custom",
            text_color=self.colors.get("muted"),
            size_hint_y=None,
            height="22dp",
        )
        self.add_widget(self.message)

        self.scroll = ScrollView(bar_width="0dp", do_scroll_x=False)
        self.list_box = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            size_hint_y=None,
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)
        self.add_widget(self.scroll)

        self._apply_permissions()
        self.refresh()

    def _allowed(self, permission):
        app = App.get_running_app()
        return bool(app and app.has_permission(permission))

    def _apply_permissions(self):
        allowed = self._allowed("projects.view")
        self.add_button.opacity = 1 if self._allowed("projects.create") else 0
        self.add_button.disabled = not self._allowed("projects.create")
        self.search_field.disabled = not allowed
        self.sync_button.opacity = 1 if allowed else 0
        self.sync_button.disabled = not allowed

    def _schedule_search(self, *_args):
        if self._search_event is not None:
            self._search_event.cancel()
        self._search_event = Clock.schedule_once(
            lambda _dt: self._load(), 0.35
        )

    def _notify(self, text, error=False):
        self.message.text = rtl(text)
        self.message.text_color = (
            self.colors.get("danger") if error else self.colors.get("success")
        )
        Clock.schedule_once(lambda _dt: setattr(self.message, "text", ""), 4)

    def refresh(self, sync=False):
        self._apply_permissions()
        if not self._allowed("projects.view"):
            self.list_box.clear_widgets()
            self.total_label.text = ""
            self.list_box.add_widget(
                MDLabel(
                    text=rtl("دسترسی به پروژه‌ها برای این حساب مجاز نیست."),
                    font_name="Vazirmatn",
                    halign="center",
                    theme_text_color="Secondary",
                )
            )
            return
        self._load()
        app = App.get_running_app()
        if sync and app is not None and getattr(app, "online", False):
            self._sync_from_server(app)

    def _sync_from_server(self, app):
        if self._syncing or not getattr(app, "current_token", ""):
            return
        self._syncing = True
        server = app.current_server
        token = app.current_token

        def worker():
            rows = []
            try:
                data = api.delta(server, token)
                rows = (data.get("tables") or {}).get("projects") or []
                database.merge_projects(rows)
            except Exception:
                rows = []
            Clock.schedule_once(
                lambda _dt: self._sync_finished(len(rows)), 0
            )

        threading.Thread(
            target=worker, name="projects-sync", daemon=True
        ).start()

    def _sync_finished(self, count):
        self._syncing = False
        if count:
            self._notify(f"{count} پروژه از سرور به‌روزرسانی شد.")
        self._load()

    def _load(self):
        self.list_box.clear_widgets()
        search = self.search_field.text if self.search_field else ""
        rows = database.list_projects(search)
        self.total_label.text = rtl(f"{len(rows)} مورد")
        if not rows:
            self.list_box.add_widget(
                MDLabel(
                    text=rtl("پروژه‌ای یافت نشد."),
                    font_name="Vazirmatn",
                    halign="center",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height="60dp",
                )
            )
            return
        for row in rows:
            self.list_box.add_widget(self._project_card(row))

    def _project_card(self, row):
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height="96dp",
            padding=("12dp", "8dp", "12dp", "8dp"),
            spacing="2dp",
            radius=[12, 12, 12, 12],
            elevation=0,
            md_bg_color=self.colors.get("card", (1, 1, 1, 1)),
        )
        top = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="26dp",
        )
        name = row["name"] or ""
        status = row["status"] or "planned"
        top.add_widget(
            MDLabel(
                text=rtl(name),
                font_name="Vazirmatn",
                font_style="Subtitle2",
                halign="right",
                theme_text_color="Custom",
                text_color=self.colors.get("text"),
            )
        )
        top.add_widget(
            MDLabel(
                text=rtl(database.PROJECT_STATUSES.get(status, status)),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="left",
                size_hint_x=0.3,
                theme_text_color="Custom",
                text_color=STATUS_COLORS.get(status, self.colors.get("muted")),
            )
        )
        card.add_widget(top)
        customer = row["customer"] or "—"
        card.add_widget(
            MDLabel(
                text=rtl(f"مشتری: {customer}"),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="right",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="20dp",
            )
        )
        created = (row["created_at"] or "")[:10]
        owner = row["created_by"] or "—"
        card.add_widget(
            MDLabel(
                text=rtl(f"ثبت: {created} — {owner}"),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="right",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="18dp",
            )
        )
        return card

    def _open_add_dialog(self, *_args):
        if not self._allowed("projects.create"):
            self._notify("مجوز ساخت پروژه برای این حساب وجود ندارد.", True)
            return
        content = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            size_hint_y=None,
            height="300dp",
        )
        name = MDTextField(
            hint_text=rtl("نام پروژه"),
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            size_hint_y=None,
            height="52dp",
        )
        customer = MDTextField(
            hint_text=rtl("مشتری (اختیاری)"),
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            size_hint_y=None,
            height="52dp",
        )
        description = MDTextField(
            hint_text=rtl("توضیحات (اختیاری)"),
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            size_hint_y=None,
            height="52dp",
        )
        state = {"status": "planned"}
        status_row = MDBoxLayout(
            orientation="horizontal",
            spacing="4dp",
            size_hint_y=None,
            height="38dp",
        )
        status_buttons = {}
        for key, label in database.PROJECT_STATUSES.items():
            button = MDFlatButton(
                text=rtl(label),
                font_name="Vazirmatn",
                font_style="Caption",
                text_color=(
                    self.colors.get("accent")
                    if key == "planned"
                    else self.colors.get("muted")
                ),
            )
            status_buttons[key] = button
            status_row.add_widget(button)

        def choose(key):
            state["status"] = key
            for item_key, item in status_buttons.items():
                item.text_color = (
                    self.colors.get("accent")
                    if item_key == key
                    else self.colors.get("muted")
                )

        for key, button in status_buttons.items():
            button.bind(on_release=lambda _b, k=key: choose(k))
        content.add_widget(name)
        content.add_widget(customer)
        content.add_widget(description)
        content.add_widget(status_row)

        dialog = MDDialog(
            title=rtl("پروژه جدید"),
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text=rtl("انصراف"),
                    font_name="Vazirmatn",
                    on_release=lambda *_a: dialog.dismiss(),
                ),
                MDRaisedButton(
                    text=rtl("ذخیره"),
                    font_name="Vazirmatn",
                    md_bg_color=self.colors.get("accent"),
                    text_color=(1, 1, 1, 1),
                    on_release=lambda *_a: self._save_project(
                        dialog, name.text, customer.text,
                        description.text, state["status"],
                    ),
                ),
            ],
        )
        self._dialog = dialog
        dialog.open()

    def _save_project(self, dialog, name, customer, description, status):
        try:
            database.create_project(
                name,
                customer=customer,
                description=description,
                status=status,
                created_by=self._current_username(),
            )
        except ValueError as exc:
            self._notify(str(exc), True)
            return
        except Exception:
            self._notify("ذخیره پروژه ناموفق بود.", True)
            return
        dialog.dismiss()
        self._notify("پروژه ذخیره شد.")
        self._load()

    @staticmethod
    def _current_username():
        app = App.get_running_app()
        user = getattr(app, "current_user", None) or {}
        try:
            return str(user["username"] or "")
        except (KeyError, IndexError, TypeError):
            return ""
