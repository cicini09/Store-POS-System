"""Products management view."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .. import database
from ..utils import validators
from .data_table import ModernDataTable, TableColumn, currency_text, truncate_text


PRODUCT_DIALOG_BACKGROUND = "#F8FAFC"
PRODUCT_DIALOG_CARD = "#FFFFFF"
PRODUCT_DIALOG_TEXT = "#0F172A"
PRODUCT_DIALOG_MUTED = "#64748B"
PRODUCT_DIALOG_BORDER = "#CBD5E1"
PRODUCT_DIALOG_DANGER = "#B42318"
PRODUCT_DIALOG_DANGER_SOFT = "#FEF3F2"


class ProductDialog(tk.Toplevel):
    """Modal dialog used for adding or editing products."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        on_save: Callable[[str, str, float, int, str], None],
        product: dict | None = None,
    ) -> None:
        super().__init__(master)
        self.on_save = on_save
        self._editing_id = (product or {}).get("id", None)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=PRODUCT_DIALOG_BACKGROUND)
        self.transient(master)
        self.grab_set()

        self.name_var = tk.StringVar(value=(product or {}).get("name", ""))
        self.category_var = tk.StringVar(value=(product or {}).get("category", ""))
        self.price_var = tk.StringVar(value=str((product or {}).get("price", "")))
        self.stock_var = tk.StringVar(value=str((product or {}).get("stock_quantity", "")))
        self.description_var = tk.StringVar(value=(product or {}).get("description", ""))

        shell = tk.Frame(
            self,
            bg=PRODUCT_DIALOG_CARD,
            highlightthickness=1,
            highlightbackground=PRODUCT_DIALOG_BORDER,
            padx=22,
            pady=20,
        )
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        header = tk.Frame(shell, bg=PRODUCT_DIALOG_CARD)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        tk.Label(
            header,
            text=title,
            bg=PRODUCT_DIALOG_CARD,
            fg=PRODUCT_DIALOG_TEXT,
            font=("Segoe UI Semibold", 17),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Keep product details accurate so inventory and receipts stay reliable.",
            bg=PRODUCT_DIALOG_CARD,
            fg=PRODUCT_DIALOG_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        for row_index, (label_text, variable) in enumerate(
            [
                ("Product name", self.name_var),
                ("Category", self.category_var),
                ("Price", self.price_var),
                ("Stock quantity", self.stock_var),
                ("Description", self.description_var),
            ],
            start=1,
        ):
            self._build_field(shell, label_text, variable, row_index)

        action_bar = tk.Frame(shell, bg=PRODUCT_DIALOG_CARD)
        action_bar.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        ttk.Button(action_bar, text="Cancel", command=self._cancel, style="Ghost.TButton", takefocus=False).pack(
            side="right",
            padx=(8, 0),
        )
        ttk.Button(action_bar, text="Save Product", command=self._save, takefocus=False).pack(side="right")

        shell.columnconfigure(1, weight=1)
        self.bind("<Return>", lambda _event: self._save())
        self.bind("<Escape>", lambda _event: self._cancel())
        self.after_idle(self._center_over_parent)

    def _build_field(self, parent: tk.Misc, label_text: str, variable: tk.StringVar, row_index: int) -> None:
        tk.Label(
            parent,
            text=label_text,
            bg=PRODUCT_DIALOG_CARD,
            fg=PRODUCT_DIALOG_MUTED,
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).grid(row=row_index, column=0, sticky="w", pady=7, padx=(0, 16))
        ttk.Entry(parent, textvariable=variable, width=42).grid(row=row_index, column=1, sticky="ew", pady=7)

    def _cancel(self) -> None:
        self.grab_release()
        self.destroy()

    def _save(self) -> None:
        errors = validators.validate_required_fields(
            {
                "Product name": self.name_var.get(),
                "Category": self.category_var.get(),
                "Price": self.price_var.get(),
                "Stock quantity": self.stock_var.get(),
            }
        )

        # Additional field-level validations
        name_error = validators.validate_product_name(self.name_var.get())
        if name_error:
            errors.append(name_error)

        category_error = validators.validate_category(self.category_var.get())
        if category_error and "required" not in (category_error or ""):
            errors.append(category_error)

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors), parent=self)
            return

        try:
            price = validators.parse_price(self.price_var.get())
            stock_quantity = validators.parse_non_negative_int(self.stock_var.get(), "Stock quantity")
        except ValueError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
            return

        # Duplicate product name check
        from .. import database
        existing = database.get_all_products(self.name_var.get().strip())
        for product in existing:
            if product.name.lower() == self.name_var.get().strip().lower():
                # Allow if editing the same product
                if self._editing_id and product.id == self._editing_id:
                    continue
                messagebox.showerror(
                    "Duplicate Product",
                    f"A product named '{product.name}' already exists.",
                    parent=self,
                )
                return

        self.on_save(
            self.name_var.get().strip(),
            self.description_var.get().strip(),
            price,
            stock_quantity,
            self.category_var.get().strip(),
        )
        self.grab_release()
        self.destroy()

    def _center_over_parent(self) -> None:
        self.update_idletasks()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width - dialog_width) // 2
        y_position = (screen_height - dialog_height) // 2
        self.geometry(f"+{max(x_position, 0)}+{max(y_position, 0)}")


