# tests/test_database.py
"""Database schema, seeding, and persistence tests."""

import bcrypt


def test_schema_and_admin_seed(database):
    tables = {
        row["name"]
        for row in database.fetch_all("SELECT name FROM sqlite_master WHERE type = ?", ("table",))
    }
    assert {
        "users",
        "permissions",
        "customers",
        "projects",
        "transactions",
        "activity_log",
        "notifications",
    } <= tables
    admin = database.fetch_one("SELECT * FROM users WHERE username = ?", ("admin",))
    assert admin is not None
    assert bcrypt.checkpw(b"admin123", admin["password_hash"].encode("utf-8"))
    assert admin["password_hash"] != "admin123"


def test_foreign_key_is_enforced(database):
    try:
        with database.transaction() as connection:
            connection.execute(
                "INSERT INTO projects (customer_id, title) VALUES (?, ?)",
                (123456, "Invalid relation"),
            )
    except Exception as exc:
        assert "FOREIGN KEY" in str(exc)
    else:
        raise AssertionError("Expected foreign key constraint to reject unknown customer")


def test_repository_crud_and_audit(database):
    from core.repository import Repository

    repository = Repository(database)
    record_id = repository.create_record("customers", {"name": "Northwind"}, 1)
    assert repository.list_records("customers")[0]["name"] == "Northwind"
    repository.update_record("customers", record_id, {"name": "Northwind Electric"}, 1)
    assert repository.list_records("customers")[0]["name"] == "Northwind Electric"
    repository.delete_record("customers", record_id, 1)
    log = database.fetch_all("SELECT action FROM activity_log ORDER BY id")
    assert [row["action"] for row in log] == [
        "create_customer",
        "update_customer",
        "delete_customer",
    ]


def test_transaction_create_delete_and_audit(database):
    from core.services.report_service import ReportService

    service = ReportService(database)
    record_id = service.create_transaction(
        {"amount": 1250, "type": "income", "category": "installation"}, user_id=1
    )
    assert service.list_transactions()[0]["id"] == record_id
    service.delete_transaction(record_id, user_id=1)
    actions = [
        row["action"] for row in database.fetch_all("SELECT action FROM activity_log ORDER BY id")
    ]
    assert actions == ["create_transaction", "delete_transaction"]
