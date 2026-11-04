"""محاسبات کامل مدارهای RLC — سری و موازی."""

import math
from dataclasses import dataclass


@dataclass
class CircuitResult:
    """نتیجه جامع محاسبه مدار."""
    # نوع مدار
    circuit_type: str   # RL | RC | LC | RLC
    topology: str       # series | parallel

    # راکتانس‌ها
    xl: float = 0.0
    xc: float = 0.0

    # امپدانس
    z: float = 0.0

    # زاویه فاز
    phase_deg: float = 0.0

    # ضریب توان
    power_factor: float = 1.0
    sin_phi: float = 0.0
    tan_phi: float = 0.0

    # جریان‌ها
    total_current: float = 0.0
    current_r: float = 0.0
    current_l: float = 0.0
    current_c: float = 0.0

    # ولتاژها
    voltage_r: float = 0.0
    voltage_l: float = 0.0
    voltage_c: float = 0.0

    # توان‌ها
    p: float = 0.0     # توان اکتیو (W)
    q: float = 0.0     # توان راکتیو (VAR)
    s: float = 0.0     # توان ظاهری (VA)

    # وضعیت
    is_inductive: bool = True
    is_resonance: bool = False
    note: str = ""


# ========================================================
# راکتانس‌ها
# ========================================================
def calc_xl(frequency: float, inductance: float) -> float:
    if frequency <= 0 or inductance <= 0:
        return 0.0
    return 2 * math.pi * frequency * inductance


def calc_xc(frequency: float, capacitance: float) -> float:
    if frequency <= 0 or capacitance <= 0:
        return 0.0
    return 1.0 / (2 * math.pi * frequency * capacitance)


# ========================================================
# مدارهای سری
# ========================================================
def calc_series_rl(voltage, resistance, inductance, frequency):
    """مدار RL سری."""
    xl = calc_xl(frequency, inductance)
    z = math.sqrt(resistance ** 2 + xl ** 2)

    phase_rad = math.atan2(xl, resistance)
    phase_deg = math.degrees(phase_rad)
    pf = math.cos(phase_rad)

    current = voltage / z
    vr = current * resistance
    vl = current * xl

    s = voltage * current
    p = s * pf
    q = s * math.sin(phase_rad)

    return CircuitResult(
        circuit_type="RL", topology="series",
        xl=xl, xc=0, z=z,
        phase_deg=phase_deg, power_factor=pf,
        sin_phi=math.sin(phase_rad), tan_phi=math.tan(phase_rad),
        total_current=current,
        current_r=current, current_l=current, current_c=0,
        voltage_r=vr, voltage_l=vl, voltage_c=0,
        p=p, q=q, s=s,
        is_inductive=True,
    )


def calc_series_rc(voltage, resistance, capacitance, frequency):
    """مدار RC سری."""
    xc = calc_xc(frequency, capacitance)
    z = math.sqrt(resistance ** 2 + xc ** 2)

    phase_rad = math.atan2(-xc, resistance)
    phase_deg = math.degrees(phase_rad)
    pf = math.cos(phase_rad)

    current = voltage / z
    vr = current * resistance
    vc = current * xc

    s = voltage * current
    p = s * pf
    q = s * math.sin(phase_rad)

    return CircuitResult(
        circuit_type="RC", topology="series",
        xl=0, xc=xc, z=z,
        phase_deg=phase_deg, power_factor=pf,
        sin_phi=math.sin(phase_rad), tan_phi=math.tan(phase_rad),
        total_current=current,
        current_r=current, current_l=0, current_c=current,
        voltage_r=vr, voltage_l=0, voltage_c=vc,
        p=p, q=q, s=s,
        is_inductive=False,
    )


