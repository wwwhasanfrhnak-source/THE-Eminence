"""محاسبات پیشرفته موتور القایی/سنکرون."""

import math
from dataclasses import dataclass


# فرکانس شبکه
DEFAULT_FREQ = 50  # Hz

# تعداد قطب‌های استاندارد
POLES = [2, 4, 6, 8, 10, 12]

# ضریب جریان راه‌انداز بر اساس روش
STARTER_FACTORS = {
    "DOL": {"name": "مستقیم (DOL)", "factor": 6.0},
    "star_delta": {"name": "ستاره-مثلث", "factor": 2.0},
    "soft": {"name": "سافت استارتر", "factor": 2.5},
    "vfd": {"name": "درایو (VFD)", "factor": 1.5},
    "resistance": {"name": "مقاومت راه‌انداز", "factor": 3.0},
    "autotransformer": {"name": "اتوترانس", "factor": 3.5},
}


@dataclass
class SyncSpeedResult:
    """نتیجه سرعت سنکرون."""
    sync_rpm: float
    actual_rpm: float
    slip_percent: float
    poles: int
    frequency: float


@dataclass
class StarterResult:
    """نتیجه محاسبه راه‌انداز."""
    starter_name: str
    starting_current: float
    starting_factor: float
    starting_torque_percent: float


def calculate_sync_speed(frequency: float, poles: int,
                          actual_rpm: float = None) -> SyncSpeedResult:
    """
    محاسبه سرعت سنکرون و لغزش.

    Ns = 120 × f / P

    پارامترها:
        frequency : فرکانس (Hz)
        poles     : تعداد قطب
        actual_rpm: دور واقعی موتور (اگه بدونیم → لغزش حساب می‌شه)
    """
    if frequency <= 0:
        raise ValueError("فرکانس باید بزرگ‌تر از صفر باشد.")
    if poles <= 0 or poles % 2 != 0:
        raise ValueError("تعداد قطب باید عدد زوج مثبت باشد.")

    ns = (120 * frequency) / poles

    if actual_rpm is not None and actual_rpm > 0:
        if actual_rpm > ns:
            raise ValueError("دور واقعی نمی‌تواند از سنکرون بیشتر باشد.")
        slip = ((ns - actual_rpm) / ns) * 100
    else:
        # لغزش معمول ۳٪
        actual_rpm = ns * 0.97
        slip = 3.0

    return SyncSpeedResult(
        sync_rpm=ns,
        actual_rpm=actual_rpm,
        slip_percent=slip,
        poles=poles,
        frequency=frequency,
    )


def calc_starting_current(nominal_current: float,
                           starter_type: str = "DOL") -> StarterResult:
    """
    محاسبه جریان راه‌انداز بر اساس روش راه‌اندازی.

    پارامترها:
        nominal_current : جریان نامی موتور (A)
        starter_type    : DOL | star_delta | soft | vfd | resistance | autotransformer
    """
    if nominal_current <= 0:
        raise ValueError("جریان نامی باید بزرگ‌تر از صفر باشد.")

    if starter_type not in STARTER_FACTORS:
        raise ValueError("روش راه‌انداز نامعتبر است.")

    info = STARTER_FACTORS[starter_type]
    factor = info["factor"]
    starting = nominal_current * factor

    # گشتاور راه‌انداز بر اساس روش (تقریبی)
    torque_map = {
        "DOL": 100,
        "star_delta": 33,
        "soft": 50,
        "vfd": 150,
        "resistance": 60,
        "autotransformer": 60,
    }
    torque = torque_map.get(starter_type, 100)

    return StarterResult(
        starter_name=info["name"],
        starting_current=starting,
        starting_factor=factor,
        starting_torque_percent=torque,
    )


def suggest_poles(frequency: float, target_rpm: float):
    """پیشنهاد تعداد قطب برای رسیدن به دور مشخص."""
    if frequency <= 0 or target_rpm <= 0:
        raise ValueError("فرکانس و دور باید بزرگ‌تر از صفر باشند.")

    best = None
    for p in POLES:
        ns = (120 * frequency) / p
        diff = abs(ns - target_rpm)
        if best is None or diff < best["diff"]:
            best = {"poles": p, "sync_rpm": ns, "diff": diff}

    return best