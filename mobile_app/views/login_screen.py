"""RTL login screen."""

from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

from rtl import rtl


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = (0.055, 0.075, 0.08, 1)

        content = MDBoxLayout(
            orientation="vertical",
            spacing="18dp",
            padding=("28dp", "36dp", "28dp", "28dp"),
            size_hint=(1, 1),
        )
        content.add_widget(MDLabel(text="", size_hint_y=0.6))
        content.add_widget(
            MDLabel(
                text="THE Eminence",
                font_name="Vazirmatn",
                font_style="H4",
                halign="center",
                size_hint_y=None,
                height="54dp",
            )
        )
        content.add_widget(
            MDLabel(
                text=rtl("ورود به حساب کاربری"),
                font_name="Vazirmatn",
                font_style="Subtitle1",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="34dp",
            )
        )

        self.username_field = MDTextField(
            hint_text=rtl("نام کاربری"),
            icon_left="account-outline",
            mode="rectangle",
            halign="right",
            font_name="Vazirmatn",
            size_hint_y=None,
            height="56dp",
        )
        self.password_field = MDTextField(
            hint_text=rtl("رمز عبور"),
            icon_left="lock-outline",
            mode="rectangle",
            password=True,
            halign="right",
            font_name="Vazirmatn",
            size_hint_y=None,
            height="56dp",
        )
        self.password_field.bind(on_text_validate=self._submit)
        content.add_widget(self.username_field)
        content.add_widget(self.password_field)

        self.message = MDLabel(
            text="",
            font_name="Vazirmatn",
            halign="center",
            theme_text_color="Error",
            size_hint_y=None,
            height="28dp",
        )
        content.add_widget(self.message)
        content.add_widget(
            MDRaisedButton(
                text=rtl("ورود"),
                font_name="Vazirmatn",
                icon="login",
                pos_hint={"center_x": 0.5},
                size_hint=(1, None),
                height="50dp",
                on_release=self._submit,
            )
        )
        content.add_widget(MDLabel(text="", size_hint_y=0.7))
        self.add_widget(content)

    def _submit(self, *_args):
        username = self.username_field.text.strip()
        password = self.password_field.text
        if not username or not password:
            self.message.text = rtl("نام کاربری و رمز عبور را وارد کنید.")
            return

        app = self.manager.app if hasattr(self.manager, "app") else None
        if app is None:
            from kivy.app import App

            app = App.get_running_app()
        if not app.authenticate(username, password):
            self.message.text = rtl("نام کاربری یا رمز عبور نادرست است.")
            self.password_field.text = ""
            self.password_field.focus = True

    def on_pre_enter(self, *_args):
        self.message.text = ""