def calc_series_lc(voltage, inductance, capacitance, frequency):
    """مدار LC سری."""
    xl = calc_xl(frequency, inductance)
    xc = calc_xc(frequency, capacitance)
    x_total = xl - xc

    if abs(x_total) < 1e-9:
        # رزونانس
        return CircuitResult(
            circuit_type="LC", topology="series",
            xl=xl, xc=xc, z=0,
            phase_deg=0, power_factor=1.0,
            total_current=float('inf'),
            voltage_l=xl, voltage_c=xc,
            is_inductive=True,
            is_resonance=True,
            note="⚠️ رزونانس — امپدانس صفر، جریان بی‌نهایت",
        )

    z = abs(x_total)
    phase_deg = 90.0 if x_total > 0 else -90.0
    current = voltage / z

    vl = current * xl
    vc = current * xc

    return CircuitResult(
        circuit_type="LC", topology="series",
        xl=xl, xc=xc, z=z,
        phase_deg=phase_deg, power_factor=0.0,
        sin_phi=1.0 if x_total > 0 else -1.0, tan_phi=0,
        total_current=current,
        current_l=current, current_c=current,
        voltage_l=vl, voltage_c=vc,
        p=0, q=voltage * current, s=voltage * current,
        is_inductive=(x_total > 0),
    )


def calc_series_rlc(voltage, resistance, inductance, capacitance, frequency):
    """مدار RLC سری."""
    xl = calc_xl(frequency, inductance)
    xc = calc_xc(frequency, capacitance)
    x_total = xl - xc

    z = math.sqrt(resistance ** 2 + x_total ** 2)
    phase_rad = math.atan2(x_total, resistance)
    phase_deg = math.degrees(phase_rad)
    pf = math.cos(phase_rad)

    current = voltage / z
    vr = current * resistance
    vl = current * xl
    vc = current * xc

    s = voltage * current
    p = s * pf
    q = s * math.sin(phase_rad)

    note = ""
    is_res = abs(x_total) < 1e-6 * max(xl, xc, 1)
    if is_res:
        note = "🎯 رزونانس — Z = R، جریان حداکثر"

    return CircuitResult(
        circuit_type="RLC", topology="series",
        xl=xl, xc=xc, z=z,
        phase_deg=phase_deg, power_factor=pf,
        sin_phi=math.sin(phase_rad), tan_phi=math.tan(phase_rad),
        total_current=current,
        current_r=current, current_l=current, current_c=current,
        voltage_r=vr, voltage_l=vl, voltage_c=vc,
        p=p, q=q, s=s,
        is_inductive=(x_total > 0),
        is_resonance=is_res,
        note=note,
    )


# ========================================================
# مدارهای موازی
# ========================================================
def calc_parallel_rl(voltage, resistance, inductance, frequency):
    """مدار RL موازی."""
    xl = calc_xl(frequency, inductance)

    ir = voltage / resistance
    il = voltage / xl if xl > 0 else 0

    i_total = math.sqrt(ir ** 2 + il ** 2)

    # امپدانس
    z = voltage / i_total if i_total > 0 else 0

    # زاویه فاز
    phase_rad = math.atan2(-il, ir)  # جریان عقب‌تره
    phase_deg = math.degrees(phase_rad)
    pf = math.cos(phase_rad)

    s = voltage * i_total
    p = s * pf
    q = s * math.sin(phase_rad)

    return CircuitResult(
        circuit_type="RL", topology="parallel",
        xl=xl, xc=0, z=z,
        phase_deg=phase_deg, power_factor=pf,
        sin_phi=math.sin(phase_rad), tan_phi=math.tan(phase_rad),
        total_current=i_total,
        current_r=ir, current_l=il, current_c=0,
        voltage_r=voltage, voltage_l=voltage, voltage_c=0,
        p=p, q=q, s=s,
        is_inductive=True,
    )


def calc_parallel_rc(voltage, resistance, capacitance, frequency):
    """مدار RC موازی."""
    xc = calc_xc(frequency, capacitance)

    ir = voltage / resistance
    ic = voltage / xc if xc > 0 else 0

    i_total = math.sqrt(ir ** 2 + ic ** 2)
    z = voltage / i_total if i_total > 0 else 0

    phase_rad = math.atan2(ic, ir)
    phase_deg = math.degrees(phase_rad)
    pf = math.cos(phase_rad)

    s = voltage * i_total
    p = s * pf
    q = s * math.sin(phase_rad)

    return CircuitResult(
        circuit_type="RC", topology="parallel",
        xl=0, xc=xc, z=z,
        phase_deg=phase_deg, power_factor=pf,
        sin_phi=math.sin(phase_rad), tan_phi=math.tan(phase_rad),
        total_current=i_total,
        current_r=ir, current_l=0, current_c=ic,
        voltage_r=voltage, voltage_l=0, voltage_c=voltage,
        p=p, q=q, s=s,
        is_inductive=False,
    )


