# utils/fonts.py
"""Select an installed font with Vazirmatn and Segoe UI preference."""

import tkinter.font as tkfont

from config.theme import FONT_CANDIDATES


def get_font_family(root) -> str:
    available = set(tkfont.families(root))
    return next((name for name in FONT_CANDIDATES if name in available), "TkDefaultFont")
