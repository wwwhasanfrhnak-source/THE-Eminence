"""تب خانه — راهنمای شروع و وضعیت پروژه."""

from tkinter import ttk

from electrocalc.config import constants as C


class HomeTab(ttk.Frame):
    """
    تب خانه.

    این تب فقط یک خوش‌آمد و راهنما نشان می‌دهد.
    هر تب جدیدی که بسازی باید از ttk.Frame ارث‌بری کند
    و مثل همین کلاس، متد build_ui داشته باشد.
    """

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.build_ui()

    def build_ui(self) -> None:
        """ساخت اجزای این تب."""
        # عنوان
        ttk.Label(
            self,
            text="به ElectroCalc خوش آمدید",
            font=C.FONT_TITLE,
            foreground=C.COLOR_HEADER_BG,
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(
            self,
            text="ماشین‌حساب تخصصی برق صنعتی — نسخه آزمایشی",
            font=C.FONT_BODY,
            foreground=C.COLOR_MUTED,
        ).pack(anchor="w", pady=(0, 20))

        # کارت راهنما
        card = ttk.LabelFrame(self, text="راهنمای شروع", padding=16)
        card.pack(fill="x", pady=(0, 16))

        guide_lines = [
            "۱) هر قابلیت جدید = یک تب در پوشه ui/tabs/",
            "۲) فرمول‌ها را در پوشه core/ قرار بده (بدون Tkinter)",
            "۳) ثابت‌های ظاهری در config/constants.py",
            "۴) تنظیمات قابل تغییر در config/settings.py",
            "۵) لاگ‌ها در پوشه logs/electrocalc.log ذخیره می‌شوند",
        ]
        for line in guide_lines:
            ttk.Label(card, text=line, font=C.FONT_BODY).pack(anchor="w", pady=2)

        # وضعیت
        status = ttk.LabelFrame(self, text="وضعیت", padding=16)
        status.pack(fill="x")
        ttk.Label(
            status,
            text=f"نسخه: {C.APP_VERSION}   |   زبان: فارسی   |   سیستم: ویندوز",
            font=C.FONT_SMALL,
            foreground=C.COLOR_MUTED,
        ).pack(anchor="w")