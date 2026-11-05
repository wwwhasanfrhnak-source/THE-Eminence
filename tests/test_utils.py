# tests/test_utils.py
"""Utility validation, formatting, image, and export tests."""

from pathlib import Path

import pytest

from core.exceptions import ValidationError
from ui.components.pillow_utils import make_rounded_card
from utils.date_helper import format_date
from utils.excel_export import export_rows_to_excel
from utils.pdf_export import export_rows_to_pdf
from utils.security import hash_password, verify_password
from utils.validators import validate_email, validate_project, validate_username


def test_bcrypt_helpers_and_input_validation():
    encoded = hash_password("long-enough-password")
    assert encoded.startswith("$2")
    assert verify_password("long-enough-password", encoded)
    assert not verify_password("wrong", encoded)
    assert validate_username("electric.user") == "electric.user"
    assert validate_email("ops@example.com") == "ops@example.com"
    with pytest.raises(ValidationError):
        validate_username("bad username")


def test_project_validation_and_date_format():
    assert validate_project({"title": "Panel upgrade", "budget": "12.5"}) == {
        "title": "Panel upgrade",
        "budget": 12.5,
    }
    with pytest.raises(ValidationError):
        validate_project({"title": " ", "budget": -1})
    assert format_date("2024-01-02") == "2024-01-02"


def test_pillow_rounded_card_has_shadow_padding():
    image, pad = make_rounded_card(100, 60, 12, "#111827", "#1e2633", True)
    assert pad > 0
    assert image.size == (100 + 2 * pad, 60 + 2 * pad)


def test_excel_export(tmp_path: Path):
    path = tmp_path / "customers.xlsx"
    export_rows_to_excel([{"name": "Northwind", "type": "commercial"}], str(path), "Customers")
    assert path.is_file()
    assert path.stat().st_size > 0


def test_pdf_export(tmp_path: Path):
    path = tmp_path / "customers.pdf"
    export_rows_to_pdf([{"name": "Northwind"}], str(path), "Customer report")
    assert path.read_bytes().startswith(b"%PDF")
