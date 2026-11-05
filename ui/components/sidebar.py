# ui/components/sidebar.py
"""240px navigation sidebar with hover and active route styling."""

import tkinter as tk

from config.constants import ROUTES
from config.theme import (
    BG_HOVER,
    BG_SIDEBAR,
    BORDER,
    PRIMARY,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class Sidebar(tk.Frame):
    def __init__(self, master, font_family, on_navigate, routes=ROUTES, user=None):
        super().__init__(master, width=240, bg=BG_SIDEBAR, highlightthickness=0)
        self.pack_propagate(False)
        self.font_family = font_family
        self.on_navigate = on_navigate
        self.routes = tuple(routes)
        self.active_key = None
        self.user = user
        self._items: dict[str, tuple[tk.Frame, tk.Label, tk.Label]] = {}
        self._build()

    def _build(self):
        logo = tk.Frame(self, bg=BG_SIDEBAR)
        logo.pack(fill="x", padx=20, pady=(26, 34))
        mark = tk.Canvas(logo, width=38, height=38, bg=BG_SIDEBAR, highlightthickness=0)
        mark.create_oval(2, 2, 36, 36, fill=PRIMARY, outline="")
        mark.create_text(19, 19, text="⚡", fill=TEXT_PRIMARY, font=(self.font_family, 17, "bold"))
        mark.pack(side="left")
        tk.Label(
            logo,
            text="THE Eminence",
            bg=BG_SIDEBAR,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 14, "bold"),
        ).pack(side="left", padx=10)

        tk.Label(
            self, text="WORKSPACE", bg=BG_SIDEBAR, fg=TEXT_MUTED, font=(self.font_family, 8, "bold")
        ).pack(anchor="w", padx=24, pady=(0, 12))
        for key, title in self.routes:
            self._add_item(key, title)
        tk.Frame(self, bg=BG_SIDEBAR).pack(fill="both", expand=True)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=18, pady=(8, 12))
        avatar = tk.Label(
            self,
            text="E",
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 11, "bold"),
            width=3,
            height=1,
        )
        avatar.pack(side="bottom", anchor="w", padx=(20, 10), pady=(4, 20))
        info = tk.Frame(self, bg=BG_SIDEBAR)
        info.place(x=68, rely=1.0, y=-26, anchor="sw")
        name = self.user.full_name if self.user else "Administrator"
        role = self.user.role.title() if self.user else "Admin"
        tk.Label(
            info, text=name, bg=BG_SIDEBAR, fg=TEXT_PRIMARY, font=(self.font_family, 9, "bold")
        ).pack(anchor="w")
        tk.Label(
            info, text=role, bg=BG_SIDEBAR, fg=TEXT_SECONDARY, font=(self.font_family, 8)
        ).pack(anchor="w")

    def _add_item(self, key: str, title: str):
        item = tk.Frame(self, bg=BG_SIDEBAR, height=44, cursor="hand2")
        item.pack(fill="x", padx=(12, 14), pady=3)
        item.pack_propagate(False)
        indicator = tk.Frame(item, bg=BG_SIDEBAR, width=3)
        indicator.pack(side="left", fill="y")
        glyph = {
            "dashboard": "▦",
            "customers": "♙",
            "projects": "▣",
            "reports": "▤",
            "users": "♧",
            "settings": "⚙",
        }.get(key, "•")
        icon = tk.Label(
            item, text=glyph, bg=BG_SIDEBAR, fg=TEXT_SECONDARY, font=(self.font_family, 13), width=3
        )
        icon.pack(side="left", padx=(8, 2))
        label = tk.Label(
            item,
            text=title,
            bg=BG_SIDEBAR,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 10),
            anchor="w",
        )
        label.pack(side="left", fill="both", expand=True)
        self._items[key] = (item, indicator, label)
        for widget in (item, icon, label):
            widget.bind("<Button-1>", lambda _event, route=key: self._click(route))
            widget.bind("<Enter>", lambda _event, route=key: self._hover(route, True))
            widget.bind("<Leave>", lambda _event, route=key: self._hover(route, False))

    def _hover(self, key: str, enabled: bool):
        if key == self.active_key:
            return
        item, _indicator, label = self._items[key]
        color = BG_HOVER if enabled else BG_SIDEBAR
        item.configure(bg=color)
        for child in item.winfo_children():
            if child is not _indicator:
                child.configure(bg=color)
        label.configure(fg=TEXT_PRIMARY if enabled else TEXT_SECONDARY)

    def _click(self, key: str):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key: str):
        self.active_key = key
        for route, (item, indicator, label) in self._items.items():
            selected = route == key
            background = BG_HOVER if selected else BG_SIDEBAR
            item.configure(bg=background)
            indicator.configure(bg=PRIMARY if selected else BG_SIDEBAR)
            label.configure(bg=background, fg=TEXT_PRIMARY if selected else TEXT_SECONDARY)
            for child in item.winfo_children():
                if child not in (indicator, label):
                    child.configure(bg=background)
