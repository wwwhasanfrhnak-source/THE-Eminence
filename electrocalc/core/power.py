"""فرمول‌های محاسبه توان — منطق محاسباتی (بدون Tkinter).

انواع توان:
  P (توان اکتیو)     → وات (W)
  S (توان ظاهری)     → ولت‌آمپر (VA)
  Q (توان راکتیو)    → وار (VAR)

برای سیستم تک‌فاز: بدون ضریب √3
برای سیستم سه‌فاز: با ضریب √3
"""

import math
from dataclasses import dataclass


@dataclass
class PowerResult:
    """نتیجه محاسبه توان."""
    p: float          # توان اکتیو (W)
    s: float          # توان ظاهری (VA)
    q: float          # توان راکتیو (VAR)


def calc_power(
    voltage: float,
    current: float,
    cos_phi: float,
    three_phase: bool = False,
) -> PowerResult:
    """
    محاسبه هر سه نوع توان.

    پارامترها:
        voltage    : ولتاژ (V)
        current    : جریان (A)
        cos_phi    : ضریب توان (0 تا 1)
        three_phase: اگر True باشد، سه‌فاز محاسبه می‌شود

    خروجی:
        PowerResult شامل p، s، q

    خطاها:
        ValueError اگر مقادیر نامعتبر باشند
    """
    # ---- اعتبارسنجی ----
    if voltage <= 0:
        raise ValueError("ولتاژ باید بزرگ‌تر از صفر باشد.")
    if current <= 0:
        raise ValueError("جریان باید بزرگ‌تر از صفر باشد.")
    if not (0 < cos_phi <= 1):
        raise ValueError("ضریب توان (cos φ) باید عددی بین ۰ و ۱ باشد.")

    # ---- محاسبه ----
    factor = math.sqrt(3) if three_phase else 1.0

    s = factor * voltage * current              # توان ظاهری
    p = s * cos_phi                             # توان اکتیو
    # sin φ = √(1 - cos²φ)
    sin_phi = math.sqrt(max(0.0, 1.0 - cos_phi ** 2))
    q = s * sin_phi                             # توان راکتیو

    return PowerResult(p=p, s=s, q=q)