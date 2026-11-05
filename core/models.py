# core/models.py
"""Typed application entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    username: str
    full_name: str
    role: str
    email: str | None = None
    phone: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class Customer:
    id: int
    name: str
    type: str | None
    phone: str | None
    email: str | None
    address: str | None
    national_id: str | None
    notes: str | None
    created_at: str


@dataclass(frozen=True)
class Project:
    id: int
    customer_id: int | None
    title: str
    description: str | None
    status: str
    budget: float
    start_date: str | None
    end_date: str | None
    created_at: str
