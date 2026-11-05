# ui/components/modern_card.py
"""Pillow-backed rounded card container with a soft shadow and hover border."""

import tkinter as tk

from ui.components.pillow_utils import make_rounded_card
from ui.theme import BG_SURFACE, BORDER, PRIMARY


class ModernCard(tk.Frame):
    def __init__(
        self,
        master,
        width: int,
        height: int,
        radius: int = 16,
        shadow: bool = True,
        bg: str = BG_SURFACE,
        border_color: str | None = BORDER,
        padding: int = 12,
        hover: bool = True,
        **kwargs,
    ):
        if width < 1 or height < 1:
            raise ValueError("ModernCard width and height must be positive")
        self._card_width = width
        self._card_height = height
        self._radius = radius
        self._shadow = shadow
        self._card_bg = bg
        self._border_color = border_color
        self._hover = hover
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
        self.grid_propagate(False)
        from PIL import ImageTk

        self._photo = ImageTk.PhotoImage(image, master=self)
        self._background = tk.Label(self, image=self._photo, bd=0, highlightthickness=0)
        self._background.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(
            self,
            bg=bg,
            bd=0,
            highlightthickness=0,
            highlightbackground=border_color or bg,
        )
        self.body.place(
            x=self._pad + padding,
            y=self._pad + padding,
            width=max(1, width - 2 * padding),
            height=max(1, height - 2 * padding),
        )
        self._bind_hover(self)
        self._bind_hover(self._background)
        self._bind_hover(self.body)

    def _bind_hover(self, widget: tk.Widget) -> None:
        if not self._hover:
            return
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, _event=None) -> None:
        self._set_border(PRIMARY)

    def _on_leave(self, event=None) -> None:
        if event is not None:
            widget = self.winfo_containing(event.x_root, event.y_root)
            if widget is not None and (widget == self or str(widget).startswith(str(self))):
                return
        self._set_border(self._border_color)

    def _set_border(self, color: str | None) -> None:
        image, _ = make_rounded_card(
            self._card_width,
            self._card_height,
            self._radius,
            self._card_bg,
            color,
            self._shadow,
        )
        from PIL import ImageTk

        self._photo = ImageTk.PhotoImage(image, master=self)
        self._background.configure(image=self._photo)
