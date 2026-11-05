# ui/components/modern_card.py
"""Pillow-backed rounded card container."""

import tkinter as tk

from config.theme import BG_CARD
from ui.components.pillow_utils import make_rounded_card


class ModernCard(tk.Frame):
    def __init__(
        self,
        master,
        width: int,
        height: int,
        radius: int = 16,
        shadow: bool = True,
        bg: str = BG_CARD,
        border_color: str | None = None,
        padding: int = 12,
        **kwargs,
    ):
        self._card_width = width
        self._card_height = height
        image, self._pad = make_rounded_card(width, height, radius, bg, border_color, shadow)
        super().__init__(
            master,
            width=image.width,
            height=image.height,
            bg=master.cget("bg"),
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.pack_propagate(False)
        from PIL import ImageTk

        self._photo = ImageTk.PhotoImage(image, master=self)
        self._background = tk.Label(self, image=self._photo, bd=0, highlightthickness=0)
        self._background.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self.body.place(
            x=self._pad + padding,
            y=self._pad + padding,
            width=max(1, width - 2 * padding),
            height=max(1, height - 2 * padding),
        )