class DeleteProductsDialog(tk.Toplevel):
    """Custom confirmation overlay for deleting one or more products."""

    def __init__(self, master: tk.Misc, selected_products: list[dict]) -> None:
        super().__init__(master)
        self.confirmed = False
        self.selected_products = selected_products
        self.title("Delete Products" if len(selected_products) > 1 else "Delete Product")
        self.resizable(False, False)
        self.configure(bg=PRODUCT_DIALOG_BACKGROUND)
        self.transient(master)
        self.grab_set()

        shell = tk.Frame(
            self,
            bg=PRODUCT_DIALOG_CARD,
            highlightthickness=1,
            highlightbackground=PRODUCT_DIALOG_BORDER,
            padx=22,
            pady=20,
        )
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        item_count = len(selected_products)
        tk.Label(
            shell,
            text="Delete selected product" if item_count == 1 else "Delete selected products",
            bg=PRODUCT_DIALOG_CARD,
            fg=PRODUCT_DIALOG_DANGER,
            font=("Segoe UI Semibold", 16),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            shell,
            text=(
                "This removes the item from inventory. Products already linked to orders will be protected by the database."
                if item_count == 1
                else "This removes these items from inventory. Products already linked to orders will be protected by the database."
            ),
            bg=PRODUCT_DIALOG_CARD,
            fg=PRODUCT_DIALOG_MUTED,
            font=("Segoe UI", 10),
            wraplength=430,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(6, 14))

        list_panel = tk.Frame(
            shell,
            bg=PRODUCT_DIALOG_DANGER_SOFT,
            highlightthickness=1,
            highlightbackground="#FECACA",
            padx=12,
            pady=10,
        )
        list_panel.pack(fill="x")
        for product in selected_products[:4]:
            tk.Label(
                list_panel,
                text=f"{product['name']} · {currency_text(product['price'])} · Stock {product['stock']}",
                bg=PRODUCT_DIALOG_DANGER_SOFT,
                fg=PRODUCT_DIALOG_TEXT,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(fill="x", pady=2)
        if len(selected_products) > 4:
            tk.Label(
                list_panel,
                text=f"+ {len(selected_products) - 4} more",
                bg=PRODUCT_DIALOG_DANGER_SOFT,
                fg=PRODUCT_DIALOG_MUTED,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(fill="x", pady=(4, 0))

        action_bar = tk.Frame(shell, bg=PRODUCT_DIALOG_CARD)
        action_bar.pack(fill="x", pady=(18, 0))
        ttk.Button(action_bar, text="Cancel", command=self._cancel, style="Ghost.TButton", takefocus=False).pack(
            side="right",
            padx=(8, 0),
        )
        ttk.Button(action_bar, text="Delete", command=self._confirm, takefocus=False).pack(side="right")

        self.bind("<Escape>", lambda _event: self._cancel())
        self.after_idle(self._center_over_parent)

    def _confirm(self) -> None:
        self.confirmed = True
        self.grab_release()
        self.destroy()

    def _cancel(self) -> None:
        self.grab_release()
        self.destroy()

    def _center_over_parent(self) -> None:
        self.update_idletasks()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = (screen_width - dialog_width) // 2
        y_position = (screen_height - dialog_height) // 2
        self.geometry(f"+{max(x_position, 0)}+{max(y_position, 0)}")


class ProductsView(ttk.Frame):
    """Frame containing product CRUD controls."""

    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, padding=16)
        self.app = app

        self.search_var = tk.StringVar()
        self.results_var = tk.StringVar(value="0 products")
        self.search_var.trace_add("write", lambda *_args: self.load_products())

        top_bar = ttk.Frame(self, style="App.TFrame")
        top_bar.pack(fill="x", pady=(0, 12))
        ttk.Label(top_bar, text="Search Products").pack(side="left")
        ttk.Entry(top_bar, textvariable=self.search_var, width=32).pack(side="left", padx=8)
        ttk.Label(top_bar, textvariable=self.results_var, style="App.Subtle.TLabel").pack(side="left", padx=(8, 0))
        self.columns_button_placeholder = ttk.Frame(top_bar, style="App.TFrame")
        self.columns_button_placeholder.pack(side="right", padx=(8, 0))
        ttk.Button(top_bar, text="Refresh", command=self.load_products, takefocus=False).pack(side="right", padx=(0, 8))
        ttk.Button(top_bar, text="Delete Selected", command=self.delete_selected, takefocus=False).pack(side="right", padx=(0, 8))
        ttk.Button(top_bar, text="Edit Selected", command=self.open_edit_dialog, takefocus=False).pack(side="right", padx=(0, 8))
        ttk.Button(top_bar, text="Add Product", command=self.open_add_dialog, takefocus=False).pack(side="right")

        content = ttk.Frame(self, style="App.TFrame")
        content.pack(fill="both", expand=True)

        left_frame = ttk.Frame(content, style="App.TFrame")
        left_frame.pack(side="left", fill="both", expand=True)

        self.table = ModernDataTable(
            left_frame,
            [
                TableColumn("name", "Product", 280, frozen=True, can_hide=False),
                TableColumn("category", "Category", 180),
                TableColumn("price", "Price", 150, sort_type="float", formatter=currency_text),
                TableColumn("stock", "Stock", 120, sort_type="int"),
                TableColumn("id", "ID", 90, hidden=True, sort_type="int"),
                TableColumn("description", "Description", 420, hidden=True, formatter=truncate_text),
            ],
            height=18,
            empty_message="No products match the current search.",
            selectmode="extended",
        )
        self.table.pack(fill="both", expand=True)
        self.table.create_columns_button(self.columns_button_placeholder).pack(side="right")

        self.load_products()

    def load_products(self) -> None:
        rows = [
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "stock": product.stock_quantity,
                "description": product.description,
            }
            for product in database.get_all_products(self.search_var.get())
        ]
        self.table.set_rows(rows)
        count = len(rows)
        self.results_var.set(f"{count} product{'s' if count != 1 else ''}")

    def open_add_dialog(self) -> None:
        ProductDialog(self, "Add Product", self._add_product)

    def open_edit_dialog(self) -> None:
        selected_products = self.table.get_selected_rows()
        if not selected_products:
            messagebox.showwarning("No Selection", "Select a product to edit.", parent=self)
            return
        if len(selected_products) > 1:
            messagebox.showwarning("Single Selection Required", "Select only one product to edit.", parent=self)
            return
        product = self._to_product_payload(selected_products[0])
        ProductDialog(self, "Edit Product", lambda *args: self._edit_product(product["id"], *args), product)

    def delete_selected(self) -> None:
        selected_products = self.table.get_selected_rows()
        if not selected_products:
            messagebox.showwarning("No Selection", "Select a product to delete.", parent=self)
            return

        names = [product["name"] for product in selected_products]
        confirmation_dialog = DeleteProductsDialog(self, selected_products)
        self.wait_window(confirmation_dialog)
        if not confirmation_dialog.confirmed:
            return

        deleted_count = 0
        blocked_names: list[str] = []
        try:
            for product in selected_products:
                try:
                    database.delete_product(product["id"])
                    deleted_count += 1
                except sqlite3.IntegrityError:
                    blocked_names.append(product["name"])
        except sqlite3.DatabaseError as exc:
            messagebox.showerror(
                "Delete Failed",
                str(exc),
                parent=self,
            )
            return

        if blocked_names:
            messagebox.showerror(
                "Delete Blocked",
                "Some products are already linked to orders and could not be deleted:\n"
                + "\n".join(blocked_names),
                parent=self,
            )

        if deleted_count:
            status_label = ", ".join(names[:2])
            suffix = "..." if len(names) > 2 else ""
            self.app.set_status(f"Deleted {deleted_count} product(s): {status_label}{suffix}")
        self.app.refresh_all()

    def _add_product(self, name: str, description: str, price: float, stock_quantity: int, category: str) -> None:
        database.add_product(name, description, price, stock_quantity, category)
        self.app.set_status(f"Added product: {name}")
        self.app.refresh_all()

    def _edit_product(
        self,
        product_id: int,
        name: str,
        description: str,
        price: float,
        stock_quantity: int,
        category: str,
    ) -> None:
        database.update_product(product_id, name, description, price, stock_quantity, category)
        self.app.set_status(f"Updated product: {name}")
        self.app.refresh_all()

    def _get_selected_product(self) -> dict | None:
        row = self.table.get_selected_row()
        return self._to_product_payload(row) if row else None

    def _to_product_payload(self, row: dict) -> dict:
        return {
            "id": int(row["id"]),
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
            "stock_quantity": row["stock"],
            "description": row["description"],
        }
