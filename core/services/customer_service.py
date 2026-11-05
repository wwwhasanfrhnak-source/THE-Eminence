# core/services/customer_service.py
"""Customer business operations."""

from core.repository import Repository
from utils.validators import validate_customer


class CustomerService:
    def __init__(self, repository: Repository | None = None):
        self.repository = repository or Repository()

    def list(self) -> list[dict]:
        return self.repository.list_records("customers")

    def create(self, values: dict, user_id: int | None = None) -> int:
        return self.repository.create_record("customers", validate_customer(values), user_id)

    def update(self, record_id: int, values: dict, user_id: int | None = None) -> None:
        self.repository.update_record("customers", record_id, validate_customer(values), user_id)

    def delete(self, record_id: int, user_id: int | None = None) -> None:
        self.repository.delete_record("customers", record_id, user_id)
