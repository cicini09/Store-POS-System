"""Reusable Treeview sorting helpers."""

from __future__ import annotations

from datetime import datetime
from tkinter import ttk


def attach_sorting(tree: ttk.Treeview, value_types: dict[str, str] | None = None) -> None:
    """Attach click-to-sort behavior to every Treeview heading."""
    value_types = value_types or {}
    base_labels = {column: tree.heading(column, "text") for column in tree["columns"]}
    tree._sort_state = {"column": None, "descending": False, "labels": base_labels, "types": value_types}

    for column in tree["columns"]:
        tree.heading(column, command=lambda col=column: _sort_tree(tree, col))


def _sort_tree(tree: ttk.Treeview, column: str) -> None:
    state = tree._sort_state
    descending = state["column"] == column and not state["descending"]

    rows = [(tree.set(item_id, column), item_id) for item_id in tree.get_children("")]
    rows.sort(key=lambda pair: _coerce_value(pair[0], state["types"].get(column, "auto")), reverse=descending)

    for index, (_, item_id) in enumerate(rows):
        tree.move(item_id, "", index)

    state["column"] = column
    state["descending"] = descending
    _refresh_headings(tree)


def _refresh_headings(tree: ttk.Treeview) -> None:
    state = tree._sort_state
    for column, label in state["labels"].items():
        suffix = ""
        if state["column"] == column:
            suffix = " ▼" if state["descending"] else " ▲"
        tree.heading(column, text=f"{label}{suffix}", command=lambda col=column: _sort_tree(tree, col))


def _coerce_value(value: str, value_type: str):
    cleaned = value.replace("PHP ", "").replace(",", "").strip()
    if value_type == "int":
        return int(cleaned or 0)
    if value_type == "float":
        return float(cleaned or 0)
    if value_type == "date":
        try:
            return datetime.fromisoformat(cleaned)
        except ValueError:
            return cleaned.lower()
    if value_type == "bool_text":
        return 1 if cleaned.lower() in {"yes", "true", "sent"} else 0

    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return cleaned.lower()
