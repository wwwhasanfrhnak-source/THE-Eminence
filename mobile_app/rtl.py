"""Persian text shaping for Kivy's left-to-right text renderer."""

import arabic_reshaper
from bidi.algorithm import get_display


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(str(text)))