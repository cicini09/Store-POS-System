"""Reporting view for products and orders."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk

from .. import database
from ..utils import pdf_reports
from .data_table import ModernDataTable, TableColumn, currency_text


class ReportsView(ttk.Frame):
    """Frame containing products and orders reports."""

    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, padding=16)
        self.app = app
        self.inventory_rows: list[dict] = []
        self.orders_rows: list[dict] = []
        self.inventory_results_var = tk.StringVar(value="0 rows")
        self.orders_results_var = tk.StringVar(value="0 rows")

        self.notebook = ttk.Notebook(self, takefocus=False, style="App.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.inventory_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.orders_tab = ttk.Frame(self.notebook, padding=12, style="App.TFrame")
        self.notebook.add(self.inventory_tab, text="Products Report")
        self.notebook.add(self.orders_tab, text="Orders Report")

        self._build_inventory_tab()
        self._build_orders_tab()
        self.refresh_reports()

    def _build_inventory_tab(self) -> None:
        top_bar = ttk.Frame(self.inventory_tab, style="App.TFrame")
        top_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(top_bar, text="Search Products Report").pack(side="left")
        self.inventory_search_var = tk.StringVar()
        self.inventory_search_var.trace_add("write", lambda *_args: self._render_inventory_rows())
        ttk.Entry(top_bar, textvariable=self.inventory_search_var, width=36).pack(side="left", padx=8)
        ttk.Label(top_bar, textvariable=self.inventory_results_var, style="App.Subtle.TLabel").pack(side="left", padx=(8, 0))
        ttk.Label(
            top_bar,
            text="Keep product identity fixed and reveal secondary metrics when needed.",
            style="App.Subtle.TLabel",
        ).pack(side="left", padx=(16, 0))
        self.inventory_columns_placeholder = ttk.Frame(top_bar, style="App.TFrame")
        self.inventory_columns_placeholder.pack(side="right", padx=(8, 0))
        ttk.Button(
            top_bar,
            text="Export Products PDF",
            command=self.export_inventory_pdf,
            takefocus=False,
        ).pack(side="right")

        self.inventory_table = ModernDataTable(
            self.inventory_tab,
            [
                TableColumn("product", "Product", 250, frozen=True, can_hide=False),
                TableColumn("category", "Category", 150),
                TableColumn("price", "Price", 130, sort_type="float", formatter=currency_text),
                TableColumn("on_hand", "On Hand", 110, sort_type="int"),
                TableColumn("sold", "Units Sold", 120, sort_type="int"),
            ],
            height=18,
            empty_message="No products matched the current report filters.",
        )
        self.inventory_table.pack(fill="both", expand=True)
        self.inventory_table.create_columns_button(self.inventory_columns_placeholder).pack(side="right")

    def _build_orders_tab(self) -> None:
        top_bar = ttk.Frame(self.orders_tab, style="App.TFrame")
        top_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(top_bar, text="Search Orders Report").pack(side="left")
        self.orders_search_var = tk.StringVar()
        self.orders_search_var.trace_add("write", lambda *_args: self._render_orders_rows())
        ttk.Entry(top_bar, textvariable=self.orders_search_var, width=36).pack(side="left", padx=8)
        ttk.Label(top_bar, textvariable=self.orders_results_var, style="App.Subtle.TLabel").pack(side="left", padx=(8, 0))
        ttk.Label(
            top_bar,
            text="Review customer, basket summary, units, and receipt status at a glance.",
            style="App.Subtle.TLabel",
        ).pack(side="left", padx=(16, 0))
        self.orders_columns_placeholder = ttk.Frame(top_bar, style="App.TFrame")
        self.orders_columns_placeholder.pack(side="right", padx=(8, 0))
        ttk.Button(
            top_bar,
            text="Export Orders PDF",
            command=self.export_orders_pdf,
            takefocus=False,
        ).pack(side="right")

        content = ttk.PanedWindow(self.orders_tab, orient="horizontal")
        content.pack(fill="both", expand=True)

        left_panel = ttk.Frame(content, style="App.TFrame")
        right_panel = ttk.Frame(content, style="App.TFrame")
        content.add(left_panel, weight=4)
        content.add(right_panel, weight=3)

        self.orders_table = ModernDataTable(
            left_panel,
            [
                TableColumn("order_id", "Order ID", 100, frozen=True, can_hide=False, sort_type="int"),
                TableColumn("customer", "Customer", 180, frozen=True, can_hide=False),
                TableColumn("items_summary", "Items", 340),
                TableColumn("units", "Units", 90, sort_type="int"),
                TableColumn("line_items", "Lines", 90, sort_type="int", hidden=True),
                TableColumn("date", "Date", 180, sort_type="date"),
                TableColumn("total", "Total", 130, sort_type="float", formatter=currency_text),
                TableColumn("email_sent", "Receipt", 110, sort_type="bool_text"),
                TableColumn("email", "Email", 240, hidden=True),
                TableColumn("phone", "Phone", 150, hidden=True),
            ],
            height=18,
            empty_message="No orders matched the current report filters.",
            selectmode="browse",
        )
        self.orders_table.pack(fill="both", expand=True)
        self.orders_table.bind_selection_change(self._on_order_select)
        self.orders_table.create_columns_button(self.orders_columns_placeholder).pack(side="right")

        detail_header = ttk.LabelFrame(right_panel, text="Order Details", padding=14, style="App.TLabelframe")
        detail_header.pack(fill="x")
        self.order_detail_vars = {
            "order_id": tk.StringVar(value="-"),
            "customer": tk.StringVar(value="-"),
            "email": tk.StringVar(value="-"),
            "phone": tk.StringVar(value="-"),
            "date": tk.StringVar(value="-"),
            "total": tk.StringVar(value="-"),
            "items": tk.StringVar(value="-"),
            "units": tk.StringVar(value="-"),
            "status": tk.StringVar(value="-"),
        }
        for label_text, key in [
            ("Order ID", "order_id"),
            ("Customer", "customer"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Date", "date"),
            ("Total", "total"),
            ("Items", "items"),
            ("Units", "units"),
            ("Receipt", "status"),
        ]:
            row = ttk.Frame(detail_header, style="App.TFrame")
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"{label_text}:", width=12).pack(side="left")
            ttk.Label(row, textvariable=self.order_detail_vars[key]).pack(side="left")

        items_frame = ttk.LabelFrame(right_panel, text="Ordered Products", padding=14, style="App.TLabelframe")
        items_frame.pack(fill="both", expand=True, pady=(12, 0))
        self.order_items_table = ModernDataTable(
            items_frame,
            [
                TableColumn("product", "Product", 240, frozen=True, can_hide=False),
                TableColumn("qty", "Qty", 80, sort_type="int"),
                TableColumn("price", "Unit Price", 130, sort_type="float", formatter=currency_text),
                TableColumn("subtotal", "Subtotal", 130, sort_type="float", formatter=currency_text),
            ],
            height=12,
            empty_message="Select an order to inspect its line items.",
            selectmode="browse",
        )
        self.order_items_table.pack(fill="both", expand=True)

    def refresh_reports(self) -> None:
        self.inventory_rows = [
            {
                "product": row[0],
                "category": row[1],
                "price": row[2],
                "on_hand": row[3],
                "sold": row[4],
            }
            for row in database.get_inventory_report()
        ]
        self.orders_rows = [
            {
                "order_id": row[0],
                "customer": row[1],
                "email": row[2],
                "phone": row[3],
                "date": row[4],
                "total": row[5],
                "email_sent": row[6],
                "line_items": row[7],
                "units": row[8],
                "items_summary": row[9],
            }
            for row in database.get_orders_report()
        ]
        self._render_inventory_rows()
        self._render_orders_rows()

    def _render_inventory_rows(self) -> None:
        query = self.inventory_search_var.get().strip().lower()
        rows = [
            row for row in self.inventory_rows
            if not query or query in " ".join(str(value).lower() for value in row.values())
        ]
        self.inventory_table.set_rows(rows)
        count = len(rows)
        self.inventory_results_var.set(f"{count} row{'s' if count != 1 else ''}")

    def _render_orders_rows(self) -> None:
        query = self.orders_search_var.get().strip().lower()
        rows = [
            row for row in self.orders_rows
            if not query or query in " ".join(str(value).lower() for value in row.values())
        ]
        self.orders_table.set_rows(rows)
        count = len(rows)
        self.orders_results_var.set(f"{count} row{'s' if count != 1 else ''}")

        if rows:
            self.orders_table.select_first()
        else:
            self._clear_order_details()

    def _on_order_select(self, _event=None) -> None:
        row = self.orders_table.get_selected_row()
        if not row:
            self._clear_order_details()
            return

        order_id = int(row["order_id"])
        self.order_detail_vars["order_id"].set(str(order_id))
        self.order_detail_vars["customer"].set(row["customer"])
        self.order_detail_vars["email"].set(row["email"])
        self.order_detail_vars["phone"].set(row["phone"] or "-")
        self.order_detail_vars["date"].set(row["date"])
        self.order_detail_vars["total"].set(currency_text(row["total"]))
        self.order_detail_vars["items"].set(f"{row['line_items']} line(s)")
        self.order_detail_vars["units"].set(str(row["units"]))
        self.order_detail_vars["status"].set(row["email_sent"])

        self.order_items_table.set_rows(
            [
                {"product": item[0], "qty": item[1], "price": item[2], "subtotal": item[3]}
                for item in database.get_order_items(order_id)
            ]
        )

    def _clear_order_details(self) -> None:
        for variable in self.order_detail_vars.values():
            variable.set("-")
        self.order_items_table.set_rows([])

    def export_inventory_pdf(self) -> None:
        rows = database.get_inventory_report()
        try:
            path = pdf_reports.generate_inventory_pdf(rows)
        except RuntimeError as exc:
            messagebox.showerror("PDF Export Unavailable", str(exc), parent=self)
            self.app.set_status("Products PDF export failed: ReportLab is not installed.")
            return
        self._handle_export_result(path, "Products report")

    def export_orders_pdf(self) -> None:
        rows = database.get_orders_report()
        try:
            path = pdf_reports.generate_orders_pdf(rows)
        except RuntimeError as exc:
            messagebox.showerror("PDF Export Unavailable", str(exc), parent=self)
            self.app.set_status("Orders PDF export failed: ReportLab is not installed.")
            return
        self._handle_export_result(path, "Orders report")

    def _handle_export_result(self, path: str, label: str) -> None:
        self.app.set_status(f"{label} exported to {path}")
        try:
            os.startfile(path)
        except OSError:
            messagebox.showinfo("PDF Exported", f"{label} saved to:\n{path}", parent=self)
