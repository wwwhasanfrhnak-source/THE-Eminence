# tests/conftest.py
"""Shared temporary SQLite fixtures."""

import pytest

from core.database import Database


@pytest.fixture
def database(tmp_path):
    Database.reset_for_tests()
    db = Database(tmp_path / "test.sqlite")
    yield db
    Database.reset_for_tests()
