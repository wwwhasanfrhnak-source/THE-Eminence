"""Project portfolio with search, pagination, and CRUD actions."""

import sqlite3
import tkinter as tk
from tkinter import messagebox

from config.theme import BG_CARD, BG_MAIN, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY
from core.exceptions import EminenceError
from core.services.project_service import ProjectService
from ui.components.data_table import DataTable
from ui.components.modern_card import ModernCard
from ui.components.toast import Toast
from ui.theme import BORDER


class ProjectsView(tk.Frame):
    FIELDS = ("customer_id", "title", "description", "status", "budget", "start_date", "end_date")
    COLUMNS = ("id",) + FIELDS + ("created_at",)
    HEADINGS = (
        "ID",
        "Customer ID",
        "Title",
        "Description",
        "Status",
        "Budget",
        "Start date",
        "End date",
        "Created",
    )
    PAGE_SIZE = 12

    def __init__(self, master, font_family, user):
        super().__init__(master, bg=BG_MAIN)
        self.font_family, self.user = font_family, user
        self.service = ProjectService()
        self._all_rows = []
        self._filtered_rows = []
        self._page = 0
        self._build()
        self.refresh()

    def _build(self):
        tk.Label(
            self, text="Projects", bg=BG_MAIN, fg=TEXT_PRIMARY, font=(self.font_family, 20, "bold")
        ).pack(anchor="w")
        tk.Label(
            self,
            text="Track budgets, delivery status, and project schedules",
            bg=BG_MAIN,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 9),
        ).pack(anchor="w", pady=(4, 18))

        actions = tk.Frame(self, bg=BG_MAIN)
        actions.pack(fill="x", pady=(0, 12))
        tk.Entry(
            actions,
            textvariable=self._search_var(),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PRIMARY,
            font=(self.font_family, 9),
            width=34,
        ).pack(side="right", ipady=8, padx=(0, 8))
        for label, command in (
            ("+ Add project", self.add),
            ("Edit selected", self.edit),
            ("Delete selected", self.delete),
        ):
            tk.Button(
                actions,
                text=label,
                command=command,
                bg=PRIMARY if label.startswith("+") else BG_CARD,
                fg=TEXT_PRIMARY,
                activebackground=PRIMARY,
                activeforeground=TEXT_PRIMARY,
                relief="flat",
                cursor="hand2",
                font=(self.font_family, 9, "bold"),
                padx=13,
                pady=8,
            ).pack(side="left", padx=(0, 8))

        card = ModernCard(self, width=1040, height=610, shadow=True)
        card.pack(fill="both", expand=True)
        self.table = DataTable(card.body, self.COLUMNS, self.HEADINGS, self.font_family)
        self.table.pack(fill="both", expand=True)
        footer = tk.Frame(self, bg=BG_MAIN)
        footer.pack(fill="x", pady=(8, 0))
        self._page_label = tk.Label(
            footer,
            text="",
            bg=BG_MAIN,
            fg=TEXT_SECONDARY,
            font=(self.font_family, 8),
        )
        self._page_label.pack(side="right", padx=8)
        self._previous_button = tk.Button(
            footer,
            text="Previous",
            command=lambda: self._change_page(-1),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 8),
            padx=10,
            pady=5,
        )
        self._previous_button.pack(side="right")
        self._next_button = tk.Button(
            footer,
            text="Next",
            command=lambda: self._change_page(1),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 8),
            padx=10,
            pady=5,
        )
        self._next_button.pack(side="right", padx=(0, 6))

    def _search_var(self):
        self.search = tk.StringVar(master=self)
        self.search.trace_add("write", self._filter_changed)
        return self.search

    def _filter_changed(self, *_args):
        self._page = 0
        self._render_page()

    def refresh(self):
        self._all_rows = self.service.list()
        self._page = 0
        self._render_page()

    def _render_page(self):
        query = self.search.get().strip().casefold()
        if query:
            self._filtered_rows = [
                row
                for row in self._all_rows
                if query in " ".join(str(value or "") for value in row.values()).casefold()
            ]
        else:
            self._filtered_rows = list(self._all_rows)

        page_count = max(1, (len(self._filtered_rows) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self._page = min(self._page, page_count - 1)
        start = self._page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, len(self._filtered_rows))
        self.table.set_rows(
            [
                tuple(row.get(col) if row.get(col) is not None else "" for col in self.COLUMNS)
                for row in self._filtered_rows[start:end]
            ]
        )
        self._page_label.configure(
            text=f"{start + 1 if end else 0}–{end} of {len(self._filtered_rows)}"
        )
        self._previous_button.configure(state="normal" if self._page > 0 else "disabled")
        self._next_button.configure(state="normal" if self._page + 1 < page_count else "disabled")

    def _change_page(self, offset):
        self._page += offset
        self._render_page()

    def _form(self, initial=None):
        dialog = tk.Toplevel(self)
        dialog.title("Project details")
        dialog.configure(bg=BG_CARD)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        fields = {}
        for row, field in enumerate(self.FIELDS):
            tk.Label(
                dialog,
                text=field.replace("_", " ").title(),
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=(self.font_family, 9),
            ).grid(row=row, column=0, padx=14, pady=6, sticky="w")
            entry = tk.Entry(
                dialog,
                bg="#0b0f19",
                fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY,
                relief="flat",
                width=38,
                font=(self.font_family, 9),
            )
            entry.grid(row=row, column=1, padx=14, pady=6, ipady=5)
            entry.insert(0, str((initial or {}).get(field) or ""))
            fields[field] = entry
        result = {}

        def save():
            result.update({key: entry.get().strip() or None for key, entry in fields.items()})
            for key in ("customer_id", "budget"):
                if result.get(key) is not None:
                    try:
                        result[key] = (
                            int(result[key]) if key == "customer_id" else float(result[key])
                        )
                    except ValueError:
                        messagebox.showerror(
                            "Invalid value",
                            f"{key.replace('_', ' ').title()} must be numeric.",
                            parent=dialog,
                        )
                        result.clear()
                        return
            dialog.destroy()

        tk.Button(
            dialog,
            text="Save project",
            command=save,
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 9, "bold"),
        ).grid(row=len(self.FIELDS), column=0, columnspan=2, padx=12, pady=14, sticky="ew")
        self.wait_window(dialog)
        return result or None

    def add(self):
        values = self._form()
        if values:
            try:
                self.service.create(values, self.user.id)
                self.refresh()
                Toast.show(self, "Project added", self.font_family, kind="success")
            except (EminenceError, LookupError, sqlite3.Error) as exc:
                messagebox.showerror("Unable to add project", str(exc), parent=self)

    def edit(self):
        record_id = self.table.selected_id()
        if record_id is None:
            messagebox.showinfo("Select project", "Choose a project row first.", parent=self)
            return
        current = next((row for row in self._all_rows if row["id"] == record_id), None)
        values = self._form(current)
        if values:
            try:
                self.service.update(record_id, values, self.user.id)
                self.refresh()
                Toast.show(self, "Project updated", self.font_family, kind="success")
            except (EminenceError, LookupError, sqlite3.Error) as exc:
                messagebox.showerror("Unable to update project", str(exc), parent=self)

    def delete(self):
        record_id = self.table.selected_id()
        if record_id is None:
            messagebox.showinfo("Select project", "Choose a project row first.", parent=self)
            return
        if messagebox.askyesno("Delete project", "Delete the selected project?", parent=self):
            try:
                self.service.delete(record_id, self.user.id)
                self.refresh()
                Toast.show(self, "Project deleted", self.font_family, kind="success")
            except (EminenceError, LookupError, sqlite3.Error) as exc:
                messagebox.showerror("Unable to delete project", str(exc), parent=self)
