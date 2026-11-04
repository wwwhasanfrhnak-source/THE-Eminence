"""محاسبه افت ولتاژ کابل."""

import math
from dataclasses import dataclass

# مقاومت ویژه مس و آلومینیوم (Ω·mm²/m)
RHO_COPPER = 0.0175
RHO_ALUMINUM = 0.028


@dataclass
class VoltageDropResult:
    drop_v: float          # افت ولتاژ (ولت)
    drop_percent: float    # درصد افت
    end_voltage: float     # ولتاژ انتهای خط


def calc_voltage_drop(
    voltage: float,
    current: float,
    length: float,
    cross_section: float,
    material: str = "copper",
    three_phase: bool = False,
    cos_phi: float = 1.0,
) -> VoltageDropResult:
    """
    افت ولتاژ = (ρ × L × I × ضریب) / A

    پارامترها:
        voltage      : ولتاژ (V)
        current      : جریان (A)
        length       : طول کابل (متر)
        cross_section: سطح مقطع (mm²)
        material     : copper یا aluminum
        three_phase  : True برای سه‌فاز
        cos_phi      : ضریب توان
    """
    if voltage <= 0:
        raise ValueError("ولتاژ باید بزرگ‌تر از صفر باشد.")
    if current <= 0:
        raise ValueError("جریان باید بزرگ‌تر از صفر باشد.")
    if length <= 0:
        raise ValueError("طول کابل باید بزرگ‌تر از صفر باشد.")
    if cross_section <= 0:
        raise ValueError("سطح مقطع باید بزرگ‌تر از صفر باشد.")
    if not (0 < cos_phi <= 1):
        raise ValueError("ضریب توان باید بین ۰ و ۱ باشد.")

    rho = RHO_COPPER if material.lower() == "copper" else RHO_ALUMINUM

    # ضریب فرمول
    if three_phase:
        factor = math.sqrt(3)
    else:
        factor = 2  # رفت و برگشت

    # افت ولتاژ
    drop_v = (factor * rho * length * current * cos_phi) / cross_section

    # درصد
    drop_percent = (drop_v / voltage) * 100
    end_voltage = voltage - drop_v

    return VoltageDropResult(
        drop_v=drop_v,
        drop_percent=drop_percent,
        end_voltage=end_voltage,
    )