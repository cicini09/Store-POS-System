"""Order processing view."""

from __future__ import annotations

import sqlite3
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .. import database
from ..utils import email_sender, validators
from .data_table import ModernDataTable, TableColumn, currency_text


PICKER_CARD = "#FFFFFF"
PICKER_BORDER = "#CBD5E1"
PICKER_SOFT = "#F8FAFC"
PICKER_TEXT = "#0F172A"
PICKER_MUTED = "#64748B"


class OrdersView(ttk.Frame):
    """Frame for creating customer orders and sending receipts."""

    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, padding=16)
        self.app = app
        self.products_by_id: dict[int, dict] = {}
        self.product_rows: list[dict] = []
        self.selected_product_id: int | None = None
        self.cart: list[dict] = []

        customer_frame = ttk.LabelFrame(self, text="Customer Details", padding=14, style="App.TLabelframe")
        customer_frame.pack(fill="x", pady=(0, 12))

        self.customer_name_var = tk.StringVar()
        self.customer_email_var = tk.StringVar()
        self.customer_phone_var = tk.StringVar()
        self.product_search_var = tk.StringVar()
        self.product_results_var = tk.StringVar(value="0 available")
        self.product_search_var.trace_add("write", lambda *_args: self._render_product_rows())

        self._build_customer_field(customer_frame, "Name", self.customer_name_var, 0)
        self._build_customer_field(customer_frame, "Email", self.customer_email_var, 1)
        self._build_customer_field(customer_frame, "Phone", self.customer_phone_var, 2)

        order_workspace = ttk.PanedWindow(self, orient="horizontal")
        order_workspace.pack(fill="both", expand=True, pady=(0, 12))

        self.quantity_var = tk.StringVar(value="1")
        self.selected_product_name_var = tk.StringVar(value="Select a product")
        self.selected_product_meta_var = tk.StringVar(value="Price and stock will appear here.")

        product_panel = ttk.LabelFrame(order_workspace, text="Choose Product", padding=14, style="App.TLabelframe")
        cart_panel = ttk.LabelFrame(order_workspace, text="Cart", padding=14, style="App.TLabelframe")
        order_workspace.add(product_panel, weight=3)
        order_workspace.add(cart_panel, weight=2)

        product_toolbar = ttk.Frame(product_panel, style="App.TFrame")
        product_toolbar.pack(fill="x", pady=(0, 10))
        ttk.Label(product_toolbar, text="Search").pack(side="left")
        ttk.Entry(product_toolbar, textvariable=self.product_search_var, width=34).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Label(product_toolbar, textvariable=self.product_results_var, style="App.Subtle.TLabel").pack(side="left")

        self.product_table = ModernDataTable(
            product_panel,
            [
                TableColumn("name", "Product", 250, frozen=True, can_hide=False),
                TableColumn("category", "Category", 145),
                TableColumn("price", "Price", 130, sort_type="float", formatter=currency_text),
                TableColumn("stock", "Stock", 95, sort_type="int"),
                TableColumn("id", "ID", 80, hidden=True, sort_type="int"),
            ],
            height=9,
            empty_message="No available products match the current search.",
            selectmode="browse",
        )
        self.product_table.pack(fill="both", expand=True)
        self.product_table.bind_selection_change(self._on_product_selected)

        selection_panel = tk.Frame(
            product_panel,
            bg=PICKER_CARD,
            highlightthickness=1,
            highlightbackground=PICKER_BORDER,
            padx=14,
            pady=12,
        )
        selection_panel.pack(fill="x", pady=(12, 0))
        selection_details = tk.Frame(selection_panel, bg=PICKER_CARD)
        selection_details.pack(side="left", fill="x", expand=True)
        tk.Label(
            selection_details,
            textvariable=self.selected_product_name_var,
            bg=PICKER_CARD,
            fg=PICKER_TEXT,
            font=("Segoe UI Semibold", 11),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            selection_details,
            textvariable=self.selected_product_meta_var,
            bg=PICKER_CARD,
            fg=PICKER_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", pady=(3, 0))

        quantity_frame = tk.Frame(selection_panel, bg=PICKER_CARD)
        quantity_frame.pack(side="right", padx=(14, 0))
        tk.Label(
            quantity_frame,
            text="Qty",
            bg=PICKER_CARD,
            fg=PICKER_MUTED,
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).pack(anchor="w")
        ttk.Spinbox(
            quantity_frame,
            from_=1,
            to=999,
            textvariable=self.quantity_var,
            width=7,
            justify="center",
            takefocus=False,
        ).pack(anchor="e", pady=(3, 0))

        ttk.Button(selection_panel, text="Add to Cart", command=self.add_to_cart, takefocus=False).pack(
            side="right",
            padx=(12, 0),
        )

        self.cart_table = ModernDataTable(
            cart_panel,
            [
                TableColumn("product", "Product", 300, frozen=True, can_hide=False),
                TableColumn("qty", "Qty", 90, sort_type="int"),
                TableColumn("unit_price", "Unit Price", 130, sort_type="float", formatter=currency_text),
                TableColumn("subtotal", "Subtotal", 140, sort_type="float", formatter=currency_text),
            ],
            height=9,
            empty_message="Add products to start building the cart.",
            selectmode="extended",
        )
        self.cart_table.pack(fill="both", expand=True)

        # Cart action panel (same style as the Choose Product selection panel)
        cart_action_panel = tk.Frame(
            cart_panel,
            bg=PICKER_CARD,
            highlightthickness=1,
            highlightbackground=PICKER_BORDER,
            padx=14,
            pady=12,
        )
        cart_action_panel.pack(fill="x", pady=(12, 0))

        # Left side: total price
        self.total_var = tk.StringVar(value="Total: PHP 0.00")
        tk.Label(
            cart_action_panel,
            textvariable=self.total_var,
            bg=PICKER_CARD,
            fg=PICKER_TEXT,
            font=("Segoe UI Semibold", 13),
            anchor="w",
        ).pack(side="left")

        # Right side: Place Order button
        ttk.Button(
            cart_action_panel,
            text="Place Order",
            command=self.place_order,
            takefocus=False,
        ).pack(side="right", padx=(12, 0))

        # Right side: Remove button
        ttk.Button(
            cart_action_panel,
            text="Remove",
            command=self.remove_selected_item,
            style="Ghost.TButton",
            takefocus=False,
        ).pack(side="right")

        self.refresh_products()

    def _build_customer_field(self, frame: ttk.LabelFrame, label: str, variable: tk.StringVar, column: int) -> None:
        field = ttk.Frame(frame, style="App.TFrame")
        field.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0))
        ttk.Label(field, text=label, style="App.Subtle.TLabel").pack(anchor="w")
        ttk.Entry(field, textvariable=variable).pack(fill="x", pady=(4, 0))
        frame.columnconfigure(column, weight=1)

    def refresh_products(self) -> None:
        previous_product_id = self.selected_product_id
        products = [
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "category": product.category,
            }
            for product in database.get_all_products()
            if product.stock_quantity > 0
        ]
        self.products_by_id = {product["id"]: product for product in products}
        self.product_rows = [
            {
                "id": product["id"],
                "name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "stock": product["stock_quantity"],
            }
            for product in products
        ]
        self._render_product_rows(preferred_product_id=previous_product_id)

    def _render_product_rows(self, preferred_product_id: int | None = None) -> None:
        query = self.product_search_var.get().strip().lower()
        rows = [
            row for row in self.product_rows
            if not query or query in f"{row['name']} {row['category']}".lower()
        ]
        self.product_table.set_rows(rows)
        count = len(rows)
        self.product_results_var.set(f"{count} available")

        preferred_product_id = preferred_product_id if preferred_product_id in self.products_by_id else None
        if rows:
            self.product_table.select_first()
            if preferred_product_id:
                self._select_product_by_id(preferred_product_id)
        else:
            self.selected_product_id = None
            self.selected_product_name_var.set("No product selected")
            self.selected_product_meta_var.set("Adjust the search or add inventory first.")

    def _select_product_by_id(self, product_id: int) -> None:
        self.product_table.select_row_by_value("id", product_id)

    def _on_product_selected(self) -> None:
        row = self.product_table.get_selected_row()
        if not row:
            self.selected_product_id = None
            self.selected_product_name_var.set("No product selected")
            self.selected_product_meta_var.set("Select an available product from the list.")
            return

        self.selected_product_id = int(row["id"])
        self.selected_product_name_var.set(str(row["name"]))
        self.selected_product_meta_var.set(
            f"{currency_text(row['price'])} · {row['stock']} in stock · {row['category'] or 'Uncategorized'}"
        )

    def add_to_cart(self) -> None:
        if self.selected_product_id is None:
            messagebox.showwarning("No Product", "Select a product to add.", parent=self)
            return

        try:
            quantity = validators.parse_positive_int(self.quantity_var.get(), "Quantity")
        except ValueError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self)
            return

        product = self.products_by_id[self.selected_product_id]
        existing_quantity = sum(item["quantity"] for item in self.cart if item["product_id"] == product["id"])
        if existing_quantity + quantity > int(product["stock_quantity"]):
            messagebox.showerror(
                "Stock Unavailable",
                f"Only {product['stock_quantity']} units of {product['name']} are available.",
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
