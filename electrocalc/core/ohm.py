"""فرمول‌های قانون اهم — بخش منطق محاسباتی (بدون Tkinter)."""

from dataclasses import dataclass


@dataclass
class OhmResult:
    """نتیجه محاسبه قانون اهم."""
    voltage: float | None = None
    current: float | None = None
    resistance: float | None = None


def calc_voltage(current: float, resistance: float) -> float:
    """V = I × R"""
    if current < 0 or resistance < 0:
        raise ValueError("جریان و مقاومت نمی‌توانند منفی باشند.")
    return current * resistance


def calc_current(voltage: float, resistance: float) -> float:
    """I = V / R"""
    if resistance == 0:
        raise ValueError("مقاومت نمی‌تواند صفر باشد (تقسیم بر صفر).")
    if voltage < 0 or resistance < 0:
        raise ValueError("ولتاژ و مقاومت نمی‌توانند منفی باشند.")
    return voltage / resistance


def calc_resistance(voltage: float, current: float) -> float:
    """R = V / I"""
    if current == 0:
        raise ValueError("جریان نمی‌تواند صفر باشد (تقسیم بر صفر).")
    if voltage < 0 or current < 0:
        raise ValueError("ولتاژ و جریان نمی‌توانند منفی باشند.")
    return voltage / current