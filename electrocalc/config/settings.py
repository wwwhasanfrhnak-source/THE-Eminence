"""تنظیمات قابل تغییر در زمان اجرا."""

from dataclasses import dataclass


@dataclass
class AppSettings:
    """تنظیمات قابل تغییر برنامه."""
    decimal_places: int = 2          # تعداد ارقام اعشار
    language: str = "fa"             # زبان
    theme: str = "light"             # light | dark (فعلاً light)
    remember_last_tab: bool = True   # یادآوری آخرین تب


# نمونه سراسری
settings = AppSettings()