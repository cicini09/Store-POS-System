"""Products management view."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from .. import database
from ..utils.treeview_sort import attach_sorting
from ..utils import validators


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
        self.search_var.trace_add("write", lambda *_args: self.load_products())

        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", pady=(0, 12))
        ttk.Label(top_bar, text="Search Products").pack(side="left")
        ttk.Entry(top_bar, textvariable=self.search_var, width=32).pack(side="left", padx=8)
        ttk.Button(top_bar, text="Add Product", command=self.open_add_dialog, takefocus=False).pack(side="right")

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True)

        left_frame = ttk.Frame(content)
        right_frame = ttk.LabelFrame(content, text="Actions", padding=12)
        left_frame.pack(side="left", fill="both", expand=True)
        right_frame.pack(side="left", fill="y", padx=(16, 0))

        columns = ("id", "name", "category", "price", "stock", "description")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=18)
        headings = {
            "id": "ID",
            "name": "Name",
            "category": "Category",
            "price": "Price",
            "stock": "Stock",
            "description": "Description",
        }
        widths = {"id": 70, "name": 230, "category": 150, "price": 120, "stock": 90, "description": 340}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], minwidth=widths[column], anchor="w", stretch=False)
        attach_sorting(self.tree, {"id": "int", "price": "float", "stock": "int"})

        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        ttk.Button(right_frame, text="Edit Selected", command=self.open_edit_dialog, takefocus=False).pack(fill="x", pady=4)
        ttk.Button(right_frame, text="Delete Selected", command=self.delete_selected, takefocus=False).pack(fill="x", pady=4)
        ttk.Button(right_frame, text="Refresh", command=self.load_products, takefocus=False).pack(fill="x", pady=4)

        self.load_products()

    def load_products(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for product in database.get_all_products(self.search_var.get()):
            self.tree.insert(
                "",
                "end",
                values=(
                    product.id,
                    product.name,
                    product.category,
                    f"PHP {product.price:,.2f}",
                    product.stock_quantity,
                    product.description,
                ),
            )

    def open_add_dialog(self) -> None:
        ProductDialog(self, "Add Product", self._add_product)

    def open_edit_dialog(self) -> None:
        product = self._get_selected_product()
        if not product:
            messagebox.showwarning("No Selection", "Select a product to edit.", parent=self)
            return
        ProductDialog(self, "Edit Product", lambda *args: self._edit_product(product["id"], *args), product)

    def delete_selected(self) -> None:
        product = self._get_selected_product()
        if not product:
            messagebox.showwarning("No Selection", "Select a product to delete.", parent=self)
            return

        confirmed = messagebox.askyesno(
            "Delete Product",
            f"Delete '{product['name']}' from inventory?",
            parent=self,
        )
        if not confirmed:
            return

        try:
            database.delete_product(product["id"])
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Delete Blocked",
                "This product is already linked to orders and cannot be deleted.",
                parent=self,
            )
            return

        self.app.set_status(f"Deleted product: {product['name']}")
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
        selection = self.tree.selection()
        if not selection:
            return None
        values = self.tree.item(selection[0], "values")
        return {
            "id": int(values[0]),
            "name": values[1],
            "category": values[2],
            "price": values[3].replace("PHP ", "").replace(",", ""),
            "stock_quantity": values[4],
            "description": values[5],
        }
