"""اسکرول‌بار مدرن — هماهنگ با تم."""

import tkinter as tk


class ModernScrollbar(tk.Canvas):
    """اسکرول‌بار نازک و مدرن."""

    def __init__(self, parent, command, width=10,
                 track_color="#e5e7eb", thumb_color="#9ca3af",
                 thumb_hover="#6b7280"):
        super().__init__(parent, width=width, highlightthickness=0,
                          bg=track_color, cursor="hand2")
        self.command = command
        self._w = width
        self.track_color = track_color
        self.thumb_color = thumb_color
        self.thumb_hover = thumb_hover
        self._first = 0.0
        self._last = 1.0
        self._thumb_id = None
        self._drag_start = 0

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Enter>", lambda e: self._redraw(hover=True))
        self.bind("<Leave>", lambda e: self._redraw())

    def set(self, first, last):
        self._first = float(first)
        self._last = float(last)
        self._redraw()

    def _redraw(self, hover=False):
        self.delete("all")
        h = self.winfo_height()
        if h < 10:
            return

        # طول نوار
        total = self._last - self._first
        if total >= 0.999:
            return  # نیازی به اسکرول نیست

        y1 = int(self._first * h)
        y2 = int(self._last * h)
        y1 = max(0, min(y1, h - 20))
        y2 = max(y1 + 20, min(y2, h))

        color = self.thumb_hover if hover else self.thumb_color
        pad = 2
        self._thumb_id = self.create_rectangle(
            0, y1, self._w, y2,
            fill=color, outline="",
        )

    def _on_press(self, event):
        h = self.winfo_height()
        y = event.y

        if self._thumb_id:
            coords = self.coords(self._thumb_id)
            if coords and coords[1] <= y <= coords[3]:
                self._drag_start = y
                return
        # کلیک روی track → پرش
        frac = y / max(h, 1)
        self.command("moveto", str(frac))

    def _on_drag(self, event):
        h = self.winfo_height()
        delta = (event.y - self._drag_start) / max(h, 1)
        self.command("moveto", str(self._first + delta))