"""Compatibility exports for the shared UI design tokens."""

from ui.theme import (
    BG_HOVER,
    BG_MAIN,
    BG_SIDEBAR,
    BORDER,
    DANGER,
    FONT_FALLBACKS,
    PRIMARY,
    PURPLE,
    SECONDARY,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
)
from ui.theme import (
    BG_SURFACE as BG_CARD,
)

__all__ = [
    "BG_CARD",
    "BG_HOVER",
    "BG_MAIN",
    "BG_SIDEBAR",
    "BORDER",
    "DANGER",
    "FONT_CANDIDATES",
    "PRIMARY",
    "PURPLE",
    "SECONDARY",
    "SUCCESS",
    "TEXT_MUTED",
    "TEXT_PRIMARY",
    "TEXT_SECONDARY",
    "WARNING",
]

FONT_CANDIDATES = FONT_FALLBACKS
