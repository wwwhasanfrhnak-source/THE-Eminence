# ui/components/data_table.py
"""Dark-styled ttk Treeview table."""

import tkinter as tk
from tkinter import ttk

from config.theme import BG_CARD, BG_HOVER, TEXT_PRIMARY, TEXT_SECONDARY


class DataTable(tk.Frame):
    def __init__(
        self, master, columns: tuple[str, ...], headings: tuple[str, ...], font_family: str
    ):
        super().__init__(master, bg=BG_CARD)
        style = ttk.Style(self)
        style.configure(
            "Eminence.Treeview",
            background=BG_CARD,
            fieldbackground=BG_CARD,
            foreground=TEXT_PRIMARY,
            rowheight=34,
            borderwidth=0,
            font=(font_family, 9),
        )
        style.configure(
            "Eminence.Treeview.Heading",
            background=BG_HOVER,
            foreground=TEXT_SECONDARY,
            relief="flat",
            font=(font_family, 9, "bold"),
        )
        style.map("Eminence.Treeview", background=[("selected", "#28364a")])
        self.tree = ttk.Treeview(self, columns=columns, show="headings", style="Eminence.Treeview")
        vertical_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        horizontal_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )
        for column, heading in zip(columns, headings):
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=140, anchor="w", stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def set_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            values = tuple(row)
            self.tree.insert("", "end", iid=str(values[0]), values=values)

    def selected_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None
