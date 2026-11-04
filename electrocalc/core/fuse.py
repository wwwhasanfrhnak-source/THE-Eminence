"""انتخاب فیوز مناسب."""

# رده‌های استاندارد فیوز (آمپر)
STANDARD_FUSES = [2, 4, 6, 10, 16, 20, 25, 32, 40, 50, 63, 80,
                  100, 125, 160, 200, 250, 315, 400, 500, 630]


def select_fuse(current: float, factor: float = 1.25) -> int:
    """
    انتخاب فیوز استاندارد.

    پارامترها:
        current: جریان نامی مدار (A)
        factor : ضریب اطمینان (پیش‌فرض ۱.۲۵)

    خروجی:
        آمپر فیوز استاندارد
    """
    if current <= 0:
        raise ValueError("جریان باید بزرگ‌تر از صفر باشد.")
    if factor < 1:
        raise ValueError("ضریب اطمینان باید حداقل ۱ باشد.")

    required = current * factor
    for fuse in STANDARD_FUSES:
        if fuse >= required:
            return fuse
    raise ValueError(f"جریان خیلی بالاست (بیشتر از {STANDARD_FUSES[-1]} A).")