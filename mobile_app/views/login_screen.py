"""Login screen: light ElectroCalc theme, RTL and asynchronous sign-in."""

from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField

import database
from rtl import rtl, rtl_lines


class ChangePasswordContent(MDBoxLayout):
    def __init__(self, colors, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing="8dp",
            size_hint_y=None,
            height="230dp",
            **kwargs,
        )
        self.add_widget(
            MDLabel(
                text=rtl_lines("برای ادامه باید رمز عبور اولیه را تغییر دهید."),
                font_name="Vazirmatn",
                font_style="Caption",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="40dp",
            )
        )
        self.new_field = MDTextField(
            hint_text=rtl("رمز عبور جدید (حداقل ۸ کاراکتر)"),
            password=True,
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            line_color_focus=colors.get("accent"),
            size_hint_y=None,
            height="54dp",
        )
        self.confirm_field = MDTextField(
            hint_text=rtl("تکرار رمز عبور جدید"),
            password=True,
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            line_color_focus=colors.get("accent"),
            size_hint_y=None,
            height="54dp",
        )
        self.error = MDLabel(
            text="",
            font_name="Vazirmatn",
            halign="center",
            theme_text_color="Custom",
            text_color=colors.get("danger", (0.86, 0.20, 0.25, 1)),
            size_hint_y=None,
            height="40dp",
        )
        self.add_widget(self.new_field)
        self.add_widget(self.confirm_field)
        self.add_widget(self.error)


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.app import App

        app = App.get_running_app()
        colors = getattr(app, "colors", {})
        self.md_bg_color = colors.get("bg", (0.957, 0.969, 0.988, 1))
        self._busy = False

        scroll = ScrollView(bar_width="0dp", do_scroll_x=False)
        page = MDBoxLayout(
            orientation="vertical",
            spacing="14dp",
            padding=("18dp", "20dp", "18dp", "26dp"),
            size_hint=(1, None),
        )
        page.bind(minimum_height=page.setter("height"))
        scroll.add_widget(page)

        page.add_widget(MDLabel(text="", size_hint_y=None, height="12dp"))
        page.add_widget(
            MDLabel(
                text="ElectroCalc",
                font_name="Vazirmatn",
                font_style="H3",
                halign="center",
                theme_text_color="Custom",
                text_color=colors.get("accent", (0.22, 0.40, 0.91, 1)),
                size_hint_y=None,
                height="54dp",
            )
        )
        page.add_widget(
            MDLabel(
                text=rtl("مدیریت پروژه‌های برق"),
                font_name="Vazirmatn",
                font_style="Subtitle1",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="30dp",
            )
        )

        card = MDCard(
            orientation="vertical",
            size_hint=(1, None),
            height="452dp",
            padding=("18dp", "20dp", "18dp", "18dp"),
            spacing="10dp",
            radius=[20, 20, 20, 20],
            elevation=0,
            md_bg_color=colors.get("card", (1, 1, 1, 1)),
        )
        self.card_title = MDLabel(
            text=rtl("ورود به حساب اختصاصی"),
            font_name="Vazirmatn",
            font_style="H6",
            halign="right",
            theme_text_color="Custom",
            text_color=colors.get("text", (0.12, 0.16, 0.22, 1)),
            size_hint_y=None,
            height="32dp",
        )
        card.add_widget(self.card_title)

        self.username_field = MDTextField(
            hint_text=rtl("نام کاربری"),
            icon_left="account-outline",
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            line_color_focus=colors.get("accent"),
            size_hint_y=None,
            height="54dp",
        )
        self.password_field = MDTextField(
            hint_text=rtl("رمز عبور"),
            icon_left="lock-outline",
            mode="rectangle",
            password=True,
            halign="right",
            font_name="Vazirmatn",
            line_color_focus=colors.get("accent"),
            size_hint_y=None,
            height="54dp",
        )
        self.password_field.bind(on_text_validate=self._submit)
        self.server_field = MDTextField(
            hint_text=rtl("آدرس سرور دفتر (اختیاری)"),
            icon_left="server-network",
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            line_color_focus=colors.get("accent"),
            helper_text=rtl(
                "مثال: https://192.168.1.20 — خالی = آفلاین"
            ),
            helper_text_mode="on_focus",
            size_hint_y=None,
            height="54dp",
        )
        card.add_widget(self.username_field)
        card.add_widget(self.password_field)
        card.add_widget(self.server_field)

        self.message = MDLabel(
            text="",
            font_name="Vazirmatn",
            halign="center",
            theme_text_color="Custom",
            text_color=colors.get("danger", (0.86, 0.20, 0.25, 1)),
            size_hint_y=None,
            height="38dp",
        )
        card.add_widget(self.message)

        self.submit_button = MDRaisedButton(
            text=rtl("ورود"),
            font_name="Vazirmatn",
            icon="login",
            pos_hint={"center_x": 0.5},
            size_hint=(1, None),
            height="50dp",
            md_bg_color=colors.get("accent", (0.22, 0.40, 0.91, 1)),
            text_color=(1, 1, 1, 1),
            on_release=self._submit,
        )
        card.add_widget(self.submit_button)
        page.add_widget(card)

        self.hint = MDLabel(
            text="",
            font_name="Vazirmatn",
            font_style="Caption",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="40dp",
        )
        page.add_widget(self.hint)
        self.add_widget(scroll)
        self._setup_mode = False
        self._change_dialog = None

    def _refresh_mode(self):
        try:
            empty = database.user_count() == 0
        except Exception:
            empty = False
        self._setup_mode = empty
        self.card_title.text = rtl(
            "راه‌اندازی مدیر اولیه" if empty else "ورود به حساب اختصاصی"
        )
        self.submit_button.text = rtl(
            "ایجاد مدیر و ورود" if empty else "ورود"
        )
        self.hint.text = rtl_lines(
            "هیچ حسابی روی این دستگاه نیست؛ اولین حساب، مدیر سیستم می‌شود "
            "و رمز آن باید در اولین ورود تغییر کند."
            if empty
            else "ورود آفلاین با حساب ذخیره‌شده روی همین دستگاه انجام می‌شود."
        )

    def _app(self):
        manager = getattr(self, "manager", None)
        app = getattr(manager, "app", None) if manager else None
        if app is None:
            from kivy.app import App

            app = App.get_running_app()
        return app

    def _submit(self, *_args):
        if self._busy:
            return
        username = self.username_field.text.strip()
        password = self.password_field.text
        server = self.server_field.text.strip()
        if not username or not password:
            self.message.text = rtl_lines("نام کاربری و رمز عبور را وارد کنید.")
            return
        app = self._app()
        if app is None:
            self.message.text = rtl_lines("برنامه آماده نیست؛ دوباره تلاش کنید.")
            return
        self._busy = True
        self.submit_button.disabled = True
        self.submit_button.text = rtl(
            "در حال ایجاد…" if self._setup_mode else "در حال ورود…"
        )
        self.message.text = ""
        app.authenticate_async(username, password, server, self._finished)

    def _finished(self, ok, message, must_change=False):
        self._busy = False
        self.submit_button.disabled = False
        self._reset_submit_text()
        if not ok:
            self.message.text = rtl_lines(message or "ورود ناموفق بود.")
            self.password_field.text = ""
            self.password_field.focus = True
            return
        self.message.text = ""
        self.password_field.text = ""
        if must_change:
            self._open_password_change()

    def _reset_submit_text(self):
        self.submit_button.text = rtl(
            "ایجاد مدیر و ورود" if self._setup_mode else "ورود"
        )

    def _open_password_change(self):
        app = self._app()
        colors = getattr(app, "colors", {}) if app else {}
        content = ChangePasswordContent(colors)
        holder = {}

        def save(*_args):
            new = content.new_field.text
            confirm = content.confirm_field.text
            if new != confirm:
                content.error.text = rtl_lines("تکرار رمز یکسان نیست.")
                return
            ok, error = app.complete_forced_change(new)
            if not ok:
                content.error.text = rtl_lines(error or "تغییر رمز ناموفق بود.")
                return
            holder["dialog"].dismiss()

        def cancel(*_args):
            if app:
                app.cancel_forced_change()
            holder["dialog"].dismiss()
            self.message.text = rtl_lines(
                "برای ورود باید رمز عبور اولیه را تغییر دهید."
            )
            self.password_field.focus = True

        dialog = MDDialog(
            title=rtl("تغییر رمز در اولین ورود"),
            type="custom",
            content_cls=content,
            auto_dismiss=False,
            buttons=[
                MDFlatButton(
                    text=rtl("انصراف"),
                    font_name="Vazirmatn",
                    on_release=cancel,
                ),
                MDRaisedButton(
                    text=rtl("ذخیره رمز جدید"),
                    font_name="Vazirmatn",
                    md_bg_color=colors.get(
                        "accent", (0.22, 0.40, 0.91, 1)
                    ),
                    text_color=(1, 1, 1, 1),
                    on_release=save,
                ),
            ],
        )
        holder["dialog"] = dialog
        self._change_dialog = dialog
        dialog.open()

    def on_pre_enter(self, *_args):
        self.message.text = ""
        self._refresh_mode()
        app = self._app()
        if app is not None and not getattr(app, "current_user", None):
            app.restore_session_async()
