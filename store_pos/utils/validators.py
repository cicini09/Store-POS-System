"""Validation helpers for forms and user input."""

from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_PATTERN = re.compile(r"^(09\d{9}|\+639\d{9})$")
PRODUCT_NAME_MIN = 2
PRODUCT_NAME_MAX = 100
CATEGORY_MAX = 50
PRICE_MAX = 999_999.99


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


def is_valid_phone(phone: str) -> bool:
    """Return True when the phone matches Philippine mobile format (09XXXXXXXXX or +639XXXXXXXXX)."""
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if not cleaned:
        return True  # phone is optional, empty is valid
    return bool(PHONE_PATTERN.match(cleaned))


def validate_phone(phone: str) -> str | None:
    """Return an error message if phone is invalid, or None if valid."""
    if not phone.strip():
        return None  # optional field
    if not is_valid_phone(phone):
        return "Phone must be a valid PH mobile number (e.g. 09171234567 or +639171234567)."
    return None


def validate_product_name(name: str) -> str | None:
    """Return an error message if product name is invalid, or None if valid."""
    stripped = name.strip()
    if len(stripped) < PRODUCT_NAME_MIN:
        return f"Product name must be at least {PRODUCT_NAME_MIN} characters."
    if len(stripped) > PRODUCT_NAME_MAX:
        return f"Product name cannot exceed {PRODUCT_NAME_MAX} characters."
    return None


def validate_category(category: str) -> str | None:
    """Return an error message if category is invalid, or None if valid."""
    stripped = category.strip()
    if not stripped:
        return "Category is required."
    if len(stripped) > CATEGORY_MAX:
        return f"Category cannot exceed {CATEGORY_MAX} characters."
    if not re.match(r"^[A-Za-z0-9 &/\-]+$", stripped):
        return "Category can only contain letters, numbers, spaces, &, /, and hyphens."
    return None


def validate_customer_name(name: str) -> str | None:
    """Return an error message if customer name is invalid, or None if valid."""
    stripped = name.strip()
    if not stripped:
        return "Customer name is required."
    if len(stripped) < 2:
        return "Customer name must be at least 2 characters."
    if len(stripped) > 100:
        return "Customer name cannot exceed 100 characters."
    if not re.match(r"^[A-Za-z\s.\-]+$", stripped):
        return "Customer name can only contain letters, spaces, dots, and hyphens."
    return None


def parse_price(value: str) -> float:
    """Parse a non-negative price value within business limits."""
    try:
        price = float(value)
    except ValueError as exc:
        raise ValueError("Price must be a number.") from exc
    if price < 0:
        raise ValueError("Price cannot be negative.")
    if price > PRICE_MAX:
        raise ValueError(f"Price cannot exceed PHP {PRICE_MAX:,.2f}.")
    if price == 0:
        raise ValueError("Price must be greater than zero.")
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
