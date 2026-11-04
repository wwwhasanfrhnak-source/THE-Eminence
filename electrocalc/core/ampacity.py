"""جریان مجاز کابل (بر اساس IEC 60364 - تقریبی)."""

# جدول جریان مجاز برای مس (آمپر)
# کلید: سطح مقطع mm² ، مقدار: جریان مجاز (A) در نصب داخل لوله
COPPER_AMPACITY = {
    1.5: 17.5,
    2.5: 24,
    4: 32,
    6: 41,
    10: 57,
    16: 76,
    25: 101,
    35: 125,
    50: 151,
    70: 192,
    95: 232,
    120: 269,
}


def get_ampacity(cross_section: float) -> float:
    """جریان مجاز کابل مسی."""
    if cross_section <= 0:
        raise ValueError("سطح مقطع باید بزرگ‌تر از صفر باشد.")
    if cross_section not in COPPER_AMPACITY:
        # نزدیک‌ترین
        closest = min(COPPER_AMPACITY.keys(),
                      key=lambda k: abs(k - cross_section))
        return COPPER_AMPACITY[closest]
    return COPPER_AMPACITY[cross_section]


def max_power(cross_section: float, voltage: float,
              cos_phi: float = 1.0, three_phase: bool = False) -> float:
    """حداکثر توان قابل انتقال (وات)."""
    import math
    amp = get_ampacity(cross_section)
    factor = math.sqrt(3) if three_phase else 1.0
    return factor * voltage * amp * cos_phi