"""تبدیل ستاره ↔ مثلث.

ستاره (Y): سه مقاومت به نقطه‌ی مشترک (نول) وصلند.
مثلث (Δ): سه مقاومت به‌صورت حلقه بسته وصلند.

فرمول‌ها:
    Y → Δ:
        R_AB = (R_A × R_B + R_B × R_C + R_C × R_A) / R_C
        R_BC = (R_A × R_B + R_B × R_C + R_C × R_A) / R_A
        R_CA = (R_A × R_B + R_B × R_C + R_C × R_A) / R_B

    Δ → Y:
        R_A = (R_AB × R_CA) / (R_AB + R_BC + R_CA)
        R_B = (R_AB × R_BC) / (R_AB + R_BC + R_CA)
        R_C = (R_BC × R_CA) / (R_AB + R_BC + R_CA)
"""

from dataclasses import dataclass


@dataclass
class StarResult:
    """نتیجه تبدیل به ستاره."""
    r_a: float
    r_b: float
    r_c: float


@dataclass
class DeltaResult:
    """نتیجه تبدیل به مثلث."""
    r_ab: float
    r_bc: float
    r_ca: float


def star_to_delta(r_a: float, r_b: float, r_c: float) -> DeltaResult:
    """تبدیل آرایش ستاره به مثلث."""
    if r_a <= 0 or r_b <= 0 or r_c <= 0:
        raise ValueError("مقاومت‌ها باید بزرگ‌تر از صفر باشند.")

    s = r_a * r_b + r_b * r_c + r_c * r_a

    r_ab = s / r_c
    r_bc = s / r_a
    r_ca = s / r_b

    return DeltaResult(r_ab=r_ab, r_bc=r_bc, r_ca=r_ca)


def delta_to_star(r_ab: float, r_bc: float, r_ca: float) -> StarResult:
    """تبدیل آرایش مثلث به ستاره."""
    if r_ab <= 0 or r_bc <= 0 or r_ca <= 0:
        raise ValueError("مقاومت‌ها باید بزرگ‌تر از صفر باشند.")

    total = r_ab + r_bc + r_ca

    r_a = (r_ab * r_ca) / total
    r_b = (r_ab * r_bc) / total
    r_c = (r_bc * r_ca) / total

    return StarResult(r_a=r_a, r_b=r_b, r_c=r_c)