"""تبدیل واحدهای پرکاربرد برق."""


def kw_to_hp(kw: float) -> float:
    """۱ کیلووات = ۱.۳۴۱ اسب بخار"""
    return kw * 1.34102


def hp_to_kw(hp: float) -> float:
    """۱ اسب بخار = ۰.۷۴۵۷ کیلووات"""
    return hp * 0.7457


def mm2_to_awg(mm2: float) -> str:
    """سطح مقطع mm² به AWG (تقریبی)."""
    table = [
        (0.5, "20"), (0.75, "18"), (1.0, "17"), (1.5, "15"),
        (2.5, "13"), (4.0, "11"), (6.0, "9"), (10.0, "7"),
        (16.0, "5"), (25.0, "3"), (35.0, "2"), (50.0, "1/0"),
        (70.0, "2/0"), (95.0, "3/0"), (120.0, "4/0"),
    ]
    closest = min(table, key=lambda t: abs(t[0] - mm2))
    return closest[1]


def celsius_to_fahrenheit(c: float) -> float:
    return c * 9 / 5 + 32


def fahrenheit_to_celsius(f: float) -> float:
    return (f - 32) * 5 / 9