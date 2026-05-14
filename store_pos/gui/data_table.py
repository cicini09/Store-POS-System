"""Reusable enterprise-style table component for Tkinter views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from typing import Callable


@dataclass(slots=True)
class TableColumn:
    """Configuration for a table column."""

    key: str
    label: str
    width: int
    minwidth: int | None = None
    anchor: str = "w"
    frozen: bool = False
    hidden: bool = False
    can_hide: bool = True
    sort_type: str = "auto"
    formatter: Callable[[object], str] | None = None


class ModernDataTable(ttk.Frame):
    """Split-table layout with frozen columns and smoother scanning UX."""

    def __init__(
        self,
        master: tk.Misc,
        columns: list[TableColumn],
        *,
        height: int = 16,
        empty_message: str = "No records to display.",
        selectmode: str = "extended",
    ) -> None:
        super().__init__(master, style="App.TFrame")
        self.columns = columns
        self.height = height
        self.empty_message = empty_message
        self.selectmode = selectmode

        self._default_visibility = {column.key: not column.hidden for column in columns}
        self._visibility = dict(self._default_visibility)
        self._rows: list[dict] = []
        self._rows_by_iid: dict[str, dict] = {}
        self._row_order: list[str] = []
        self._row_index: dict[str, int] = {}
        self._hover_iid: str | None = None
        self._selection_sync_active = False
        self._last_selection: tuple[str, ...] = ()
        self._y_sync_active = False
        self._sort_column: str | None = None
        self._sort_descending = False
        self._selection_callbacks: list[Callable[[], None]] = []
        self._column_menu_vars: dict[str, tk.BooleanVar] = {}

        self._build_shell()
        self._rebuild_columns()

    def set_rows(self, rows: list[dict]) -> None:
        """Replace the rendered rows."""
        self._rows = list(rows)
        self._render_rows()

    def get_selected_rows(self) -> list[dict]:
        """Return the currently selected raw rows."""
        selection = self.scroll_tree.selection() or self.frozen_tree.selection()
        return [self._rows_by_iid[iid] for iid in selection if iid in self._rows_by_iid]

    def get_selected_row(self) -> dict | None:
        """Return the first selected row when available."""
        selected_rows = self.get_selected_rows()
        return selected_rows[0] if selected_rows else None

    def clear_selection(self) -> None:
        """Remove any active row selection."""
        self._apply_selection(())

    def select_first(self) -> None:
        """Select the first row when the table has content."""
        if not self._row_order:
            return
        first_iid = self._row_order[0]
        self._apply_selection((first_iid,))

    def bind_selection_change(self, callback: Callable[[], None]) -> None:
        """Register a callback for selection changes."""
        self._selection_callbacks.append(callback)

    def create_columns_button(self, parent: tk.Misc, text: str = "Columns") -> ttk.Menubutton:
        """Create a reusable column-visibility menu button."""
        button = ttk.Menubutton(parent, text=text, style="Ghost.TMenubutton", takefocus=False)
        menu = tk.Menu(button, tearoff=False)
        button["menu"] = menu
        self._column_menu_vars = {}

        for column in self.columns:
            if not column.can_hide:
                continue
            variable = tk.BooleanVar(value=self._visibility[column.key])
            self._column_menu_vars[column.key] = variable
            menu.add_checkbutton(
                label=column.label,
                variable=variable,
                command=lambda key=column.key: self._toggle_column_visibility(key),
            )

        if self._column_menu_vars:
            menu.add_separator()
        menu.add_command(label="Reset Columns", command=self.reset_columns)
        return button

    def reset_columns(self) -> None:
        """Restore the default visible column set."""
        self._visibility = dict(self._default_visibility)
        for key, variable in self._column_menu_vars.items():
            variable.set(self._visibility[key])
        self._rebuild_columns()
        self._render_rows()

    def _build_shell(self) -> None:
        outer = tk.Frame(self, bg="#D7E0EA", highlightthickness=0)
        outer.pack(fill="both", expand=True)

        shell = tk.Frame(outer, bg="#FFFFFF", highlightthickness=0)
        shell.pack(fill="both", expand=True, padx=1, pady=1)

        self.table_area = tk.Frame(shell, bg="#FFFFFF", highlightthickness=0)
        self.table_area.pack(fill="both", expand=True)

        self.frozen_wrapper = tk.Frame(self.table_area, bg="#FFFFFF", highlightthickness=0)
        self.frozen_wrapper.pack(side="left", fill="y")

        self.divider = tk.Frame(self.table_area, width=1, bg="#D7E0EA", highlightthickness=0)
        self.divider.pack(side="left", fill="y")

        self.scroll_wrapper = tk.Frame(self.table_area, bg="#FFFFFF", highlightthickness=0)
        self.scroll_wrapper.pack(side="left", fill="both", expand=True)

        self.frozen_tree = ttk.Treeview(
            self.frozen_wrapper,
            show="headings",
            height=self.height,
            selectmode=self.selectmode,
            style="DataTable.Treeview",
        )
        self.scroll_tree = ttk.Treeview(
            self.scroll_wrapper,
            show="headings",
            height=self.height,
            selectmode=self.selectmode,
            style="DataTable.Treeview",
        )
        self.frozen_tree.pack(side="left", fill="y")
        self.scroll_tree.pack(side="top", fill="both", expand=True)

        self.v_scrollbar = ttk.Scrollbar(self.table_area, orient="vertical", command=self._on_vertical_scroll)
        self.h_scrollbar = ttk.Scrollbar(self.scroll_wrapper, orient="horizontal", command=self.scroll_tree.xview)
        self.h_scrollbar.pack(side="bottom", fill="x")

        self.frozen_tree.configure(
            yscrollcommand=lambda first, last: self._on_tree_yview(self.frozen_tree, first, last)
        )
        self.scroll_tree.configure(
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=lambda first, last: self._on_tree_yview(self.scroll_tree, first, last),
        )

        self.empty_state_label = ttk.Label(
            shell,
            text=self.empty_message,
            style="Table.Empty.TLabel",
            justify="center",
            anchor="center",
        )

        for tree in (self.frozen_tree, self.scroll_tree):
            tree.tag_configure("row_even", background="#FFFFFF")
            tree.tag_configure("row_odd", background="#F8FAFC")
            tree.tag_configure("row_hover", background="#EFF6FF")
            tree.bind("<<TreeviewSelect>>", self._on_tree_select, add="+")
            tree.bind("<Motion>", self._on_tree_hover, add="+")
            tree.bind("<Leave>", self._clear_hover, add="+")
            tree.bind("<MouseWheel>", self._on_mousewheel, add="+")
            tree.bind("<Shift-MouseWheel>", self._on_shift_mousewheel, add="+")

    def _rebuild_columns(self) -> None:
        visible_columns = [column for column in self.columns if self._visibility[column.key]]
        frozen_columns = [column for column in visible_columns if column.frozen]
        scrollable_columns = [column for column in visible_columns if not column.frozen]

        self._frozen_columns = frozen_columns
        self._scrollable_columns = scrollable_columns

        self.frozen_tree.configure(columns=[column.key for column in frozen_columns])
        self.scroll_tree.configure(columns=[column.key for column in scrollable_columns])

        for tree, tree_columns in (
            (self.frozen_tree, frozen_columns),
            (self.scroll_tree, scrollable_columns),
        ):
            for column in tree_columns:
                label = self._heading_label(column)
                tree.heading(column.key, text=label, command=lambda key=column.key: self._sort_by(key))
                tree.column(
                    column.key,
                    width=column.width,
                    minwidth=column.minwidth or column.width,
                    anchor=column.anchor,
                    stretch=False,
                )

        has_frozen_columns = bool(frozen_columns)
        self.frozen_wrapper.pack_forget()
        self.divider.pack_forget()
        if has_frozen_columns:
            self.frozen_wrapper.pack(side="left", fill="y", before=self.scroll_wrapper)
            self.divider.pack(side="left", fill="y", before=self.scroll_wrapper)

    def _render_rows(self) -> None:
        self._clear_trees()
        rows = self._sorted_rows(self._rows)
        self._rows_by_iid.clear()
        self._row_order.clear()
        self._row_index.clear()

        for index, row in enumerate(rows):
            iid = f"row-{index}"
            tag = "row_even" if index % 2 == 0 else "row_odd"
            frozen_values = [self._format_value(column, row.get(column.key)) for column in self._frozen_columns]
            scroll_values = [self._format_value(column, row.get(column.key)) for column in self._scrollable_columns]

            self.frozen_tree.insert("", "end", iid=iid, values=frozen_values, tags=(tag,))
            self.scroll_tree.insert("", "end", iid=iid, values=scroll_values, tags=(tag,))
            self._rows_by_iid[iid] = row
            self._row_order.append(iid)
            self._row_index[iid] = index

        self._hover_iid = None
        self._update_empty_state()

    def _clear_trees(self) -> None:
        for tree in (self.frozen_tree, self.scroll_tree):
            for item in tree.get_children():
                tree.delete(item)

    def _sorted_rows(self, rows: list[dict]) -> list[dict]:
        if not self._sort_column:
            return list(rows)

        column = next((item for item in self.columns if item.key == self._sort_column), None)
        if column is None:
            return list(rows)

        return sorted(
            rows,
            key=lambda row: _coerce_sort_value(row.get(column.key), column.sort_type),
            reverse=self._sort_descending,
        )

    def _sort_by(self, key: str) -> None:
        if self._sort_column == key:
            self._sort_descending = not self._sort_descending
        else:
            self._sort_column = key
            self._sort_descending = False
        self._rebuild_columns()
        self._render_rows()

    def _heading_label(self, column: TableColumn) -> str:
        if self._sort_column != column.key:
            return column.label
        indicator = " v" if self._sort_descending else " ^"
        return f"{column.label}{indicator}"

    def _format_value(self, column: TableColumn, value: object) -> str:
        if column.formatter is not None:
            return column.formatter(value)
        return "" if value is None else str(value)

    def _toggle_column_visibility(self, key: str) -> None:
        visible_keys = [column.key for column in self.columns if self._visibility[column.key]]
        if self._visibility[key] and len(visible_keys) == 1:
            if key in self._column_menu_vars:
                self._column_menu_vars[key].set(True)
            return

        self._visibility[key] = not self._visibility[key]
        if key in self._column_menu_vars:
            self._column_menu_vars[key].set(self._visibility[key])
        self._rebuild_columns()
        self._render_rows()

    def _on_vertical_scroll(self, *args) -> None:
        self.frozen_tree.yview(*args)
        self.scroll_tree.yview(*args)

    def _on_tree_yview(self, source: ttk.Treeview, first: str, last: str) -> None:
        self.v_scrollbar.set(first, last)
        if self._y_sync_active:
            return

        other = self.scroll_tree if source is self.frozen_tree else self.frozen_tree
        self._y_sync_active = True
        try:
            other.yview_moveto(first)
        finally:
            self._y_sync_active = False

    def _on_tree_select(self, event) -> None:
        if self._selection_sync_active:
            return
        self._apply_selection(event.widget.selection())

    def _apply_selection(self, selection: tuple[str, ...] | list[str]) -> None:
        normalized_selection = tuple(selection)
        frozen_selection = tuple(self.frozen_tree.selection())
        scroll_selection = tuple(self.scroll_tree.selection())

        if (
            normalized_selection == self._last_selection
            and frozen_selection == normalized_selection
            and scroll_selection == normalized_selection
        ):
            return

        self._selection_sync_active = True
        try:
            for tree in (self.frozen_tree, self.scroll_tree):
                current_selection = tuple(tree.selection())
                if current_selection != normalized_selection:
                    if normalized_selection:
                        tree.selection_set(normalized_selection)
                    else:
                        tree.selection_remove(current_selection)
                if normalized_selection:
                    tree.focus(normalized_selection[0])
        finally:
            self._selection_sync_active = False

        if normalized_selection != self._last_selection:
            self._last_selection = normalized_selection
            self._notify_selection_callbacks()

    def _notify_selection_callbacks(self) -> None:
        for callback in self._selection_callbacks:
            callback()

    def _on_mousewheel(self, event) -> str:
        step = -1 * int(event.delta / 120)
        self.frozen_tree.yview_scroll(step, "units")
        self.scroll_tree.yview_scroll(step, "units")
        return "break"

    def _on_shift_mousewheel(self, event) -> str:
        step = -1 * int(event.delta / 120)
        self.scroll_tree.xview_scroll(step, "units")
        return "break"

    def _on_tree_hover(self, event) -> None:
        iid = event.widget.identify_row(event.y) or None
        if iid == self._hover_iid:
            return

        previous_hover = self._hover_iid
        self._hover_iid = iid
        if previous_hover:
            self._apply_row_tag(previous_hover)
        if iid:
            self._apply_row_tag(iid, hover=True)

    def _clear_hover(self, _event=None) -> None:
        if not self._hover_iid:
            return
        previous_hover = self._hover_iid
        self._hover_iid = None
        self._apply_row_tag(previous_hover)

    def _apply_row_tag(self, iid: str, *, hover: bool = False) -> None:
        if iid not in self._row_index:
            return
        base_tag = "row_even" if self._row_index[iid] % 2 == 0 else "row_odd"
        active_tag = "row_hover" if hover else base_tag
        for tree in (self.frozen_tree, self.scroll_tree):
            if tree.exists(iid):
                tree.item(iid, tags=(active_tag,))

    def _update_empty_state(self) -> None:
        if self._row_order:
            self.empty_state_label.place_forget()
            return
        self.empty_state_label.place(relx=0.5, rely=0.5, anchor="center")


def currency_text(value: object) -> str:
    """Format a numeric value as peso currency text."""
    try:
        numeric = float(value or 0)
    except (TypeError, ValueError):
        return "PHP 0.00"
    return f"PHP {numeric:,.2f}"


def truncate_text(value: object, limit: int = 48) -> str:
    """Trim long strings for cleaner table scans."""
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def _coerce_sort_value(value: object, sort_type: str):
    if value is None:
        return ""
    if sort_type == "int":
        return int(value)
    if sort_type == "float":
        return float(value)
    if sort_type == "date":
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return str(value).lower()
    if sort_type == "bool_text":
        return 1 if str(value).strip().lower() in {"yes", "true", "sent"} else 0
    try:
        if isinstance(value, str) and "." in value:
            return float(value)
        return int(value)
    except (TypeError, ValueError):
        return str(value).lower()
