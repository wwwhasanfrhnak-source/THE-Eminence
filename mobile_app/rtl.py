"""Persian text shaping for Kivy's left-to-right text renderer."""

import arabic_reshaper
from bidi.algorithm import get_display


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(str(text)))


def rtl_lines(text: str, max_chars: int = 30) -> str:
    """Shape RTL text line by line so wrapped lines keep their order.

    Kivy wraps the mirrored string left-to-right, which reverses the visual
    order of lines when a whole sentence is passed through ``rtl`` at once.
    """
    words = str(text).split()
    lines = []
    current = []
    length = 0
    for word in words:
        if current and length + len(word) + 1 > max_chars:
            lines.append(" ".join(current))
            current, length = [word], len(word)
        else:
            current.append(word)
            length += len(word) + 1
    if current:
        lines.append(" ".join(current))
    return "\n".join(rtl(line) for line in lines)