"""قاب پایه قابل اسکرول — با اعمال زنده سرعت و حالت."""

import tkinter as tk
from tkinter import ttk


SCROLL_ALWAYS = "always"
SCROLL_HIDDEN = "hidden"
SCROLL_THIN = "thin"
SCROLL_SMART = "smart"
SCROLL_TOUCH = "touch"


# ⭐ متغیرهای سراسری — برای اعمال زنده
_current_speed = 0.5
_current_mode = "always"


def _load_from_db():
    """خوندن از پایگاه داده یه بار."""
    global _current_speed, _current_mode
    try:
        from electrocalc.core import settings as st
        _current_speed = max(0.05, min(2.0,
                                        float(st.get_setting("scroll_speed", "0.5"))))
        _current_mode = st.get_setting("scroll_mode", SCROLL_ALWAYS)
    except Exception:
        pass


def get_scroll_mode():
    global _current_mode
    _load_from_db()
    return _current_mode


def get_scroll_speed():
    global _current_speed
    _load_from_db()
    return _current_speed


def set_scroll_speed(value):
    """از تنظیمات صدا زده می‌شه — زنده اعمال می‌شه."""
    global _current_speed
    try:
        _current_speed = max(0.05, min(2.0, float(value)))
    except Exception:
        pass


def set_scroll_mode(value):
    """از تنظیمات صدا زده می‌شه."""
    global _current_mode
    _current_mode = value


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, padding=20, bg=None):
        super().__init__(parent)
        self._pad = padding
        self._bg = bg
        self._mode = get_scroll_mode()
        self._scrollbar = None
        self._drag_data = {"y": 0, "x": 0, "scrolling": False}
        self._build_scrollable()

    def _build_scrollable(self):
        if self._bg:
            container = tk.Frame(self, bg=self._bg)
        else:
            container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas_kw = {"highlightthickness": 0, "borderwidth": 0}
        if self._bg:
            canvas_kw["bg"] = self._bg
        self.canvas = tk.Canvas(container, **canvas_kw)

        if self._mode == SCROLL_ALWAYS:
            self._scrollbar = ttk.Scrollbar(container, orient="vertical",
                                              command=self.canvas.yview)
            self._scrollbar.pack(side="left", fill="y")
            self.canvas.configure(yscrollcommand=self._scrollbar.set)

        elif self._mode == SCROLL_THIN:
            self._scrollbar = tk.Scrollbar(
                container, orient="vertical",
                command=self.canvas.yview,
                width=6, troughcolor="#e5e7eb",
                bg="#9ca3af", activebackground="#6b7280",
                borderwidth=0, highlightthickness=0, relief="flat",
            )
            self._scrollbar.pack(side="left", fill="y")
            self.canvas.configure(yscrollcommand=self._scrollbar.set)

        elif self._mode == SCROLL_SMART:
            self._scrollbar = ttk.Scrollbar(container, orient="vertical",
                                              command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=self._smart_yscroll)
            self.canvas.bind("<Enter>", self._smart_show)
            self.canvas.bind("<Leave>", self._smart_hide)

        elif self._mode == SCROLL_TOUCH:
            self._scrollbar = ttk.Scrollbar(container, orient="vertical",
                                              command=self.canvas.yview)
            style = ttk.Style()
            style.configure("Touch.Vertical.TScrollbar",
                             width=28, arrowsize=22)
            self._scrollbar.configure(style="Touch.Vertical.TScrollbar")
            self._scrollbar.pack(side="left", fill="y")
            self.canvas.configure(yscrollcommand=self._scrollbar.set)

        self.canvas.pack(side="right", fill="both", expand=True)

        if self._bg:
            self.inner = tk.Frame(self.canvas, padx=self._pad, pady=self._pad,
                                   bg=self._bg)
        else:
            self.inner = ttk.Frame(self.canvas, padding=self._pad)

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_config)
        self.canvas.bind("<Configure>", self._on_canvas_config)

        self.canvas.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.inner.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind("<Button-4>", self._on_mousewheel, add="+")
        self.canvas.bind("<Button-5>", self._on_mousewheel, add="+")

        if self._mode == SCROLL_TOUCH:
            self._bind_touch(self.canvas)
            self._bind_touch(self.inner)

    def _on_mousewheel(self, event):
        try:
            if not self.winfo_ismapped():
                return

            speed = _current_speed

            delta = event.delta if hasattr(event, "delta") else 0
            if event.num == 4:
                delta = 120
            elif event.num == 5:
                delta = -120

            step_float = -1 * (delta / 120) * speed

            if step_float >= 1:
                step = int(step_float)
            elif step_float <= -1:
                step = int(step_float)
            elif step_float > 0:
                step = 1
            elif step_float < 0:
                step = -1
            else:
                return

            self.canvas.yview_scroll(step, "units")
        except Exception:
            pass

    def _bind_touch(self, widget):
        widget.bind("<Button-1>", self._on_touch_start, add="+")
        widget.bind("<B1-Motion>", self._on_touch_move, add="+")
        widget.bind("<ButtonRelease-1>", self._on_touch_end, add="+")

    def _on_touch_start(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
        self._drag_data["scrolling"] = False

    def _on_touch_move(self, event):
        if self._drag_data["y"] == 0:
            return
        dy = event.y_root - self._drag_data["y"]
        dx = event.x_root - self._drag_data["x"]

        if abs(dx) > abs(dy) and not self._drag_data["scrolling"]:
            return

        if not self._drag_data["scrolling"]:
            if abs(dy) < 5:
                return
            self._drag_data["scrolling"] = True

        try:
            speed = _current_speed
            step_float = -1 * dy * speed * 0.5
            step = int(step_float)
            if step == 0:
                return
            self.canvas.yview_scroll(step, "units")
        except Exception:
            pass

        self._drag_data["y"] = event.y_root
        self._drag_data["x"] = event.x_root

    def _on_touch_end(self, event):
        self._drag_data["scrolling"] = False

    def _smart_yscroll(self, first, last):
        if self._scrollbar:
            self._scrollbar.set(first, last)
        try:
            if float(first) <= 0 and float(last) >= 1:
                if self._scrollbar and self._scrollbar.winfo_ismapped():
                    self._scrollbar.pack_forget()
            else:
                if (self._scrollbar and
                        not self._scrollbar.winfo_ismapped()):
                    self._scrollbar.pack(side="left", fill="y",
                                          before=self.canvas)
        except Exception:
            pass

    def _smart_show(self, e=None):
        try:
            if self._scrollbar and not self._scrollbar.winfo_ismapped():
                self._scrollbar.pack(side="left", fill="y", before=self.canvas)
        except Exception:
            pass

    def _smart_hide(self, e=None):
        try:
            if self._scrollbar:
                first, last = self.canvas.yview()
                if float(first) <= 0 and float(last) >= 1:
                    self._scrollbar.pack_forget()
        except Exception:
            pass

    def _on_inner_config(self, event):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass

    def _on_canvas_config(self, event):
        try:
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        except Exception:
            pass