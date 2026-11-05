# core/services/report_service.py
"""Report data queries and exports."""

from datetime import date
import math

from core.database import Database
from core.exceptions import ValidationError
from utils.excel_export import export_rows_to_excel
from utils.pdf_export import export_rows_to_pdf
from utils.date_helper import today_iso


class ReportService:
    def __init__(self, database: Database | None = None):
        self.db = database or Database()

    def summary(self) -> dict:
        return {
            "customers": self.db.fetch_all("SELECT COUNT(*) AS total FROM customers")[0]["total"],
            "projects": self.db.fetch_all(
                "SELECT status, COUNT(*) AS total FROM projects GROUP BY status"
            ),
            "transactions": self.db.fetch_all(
                "SELECT type, COALESCE(SUM(amount), 0) AS total FROM transactions GROUP BY type"
            ),
            "recent_activity": self.db.fetch_all(
                "SELECT action, details, created_at FROM activity_log ORDER BY id DESC LIMIT 20"
            ),
        }

    def export_customers(self, path: str, kind: str) -> None:
        rows = [
            dict(row)
            for row in self.db.fetch_all(
                "SELECT id, name, type, phone, email, address, created_at FROM customers ORDER BY name"
            )
        ]
        if kind == "excel":
            export_rows_to_excel(rows, path, "Customers")
        elif kind == "pdf":
            export_rows_to_pdf(rows, path, "Customer report")
        else:
            raise ValueError("Export kind must be 'excel' or 'pdf'")

    def list_transactions(self) -> list[dict]:
        return [
            dict(row)
            for row in self.db.fetch_all(
                "SELECT id, project_id, amount, type, category, description, tx_date "
                "FROM transactions ORDER BY tx_date DESC, id DESC"
            )
        ]

    def create_transaction(self, values: dict, user_id: int | None = None) -> int:
        try:
            amount = float(values.get("amount", 0))
        except (TypeError, ValueError) as exc:
            raise ValidationError("Amount must be a number") from exc
        if not math.isfinite(amount) or amount < 0:
            raise ValidationError("Amount must be finite and non-negative")
        transaction_type = values.get("type")
        if transaction_type not in ("income", "expense"):
            raise ValidationError("Type must be income or expense")
        tx_date = values.get("tx_date") or today_iso()
        try:
            date.fromisoformat(tx_date)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Transaction date must be YYYY-MM-DD") from exc
        project_id = values.get("project_id") or None
        if project_id is not None:
            try:
                project_id = int(project_id)
            except (TypeError, ValueError) as exc:
                raise ValidationError("Project ID must be an integer") from exc
            if project_id < 1:
                raise ValidationError("Project ID must be a positive integer")
        with self.db.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO transactions "
                "(project_id, amount, type, category, description, tx_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    project_id,
                    amount,
                    transaction_type,
                    values.get("category"),
                    values.get("description"),
                    tx_date,
                ),
            )
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "create_transaction", f"id={cursor.lastrowid}; type={transaction_type}"),
            )
            return int(cursor.lastrowid)

    def delete_transaction(self, record_id: int, user_id: int | None = None) -> None:
        with self.db.transaction() as connection:
            cursor = connection.execute("DELETE FROM transactions WHERE id = ?", (record_id,))
            if cursor.rowcount == 0:
                raise LookupError(f"Transaction {record_id} does not exist")
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "delete_transaction", f"id={record_id}"),
            )
