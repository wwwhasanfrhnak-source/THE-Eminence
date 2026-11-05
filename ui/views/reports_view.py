# ui/views/reports_view.py
"""Business reporting and customer export page."""

import tkinter as tk
from tkinter import filedialog, messagebox

from config.theme import BG_CARD, BG_MAIN, PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY
from core.services.report_service import ReportService
from ui.components.data_table import DataTable
from ui.components.modern_card import ModernCard


class ReportsView(tk.Frame):
    def __init__(self, master, font_family, user):
        super().__init__(master, bg=BG_MAIN)
        self.font_family = font_family
        self.user = user
        self.service = ReportService()
        tk.Label(
            self,
            text="Reports & exports",
            bg=BG_MAIN,
            fg=TEXT_PRIMARY,
            font=(font_family, 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            self,
            text="Review activity and export customer data",
            bg=BG_MAIN,
            fg=TEXT_SECONDARY,
            font=(font_family, 9),
        ).pack(anchor="w", pady=(4, 18))
        card = ModernCard(self, width=1040, height=230)
        card.pack(fill="x", pady=(0, 14))
        self.summary_label = tk.Label(
            card.body,
            text="",
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            justify="left",
            anchor="nw",
            font=(font_family, 10),
        )
        self.summary_label.pack(fill="x", pady=(8, 12))
        self.refresh()
        buttons = tk.Frame(card.body, bg=BG_CARD)
        buttons.pack(anchor="w")
        for title, command, color in (
            ("+ Add transaction", self.add_transaction, PRIMARY),
            ("Delete selected", self.delete_transaction, BG_CARD),
            ("Export Excel", lambda: self.export("excel"), BG_CARD),
            ("Export PDF", lambda: self.export("pdf"), BG_CARD),
        ):
            tk.Button(
                buttons,
                text=title,
                command=command,
                bg=color,
                fg=TEXT_PRIMARY,
                relief="flat",
                padx=14,
                pady=9,
                font=(font_family, 9, "bold"),
            ).pack(side="left", padx=(0, 8))
        transaction_card = ModernCard(self, width=1040, height=375)
        transaction_card.pack(fill="both", expand=True)
        self.transactions = DataTable(
            transaction_card.body,
            ("id", "project_id", "amount", "type", "category", "description", "tx_date"),
            ("ID", "Project ID", "Amount", "Type", "Category", "Description", "Date"),
            font_family,
        )
        self.transactions.pack(fill="both", expand=True)
        self.refresh_transactions()

    def refresh(self):
        data = self.service.summary()
        projects = (
            ", ".join(f"{row['status']}: {row['total']}" for row in data["projects"]) or "None"
        )
        money = (
            ", ".join(f"{row['type']}: {row['total']:,.2f}" for row in data["transactions"])
            or "None"
        )
        self.summary_label.configure(
            text=f"Customer records: {data['customers']}\n\nProjects by status: {projects}"
            f"\n\nTransaction totals: {money}\n\nRecent activity entries: {len(data['recent_activity'])}"
        )

    def refresh_transactions(self):
        rows = self.service.list_transactions()
        columns = ("id", "project_id", "amount", "type", "category", "description", "tx_date")
        self.transactions.set_rows(
            [tuple(row.get(column) or "" for column in columns) for row in rows]
        )

    def add_transaction(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add transaction")
        dialog.configure(bg=BG_CARD)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        labels = (
            "Project ID (optional)",
            "Amount",
            "Type (income/expense)",
            "Category",
            "Description",
            "Date (YYYY-MM-DD)",
        )
        entries = {}
        for row, label in enumerate(labels):
            tk.Label(
                dialog, text=label, bg=BG_CARD, fg=TEXT_SECONDARY, font=(self.font_family, 9)
            ).grid(row=row, column=0, padx=12, pady=7, sticky="w")
            entry = tk.Entry(
                dialog,
                bg="#0b0f19",
                fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY,
                relief="flat",
                width=34,
                font=(self.font_family, 9),
            )
            entry.grid(row=row, column=1, padx=12, pady=7, ipady=5)
            entries[label] = entry
        entries["Type (income/expense)"].insert(0, "income")
        result = {}

        def save():
            project_id = entries[labels[0]].get().strip()
            amount = entries[labels[1]].get().strip()
            try:
                result["id"] = self.service.create_transaction(
                    {
                        "project_id": int(project_id) if project_id else None,
                        "amount": amount,
                        "type": entries[labels[2]].get().strip().lower(),
                        "category": entries[labels[3]].get().strip() or None,
                        "description": entries[labels[4]].get().strip() or None,
                        "tx_date": entries[labels[5]].get().strip() or None,
                    },
                    self.user.id,
                )
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror("Unable to add transaction", str(exc), parent=dialog)

        tk.Button(
            dialog,
            text="Save transaction",
            command=save,
            bg=PRIMARY,
            fg=TEXT_PRIMARY,
            relief="flat",
            font=(self.font_family, 9, "bold"),
        ).grid(row=len(labels), column=0, columnspan=2, padx=12, pady=14, sticky="ew")
        self.wait_window(dialog)
        if result:
            self.refresh()
            self.refresh_transactions()

    def delete_transaction(self):
        record_id = self.transactions.selected_id()
        if record_id is None:
            messagebox.showinfo(
                "Select transaction", "Choose a transaction row first.", parent=self
            )
            return
        if messagebox.askyesno(
            "Delete transaction", "Delete the selected transaction?", parent=self
        ):
            try:
                self.service.delete_transaction(record_id, self.user.id)
                self.refresh()
                self.refresh_transactions()
            except Exception as exc:
                messagebox.showerror("Unable to delete transaction", str(exc), parent=self)

    def export(self, kind):
        extension = ".xlsx" if kind == "excel" else ".pdf"
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=extension,
            filetypes=[("Excel workbook", "*.xlsx")] if kind == "excel" else [("PDF", "*.pdf")],
        )
        if path:
            try:
                self.service.export_customers(path, kind)
                messagebox.showinfo("Export complete", f"Report saved to:\n{path}", parent=self)
            except Exception as exc:
                messagebox.showerror("Export failed", str(exc), parent=self)
