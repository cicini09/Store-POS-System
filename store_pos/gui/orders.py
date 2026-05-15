"""Order processing view."""

from __future__ import annotations

import sqlite3
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .. import database
from ..utils import email_sender, validators
from .data_table import ModernDataTable, TableColumn, currency_text


class OrdersView(ttk.Frame):
    """Frame for creating customer orders and sending receipts."""

    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, padding=16)
        self.app = app
        self.products_by_name: dict[str, dict] = {}
        self.cart: list[dict] = []

        customer_frame = ttk.LabelFrame(self, text="Customer Details", padding=12, style="App.TLabelframe")
        customer_frame.pack(fill="x", pady=(0, 12))

        self.customer_name_var = tk.StringVar()
        self.customer_email_var = tk.StringVar()
        self.customer_phone_var = tk.StringVar()

        self._build_customer_row(customer_frame, "Name", self.customer_name_var, 0)
        self._build_customer_row(customer_frame, "Email", self.customer_email_var, 1)
        self._build_customer_row(customer_frame, "Phone", self.customer_phone_var, 2)

        order_frame = ttk.LabelFrame(self, text="Add Product to Cart", padding=12, style="App.TLabelframe")
        order_frame.pack(fill="x", pady=(0, 12))

        self.product_var = tk.StringVar()
        self.quantity_var = tk.StringVar(value="1")

        ttk.Label(order_frame, text="Product").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(order_frame, text="Quantity").grid(row=0, column=2, sticky="w", pady=6, padx=(12, 0))

        self.product_combobox = ttk.Combobox(
            order_frame,
            textvariable=self.product_var,
            state="readonly",
            width=36,
            height=10,
            takefocus=False,
        )
        self.product_combobox.grid(row=0, column=1, sticky="ew", pady=6)
        ttk.Entry(order_frame, textvariable=self.quantity_var, width=10).grid(
            row=0,
            column=3,
            sticky="w",
            pady=6,
            padx=(8, 0),
        )
        ttk.Button(order_frame, text="Add to Cart", command=self.add_to_cart, takefocus=False).grid(
            row=0,
            column=4,
            sticky="w",
            padx=(12, 0),
        )

        order_frame.columnconfigure(1, weight=1)

        cart_frame = ttk.LabelFrame(self, text="Cart", padding=12, style="App.TLabelframe")
        cart_frame.pack(fill="both", expand=True)

        self.cart_table = ModernDataTable(
            cart_frame,
            [
                TableColumn("product", "Product", 300, frozen=True, can_hide=False),
                TableColumn("qty", "Qty", 90, sort_type="int"),
                TableColumn("unit_price", "Unit Price", 130, sort_type="float", formatter=currency_text),
                TableColumn("subtotal", "Subtotal", 140, sort_type="float", formatter=currency_text),
            ],
            height=13,
            empty_message="Add products to start building the cart.",
            selectmode="extended",
        )
        self.cart_table.pack(fill="both", expand=True)

        action_frame = ttk.Frame(self, style="App.TFrame")
        action_frame.pack(fill="x", pady=(12, 0))
        self.total_var = tk.StringVar(value="Total: PHP 0.00")
        ttk.Label(action_frame, textvariable=self.total_var, font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(action_frame, text="Remove Selected Item", command=self.remove_selected_item, takefocus=False).pack(side="right")
        ttk.Button(action_frame, text="Place Order", command=self.place_order, takefocus=False).pack(side="right", padx=(0, 10))

        self.refresh_products()

    def _build_customer_row(self, frame: ttk.LabelFrame, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=variable, width=50).grid(row=row, column=1, sticky="ew", pady=6)
        frame.columnconfigure(1, weight=1)

    def refresh_products(self) -> None:
        self.products_by_name = {
            product.name: {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
            }
            for product in database.get_all_products()
            if product.stock_quantity > 0
        }
        product_names = sorted(self.products_by_name)
        self.product_combobox["values"] = product_names
        if product_names and self.product_var.get() not in self.products_by_name:
            self.product_var.set(product_names[0])
        elif not product_names:
            self.product_var.set("")

    def add_to_cart(self) -> None:
        product_name = self.product_var.get().strip()
        if not product_name:
            messagebox.showwarning("No Product", "Select a product to add.", parent=self)
            return

        try:
            quantity = validators.parse_positive_int(self.quantity_var.get(), "Quantity")
        except ValueError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
            return

        product = self.products_by_name[product_name]
        existing_quantity = sum(item["quantity"] for item in self.cart if item["product_id"] == product["id"])
        if existing_quantity + quantity > int(product["stock_quantity"]):
            messagebox.showerror(
                "Stock Unavailable",
                f"Only {product['stock_quantity']} units of {product_name} are available.",
                parent=self,
            )
            return

        for item in self.cart:
            if item["product_id"] == product["id"]:
                item["quantity"] += quantity
                self._refresh_cart()
                return

        self.cart.append(
            {
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
            }
        )
        self._refresh_cart()

    def remove_selected_item(self) -> None:
        selected_rows = self.cart_table.get_selected_rows()
        if not selected_rows:
            messagebox.showwarning("No Selection", "Select a cart item to remove.", parent=self)
            return

        selected_ids = {row["product_id"] for row in selected_rows}
        self.cart = [item for item in self.cart if item["product_id"] not in selected_ids]
        self._refresh_cart()

    def place_order(self) -> None:
        errors = validators.validate_required_fields(
            {
                "Customer name": self.customer_name_var.get(),
                "Customer email": self.customer_email_var.get(),
            }
        )
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors), parent=self)
            return
        if not validators.is_valid_email(self.customer_email_var.get()):
            messagebox.showerror("Validation Error", "Enter a valid email address.", parent=self)
            return
        if not self.cart:
            messagebox.showerror("Empty Cart", "Add at least one product to the cart first.", parent=self)
            return

        customer_id = database.get_or_create_customer(
            self.customer_name_var.get(),
            self.customer_email_var.get(),
            self.customer_phone_var.get(),
        )
        items = [{"product_id": item["product_id"], "quantity": item["quantity"]} for item in self.cart]

        try:
            order_id = database.save_order(customer_id, items)
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror("Order Failed", str(exc), parent=self)
            self.refresh_products()
            return

        receipt_data = database.get_order_receipt_data(order_id)
        self.clear_form()
        self.app.refresh_all()
        self.app.set_status(f"Order #{order_id} placed. Processing receipt...")

        thread = threading.Thread(
            target=self._send_receipt_async,
            args=(order_id, receipt_data, receipt_data["customer_email"]),
            daemon=True,
        )
        thread.start()

    def clear_form(self) -> None:
        self.customer_name_var.set("")
        self.customer_email_var.set("")
        self.customer_phone_var.set("")
        self.quantity_var.set("1")
        self.cart.clear()
        self._refresh_cart()

    def _refresh_cart(self) -> None:
        total = 0.0
        rows: list[dict] = []
        for item in self.cart:
            subtotal = round(item["quantity"] * item["unit_price"], 2)
            total += subtotal
            rows.append(
                {
                    "product_id": item["product_id"],
                    "product": item["product_name"],
                    "qty": item["quantity"],
                    "unit_price": item["unit_price"],
                    "subtotal": subtotal,
                }
            )

        self.cart_table.set_rows(rows)
        self.total_var.set(f"Total: PHP {total:,.2f}")

    def _send_receipt_async(self, order_id: int, order_data: dict, customer_email: str) -> None:
        sent = email_sender.send_receipt(order_data, customer_email)
        database.set_order_email_status(order_id, sent)

        def update_ui() -> None:
            self.app.refresh_all()
            if sent:
                self.app.set_status(
                    f"Order #{order_id} completed. Receipt processed for {customer_email}."
                )
            else:
                self.app.set_status(
                    f"Order #{order_id} completed, but receipt delivery failed."
                )

        self.after(0, update_ui)