def calc_parallel_lc(voltage, inductance, capacitance, frequency):
    """مدار LC موازی."""
    xl = calc_xl(frequency, inductance)
    xc = calc_xc(frequency, capacitance)

    il = voltage / xl if xl > 0 else 0
    ic = voltage / xc if xc > 0 else 0

    i_total = abs(il - ic)
    z = voltage / i_total if i_total > 0 else float('inf')

    is_res = abs(il - ic) < 1e-9
    note = ""
    if is_res:
        note = "🎯 رزونانس موازی — جریان کل صفر، امپدانس بی‌نهایت"

    phase_deg = 90.0 if il > ic else -90.0
    pf = 0.0

    return CircuitResult(
        circuit_type="LC", topology="parallel",
        xl=xl, xc=xc, z=z,
        phase_deg=phase_deg, power_factor=pf,
        total_current=i_total,
        current_l=il, current_c=ic,
        voltage_l=voltage, voltage_c=voltage,
        p=0, q=voltage * i_total, s=voltage * i_total,
        is_inductive=(il > ic),
        is_resonance=is_res,
        note=note,
    )


def calc_parallel_rlc(voltage, resistance, inductance, capacitance, frequency):
    """مدار RLC موازی."""
    xl = calc_xl(frequency, inductance)
    xc = calc_xc(frequency, capacitance)

    ir = voltage / resistance if resistance > 0 else 0
    il = voltage / xl if xl > 0 else 0
    ic = voltage / xc if xc > 0 else 0

    # جریان‌های اکتیو و راکتیو
    i_reactive = il - ic
    i_total = math.sqrt(ir ** 2 + i_reactive ** 2)

    z = voltage / i_total if i_total > 0 else float('inf')

    phase_rad = math.atan2(-i_reactive, ir)
    phase_deg = math.degrees(phase_rad)
    pf = math.cos(phase_rad)

    s = voltage * i_total
    p = s * pf
    q = s * math.sin(phase_rad)

    is_res = abs(i_reactive) < 1e-9
    note = ""
    if is_res:
        note = "🎯 رزونانس — فقط جریان مقاومتی"

    return CircuitResult(
        circuit_type="RLC", topology="parallel",
        xl=xl, xc=xc, z=z,
        phase_deg=phase_deg, power_factor=pf,
        sin_phi=math.sin(phase_rad), tan_phi=math.tan(phase_rad),
        total_current=i_total,
        current_r=ir, current_l=il, current_c=ic,
        voltage_r=voltage, voltage_l=voltage, voltage_c=voltage,
        p=p, q=q, s=s,
        is_inductive=(i_reactive > 0),
        is_resonance=is_res,
        note=note,
    )


# ========================================================
# رزونانس
# ========================================================
def calc_resonance_frequency(inductance, capacitance):
    """فرکانس رزونانس f₀ = 1/(2π√LC)."""
    if inductance <= 0 or capacitance <= 0:
        raise ValueError("L و C باید بزرگ‌تر از صفر باشند.")
    return 1.0 / (2 * math.pi * math.sqrt(inductance * capacitance))


def calc_quality_factor(inductance, capacitance, resistance):
    """ضریب کیفیت Q = (1/R)√(L/C)."""
    if resistance <= 0:
        raise ValueError("مقاومت باید بزرگ‌تر از صفر باشد.")
    if inductance <= 0 or capacitance <= 0:
        raise ValueError("L و C باید بزرگ‌تر از صفر باشند.")
    return (1.0 / resistance) * math.sqrt(inductance / capacitance)


def calc_bandwidth(f0, q):
    """پهنای باند BW = f₀/Q."""
    if q <= 0:
        return 0
    return f0 / q