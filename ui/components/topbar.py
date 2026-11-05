"""Application top navigation with global search, notifications, and account menu."""

import tkinter as tk

from PIL import Image, ImageDraw, ImageTk

from ui.theme import BG_HOVER, BG_SURFACE, BORDER, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY


class TopBar(tk.Frame):
    def __init__(
        self,
        master,
        font_family: str,
        user=None,
        on_search=None,
        on_notifications=None,
        on_logout=None,
    ):
        super().__init__(master, bg=BG_SURFACE, height=68, highlightthickness=1)
        self.configure(highlightbackground=BORDER)
        self.pack_propagate(False)
        self.font_family = font_family
        self.user = user
        self.on_search = on_search or (lambda _query="": None)
        self.on_notifications = on_notifications or (lambda: None)
        self.on_logout = on_logout or (lambda: None)
        self._build()

    def _build(self):
        right = tk.Frame(self, bg=BG_SURFACE)
        right.pack(side="right", fill="y", padx=(18, 12))

        self.search_entry = tk.Entry(
            right,
            bg="#0B0F19",
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 9),
            width=34,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PRIMARY,
        )
        self.search_entry.insert(0, "Search pages and projects…")
        self.search_entry.configure(fg=TEXT_SECONDARY)
        self.search_entry.bind("<FocusIn>", self._clear_hint)
        self.search_entry.bind("<Return>", self._submit_search)
        self.search_entry.pack(side="right", ipady=9, padx=(0, 8), pady=13)
        tk.Label(
            right,
            text="⌕",
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 17),
        ).pack(side="right", padx=(4, 8))

        left = tk.Frame(self, bg=BG_SURFACE)
        left.pack(side="left", fill="y", padx=(12, 18))
        self.notification_button = tk.Button(
            left,
            text="🔔",
            command=self.on_notifications,
            bg=BG_SURFACE,
            fg=TEXT_SECONDARY,
            activebackground=BG_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=(self.font_family, 15),
            width=3,
        )
        self.notification_button.pack(side="left", padx=(0, 8), pady=12)

        self.avatar_button = tk.Canvas(
            left,
            width=34,
            height=34,
            bg=BG_SURFACE,
            highlightthickness=0,
            cursor="hand2",
        )
        scale = 4
        avatar = Image.new("RGBA", (34 * scale, 34 * scale), (0, 0, 0, 0))
        ImageDraw.Draw(avatar).ellipse((2 * scale, 2 * scale, 32 * scale, 32 * scale), fill=PRIMARY)
        self._avatar_photo = ImageTk.PhotoImage(
            avatar.resize((34, 34), Image.Resampling.LANCZOS),
            master=self.avatar_button,
        )
        self.avatar_button.create_image(17, 17, image=self._avatar_photo)
        self.avatar_button.create_text(
            17,
            17,
            text=self._avatar_initial(),
            fill=TEXT_PRIMARY,
            font=(self.font_family, 10, "bold"),
        )
        self.avatar_button.bind("<Button-1>", lambda _event: self._show_account_menu())
        self.avatar_button.pack(side="left", pady=12)
        self.profile_name = tk.Label(
            left,
            text=getattr(self.user, "full_name", "Account"),
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            font=(self.font_family, 9, "bold"),
        )
        self.profile_name.pack(side="left", padx=(8, 0))

    def _avatar_initial(self):
        name = getattr(self.user, "full_name", "A")
        return (name[:1] or "A").upper()

    def _clear_hint(self, _event=None):
        if self.search_entry.get() == "Search pages and projects…":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg=TEXT_PRIMARY)

    def _submit_search(self, _event=None):
        query = self.search_entry.get().strip()
        if query and query != "Search pages and projects…":
            self.on_search(query)

    def focus_search(self):
        self._clear_hint()
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, "end")

    def _show_account_menu(self):
        menu = tk.Menu(
            self,
            tearoff=False,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            activebackground=BG_HOVER,
            activeforeground=TEXT_PRIMARY,
            font=(self.font_family, 9),
        )
        menu.add_command(label="Sign out", command=self.on_logout)
        x = self.avatar_button.winfo_rootx()
        y = self.avatar_button.winfo_rooty() + self.avatar_button.winfo_height()
        menu.tk_popup(x, y)
