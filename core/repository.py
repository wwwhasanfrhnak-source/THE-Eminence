# core/repository.py
"""Parameterized persistence operations and audit logging."""

from typing import Any

from core.database import Database


TABLE_FIELDS = {
    "customers": ("name", "type", "phone", "email", "address", "national_id", "notes"),
    "projects": (
        "customer_id",
        "title",
        "description",
        "status",
        "budget",
        "start_date",
        "end_date",
    ),
}
LIST_QUERIES = {
    "customers": "SELECT * FROM customers ORDER BY id DESC",
    "projects": "SELECT * FROM projects ORDER BY id DESC",
}
CREATE_QUERIES = {
    "customers": (
        "INSERT INTO customers (name, type, phone, email, address, national_id, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    ),
    "projects": (
        "INSERT INTO projects (customer_id, title, description, status, budget, start_date, end_date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    ),
}
UPDATE_QUERIES = {
    "customers": (
        "UPDATE customers SET name = ?, type = ?, phone = ?, email = ?, address = ?, "
        "national_id = ?, notes = ? WHERE id = ?"
    ),
    "projects": (
        "UPDATE projects SET customer_id = ?, title = ?, description = ?, status = ?, "
        "budget = ?, start_date = ?, end_date = ? WHERE id = ?"
    ),
}
DELETE_QUERIES = {
    "customers": "DELETE FROM customers WHERE id = ?",
    "projects": "DELETE FROM projects WHERE id = ?",
}


class Repository:
    def __init__(self, database: Database | None = None):
        self.db = database or Database()

    def log_activity(self, action: str, details: str = "", user_id: int | None = None) -> None:
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, action, details),
            )

    def list_records(self, table: str) -> list[dict[str, Any]]:
        query = LIST_QUERIES.get(table)
        if query is None:
            raise ValueError(f"Unsupported record type: {table}")
        return [dict(row) for row in self.db.fetch_all(query)]

    def create_record(self, table: str, values: dict[str, Any], user_id: int | None = None) -> int:
        fields = TABLE_FIELDS.get(table)
        if fields is None:
            raise ValueError(f"Unsupported record type: {table}")
        params = tuple(values.get(field) for field in fields)
        with self.db.transaction() as connection:
            cursor = connection.execute(CREATE_QUERIES[table], params)
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, f"create_{table[:-1]}", f"id={cursor.lastrowid}"),
            )
            return int(cursor.lastrowid)

    def update_record(
        self, table: str, record_id: int, values: dict[str, Any], user_id: int | None = None
    ) -> None:
        fields = TABLE_FIELDS.get(table)
        if fields is None:
            raise ValueError(f"Unsupported record type: {table}")
        params = tuple(values.get(field) for field in fields) + (record_id,)
        with self.db.transaction() as connection:
            cursor = connection.execute(UPDATE_QUERIES[table], params)
            if cursor.rowcount == 0:
                raise LookupError(f"Record {record_id} does not exist")
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, f"update_{table[:-1]}", f"id={record_id}"),
            )

    def delete_record(self, table: str, record_id: int, user_id: int | None = None) -> None:
        query = DELETE_QUERIES.get(table)
        if query is None:
            raise ValueError(f"Unsupported record type: {table}")
        with self.db.transaction() as connection:
            cursor = connection.execute(query, (record_id,))
            if cursor.rowcount == 0:
                raise LookupError(f"Record {record_id} does not exist")
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, f"delete_{table[:-1]}", f"id={record_id}"),
            )

    def dashboard_stats(self) -> dict[str, int | float]:
        return {
            "customers": int(self.db.fetch_one("SELECT COUNT(*) AS n FROM customers")["n"]),
            "projects": int(self.db.fetch_one("SELECT COUNT(*) AS n FROM projects")["n"]),
            "revenue": float(
                self.db.fetch_one(
                    "SELECT COALESCE(SUM(amount), 0) AS n FROM transactions WHERE type = ?",
                    ("income",),
                )["n"]
            ),
            "users": int(self.db.fetch_one("SELECT COUNT(*) AS n FROM users")["n"]),
        }

    def list_users(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.fetch_all(
                "SELECT id, username, full_name, role, email, phone, is_active, created_at, last_login "
                "FROM users ORDER BY id"
            )
        ]
