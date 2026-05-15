"""Products management view."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from .. import database
from ..utils import validators
from .data_table import ModernDataTable, TableColumn, currency_text, truncate_text


class ProductDialog(tk.Toplevel):
    """Modal dialog used for adding or editing products."""

    def __init__(self, master: tk.Misc, title: str, on_save, product: dict | None = None) -> None:
        super().__init__(master)
        self.on_save = on_save
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.name_var = tk.StringVar(value=(product or {}).get("name", ""))
        self.category_var = tk.StringVar(value=(product or {}).get("category", ""))
        self.price_var = tk.StringVar(value=str((product or {}).get("price", "")))
        self.stock_var = tk.StringVar(value=str((product or {}).get("stock_quantity", "")))
        self.description_var = tk.StringVar(value=(product or {}).get("description", ""))

        frame = ttk.Frame(self, padding=18)
        frame.pack(fill="both", expand=True)

        labels = ["Name", "Category", "Price", "Stock Quantity", "Description"]
        vars_ = [
            self.name_var,
            self.category_var,
            self.price_var,
            self.stock_var,
            self.description_var,
        ]
        for idx, (label_text, variable) in enumerate(zip(labels, vars_), start=0):
            ttk.Label(frame, text=label_text).grid(row=idx, column=0, sticky="w", pady=6)
            ttk.Entry(frame, textvariable=variable, width=36).grid(
                row=idx,
                column=1,
                sticky="ew",
                pady=6,
            )

        ttk.Button(frame, text="Save", command=self._save, takefocus=False).grid(
            row=len(labels),
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 0),
        )

        frame.columnconfigure(1, weight=1)
        self.bind("<Return>", lambda _event: self._save())

    def _save(self) -> None:
        errors = validators.validate_required_fields(
            {
                "Product name": self.name_var.get(),
                "Category": self.category_var.get(),
                "Price": self.price_var.get(),
                "Stock quantity": self.stock_var.get(),
            }
        )
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors), parent=self)
            return

        try:
            price = validators.parse_price(self.price_var.get())
            stock_quantity = validators.parse_non_negative_int(self.stock_var.get(), "Stock quantity")
        except ValueError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
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
        item_count = len(selected_products)
        confirmed = messagebox.askyesno(
            "Delete Products" if item_count > 1 else "Delete Product",
            f"Delete {item_count} selected product{'s' if item_count != 1 else ''} from inventory?",
            parent=self,
        )
        if not confirmed:
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
