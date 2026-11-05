# core/services/project_service.py
"""Project business operations."""

from core.repository import Repository
from utils.validators import validate_project


class ProjectService:
    def __init__(self, repository: Repository | None = None):
        self.repository = repository or Repository()

    def list(self) -> list[dict]:
        return self.repository.list_records("projects")

    def create(self, values: dict, user_id: int | None = None) -> int:
        return self.repository.create_record("projects", validate_project(values), user_id)

    def update(self, record_id: int, values: dict, user_id: int | None = None) -> None:
        self.repository.update_record("projects", record_id, validate_project(values), user_id)

    def delete(self, record_id: int, user_id: int | None = None) -> None:
        self.repository.delete_record("projects", record_id, user_id)
