"""Collapsible right-to-left workspace navigation."""

import tkinter as tk

from ui.theme import (
    BG_HOVER,
    BG_SIDEBAR,
    BORDER,
    PRIMARY,
    SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_WIDTH,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class Sidebar(tk.Frame):
    def __init__(self, master, font_family, on_navigate, routes, user=None):
        super().__init__(master, width=SIDEBAR_WIDTH, bg=BG_SIDEBAR, highlightthickness=0)
        self.pack_propagate(False)
        self.font_family = font_family
        self.on_navigate = on_navigate
        self.routes = tuple(routes)
        self.user = user
        self.active_key = None
        self.expanded = True
        self._items: dict[str, tuple[tk.Frame, tk.Frame, tk.Label, tk.Label]] = {}
        self._build()

    def _build(self):
        self.header = tk.Frame(self, bg=BG_SIDEBAR, height=76)
        self.header.pack(fill="x", padx=12, pady=(12, 8))
        self.header.pack_propagate(False)

        self.toggle = tk.Button(
            self.header,
            text="☰",
            command=self.toggle_collapsed,
            bg=BG_SIDEBAR,
            fg=TEXT_SECONDARY,
            activebackground=BG_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=(self.font_family, 15),
            width=3,
        )
        self.toggle.pack(side="left", fill="y")
        self.brand = tk.Frame(self.header, bg=BG_SIDEBAR)
        self.brand.pack(side="right", fill="y", expand=True)
        tk.Label(
            self.brand,
            text="⚡",
            bg=BG_SIDEBAR,
            fg=PRIMARY,
            font=(self.font_family, 21, "bold"),
        ).pack(side="right", padx=(8, 2))
        self.brand_name = tk.Label(
            self.brand,
            text="THE Eminence",
            bg=BG_SIDEBAR,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 12, "bold"),
            anchor="e",
        )
        self.brand_name.pack(side="right", fill="x", expand=True)

        tk.Frame(self, height=1, bg=BORDER).pack(fill="x", padx=14, pady=(0, 12))
        self.section_label = tk.Label(
            self,
            text="WORKSPACE",
            bg=BG_SIDEBAR,
            fg=TEXT_MUTED,
            font=(self.font_family, 8, "bold"),
            anchor="e",
        )
        self.section_label.pack(fill="x", padx=20, pady=(0, 8))

        nav_host = tk.Frame(self, bg=BG_SIDEBAR)
        nav_host.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(nav_host, bg=BG_SIDEBAR, highlightthickness=0, borderwidth=0)
        scrollbar = tk.Scrollbar(nav_host, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side="right", fill="both", expand=True)
        self._nav = tk.Frame(self._canvas, bg=BG_SIDEBAR)
        self._nav_window = self._canvas.create_window(
            (0, 0), window=self._nav, anchor="nw", tags=("navigation",)
        )
        self._nav.bind(
            "<Configure>",
            lambda _event: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind(
            "<Configure>",
            lambda event: self._canvas.itemconfigure(self._nav_window, width=event.width),
        )
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        for key, title in self.routes:
            self._add_item(key, title)

        footer = tk.Frame(self, bg=BG_SIDEBAR)
        footer.pack(side="bottom", fill="x", padx=14, pady=(8, 16))
        tk.Frame(footer, height=1, bg=BORDER).pack(fill="x", pady=(0, 12))
        self.avatar = tk.Label(
            footer,
            text=self._initial(),
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 10, "bold"),
            width=3,
            height=1,
        )
        self.avatar.pack(side="right", padx=(0, 8))
        self.user_info = tk.Frame(footer, bg=BG_SIDEBAR)
        self.user_info.pack(side="right", fill="x", expand=True)
        tk.Label(
            self.user_info,
            text=getattr(self.user, "full_name", "Administrator"),
            bg=BG_SIDEBAR,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 9, "bold"),
            anchor="e",
        ).pack(fill="x")
        tk.Label(
            self.user_info,
            text=getattr(self.user, "role", "Admin").title(),
            bg=BG_SIDEBAR,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 8),
            anchor="e",
        ).pack(fill="x")

    def _initial(self) -> str:
        name = getattr(self.user, "full_name", "A")
        return (name[:1] or "A").upper()

    def _on_mousewheel(self, event):
        if event.delta:
            self._canvas.yview_scroll(int(-event.delta / 120), "units")

    def _add_item(self, key: str, title: str):
        item = tk.Frame(self._nav, bg=BG_SIDEBAR, height=42, cursor="hand2")
        item.pack(fill="x", padx=8, pady=2)
        item.pack_propagate(False)
        indicator = tk.Frame(item, bg=BG_SIDEBAR, width=3)
        indicator.pack(side="right", fill="y")
        icon = {
            "dashboard": "▦",
            "customers": "♙",
            "projects": "▣",
            "reports": "▤",
            "users": "♧",
            "settings": "⚙",
        }.get(key, "•")
        icon_label = tk.Label(
            item,
            text=icon,
            bg=BG_SIDEBAR,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 13),
            width=3,
        )
        icon_label.pack(side="right", padx=(3, 5))
        text_label = tk.Label(
            item,
            text=title,
            bg=BG_SIDEBAR,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 9),
            anchor="e",
        )
        text_label.pack(side="right", fill="both", expand=True, padx=(4, 10))
        self._items[key] = (item, indicator, icon_label, text_label)
        for widget in (item, indicator, icon_label, text_label):
            widget.bind("<Button-1>", lambda _event, route=key: self._click(route))
            widget.bind("<Enter>", lambda _event, route=key: self._hover(route, True))
            widget.bind("<Leave>", lambda _event, route=key: self._hover(route, False))

    def _hover(self, key: str, enabled: bool):
        if key == self.active_key:
            return
        item, indicator, icon, label = self._items[key]
        background = BG_HOVER if enabled else BG_SIDEBAR
        item.configure(bg=background)
        indicator.configure(bg=background)
        icon.configure(bg=background, fg=TEXT_PRIMARY if enabled else TEXT_SECONDARY)
        label.configure(bg=background, fg=TEXT_PRIMARY if enabled else TEXT_SECONDARY)

    def _click(self, key: str):
        if key not in self._items:
            return
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key: str):
        self.active_key = key
        for route, (item, indicator, icon, label) in self._items.items():
            selected = route == key
            background = BG_HOVER if selected else BG_SIDEBAR
            item.configure(bg=background)
            indicator.configure(bg=PRIMARY if selected else BG_SIDEBAR)
            icon.configure(bg=background, fg=PRIMARY if selected else TEXT_SECONDARY)
            label.configure(bg=background, fg=TEXT_PRIMARY if selected else TEXT_SECONDARY)

    def toggle_collapsed(self):
        self.expanded = not self.expanded
        width = SIDEBAR_WIDTH if self.expanded else SIDEBAR_COLLAPSED_WIDTH
        self.configure(width=width)
        if self.expanded:
            self.brand_name.pack(side="right", fill="x", expand=True)
        else:
            self.brand_name.pack_forget()
        self.section_label.configure(text="WORKSPACE" if self.expanded else "")
        if self.expanded:
            self.user_info.pack(side="right", fill="x", expand=True)
        else:
            self.user_info.pack_forget()
        for _item, _indicator, _icon, label in self._items.values():
            if self.expanded:
                label.pack(side="right", fill="both", expand=True, padx=(4, 10))
            else:
                label.pack_forget()
