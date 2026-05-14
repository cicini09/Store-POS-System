"""Validation helpers for forms and user input."""

from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_required_fields(fields: dict[str, str]) -> list[str]:
    """Return a list of errors for blank required fields."""
    errors = []
    for label, value in fields.items():
        if not str(value).strip():
            errors.append(f"{label} is required.")
    return errors


def is_valid_email(email: str) -> bool:
    """Return True when the email matches a basic valid format."""
    return bool(EMAIL_PATTERN.match(email.strip()))


def parse_price(value: str) -> float:
    """Parse a non-negative price value."""
    try:
        price = float(value)
    except ValueError as exc:
        raise ValueError("Price must be a number.") from exc
    if price < 0:
        raise ValueError("Price cannot be negative.")
    return round(price, 2)


def parse_non_negative_int(value: str, label: str) -> int:
    """Parse a non-negative integer."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a whole number.") from exc
    if parsed < 0:
        raise ValueError(f"{label} cannot be negative.")
    return parsed


def parse_positive_int(value: str, label: str) -> int:
    """Parse a positive integer."""
    parsed = parse_non_negative_int(value, label)
    if parsed <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return parsed
