"""محاسبه جریان و توان موتور."""

import math
from dataclasses import dataclass


@dataclass
class MotorResult:
    nominal_current: float      # جریان نامی (A)
    starting_current: float     # جریان راه‌انداز (A)
    starting_factor: float      # ضریب راه‌انداز (DOL = 6 تا 8)


def calc_motor_current(
    power_kw: float,
    voltage: float,
    cos_phi: float = 0.85,
    efficiency: float = 0.9,
    three_phase: bool = True,
) -> MotorResult:
    """
    محاسبه جریان نامی موتور.

    فرمول: I = P / (√3 × V × cos φ × η)   برای سه‌فاز
           I = P / (V × cos φ × η)         برای تک‌فاز

    پارامترها:
        power_kw   : توان موتور (کیلووات)
        voltage    : ولتاژ (V)
        cos_phi    : ضریب توان
        efficiency : بازده (0-1)
        three_phase: True برای سه‌فاز
    """
    if power_kw <= 0:
        raise ValueError("توان باید بزرگ‌تر از صفر باشد.")
    if voltage <= 0:
        raise ValueError("ولتاژ باید بزرگ‌تر از صفر باشد.")
    if not (0 < cos_phi <= 1):
        raise ValueError("ضریب توان باید بین ۰ و ۱ باشد.")
    if not (0 < efficiency <= 1):
        raise ValueError("بازده باید بین ۰ و ۱ باشد.")

    p_watt = power_kw * 1000
    factor = math.sqrt(3) if three_phase else 1.0

    current = p_watt / (factor * voltage * cos_phi * efficiency)
    starting = current * 6.5  # ضریب راه‌انداز معمول

    return MotorResult(
        nominal_current=current,
        starting_current=starting,
        starting_factor=6.5,
    )