"""Reporting view for products and orders."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk

from .. import database
from ..utils import pdf_reports
from .data_table import ModernDataTable, TableColumn, currency_text


LIST_BORDER = "#E2E8F0"
LIST_MUTED = "#64748B"
LIST_TEXT = "#0F172A"
LIST_SURFACE = "#FFFFFF"
LIST_ROW = "#F8FAFC"


class OrderedProductsList(ttk.Frame):
    """Receipt-style list for the selected order's products."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, style="App.TFrame")

        self.canvas = tk.Canvas(self, bg=LIST_SURFACE, highlightthickness=1, highlightbackground=LIST_BORDER)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=LIST_SURFACE, padx=10, pady=10)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._sync_content_width)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.set_items([])

    def set_items(self, items: list[dict]) -> None:
        """Render ordered products as compact receipt lines."""
        for child in self.content.winfo_children():
            child.destroy()

        if not items:
            tk.Label(
                self.content,
                text="Select an order to inspect its products.",
                bg=LIST_SURFACE,
                fg=LIST_MUTED,
                font=("Segoe UI", 10),
                pady=24,
            ).pack(fill="x")
            return

        for index, item in enumerate(items):
            row = tk.Frame(
                self.content,
                bg=LIST_ROW if index % 2 == 0 else LIST_SURFACE,
                highlightthickness=1,
                highlightbackground=LIST_BORDER,
                padx=12,
                pady=10,
            )
            row.pack(fill="x", pady=(0, 8))

            tk.Label(
                row,
                text=str(item["product"]),
                bg=row["bg"],
                fg=LIST_TEXT,
                font=("Segoe UI Semibold", 10),
                anchor="w",
                justify="left",
                wraplength=260,
            ).pack(fill="x")

            details = tk.Frame(row, bg=row["bg"])
            details.pack(fill="x", pady=(6, 0))
            tk.Label(
                details,
                text=f"Qty: {item['qty']}",
                bg=row["bg"],
                fg=LIST_MUTED,
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(side="left")
            tk.Label(
                details,
                text=currency_text(item["price"]),
                bg=row["bg"],
                fg=LIST_TEXT,
                font=("Segoe UI Semibold", 10),
                anchor="e",
            ).pack(side="right")

    def _sync_scroll_region(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_content_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> str:
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        return "break"


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
                TableColumn("order_id", "Order ID", 105, frozen=True, can_hide=False, sort_type="int"),
                TableColumn("customer", "Customer", 220, frozen=True, can_hide=False),
                TableColumn("date", "Date", 175, sort_type="date"),
                TableColumn("total", "Total", 145, sort_type="float", formatter=currency_text),
                TableColumn("email_sent", "Receipt", 110, sort_type="bool_text"),
                TableColumn("units", "Units", 90, sort_type="int"),
                TableColumn("items_summary", "Items", 360, hidden=True),
                TableColumn("line_items", "Lines", 90, sort_type="int", hidden=True),
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
        self.order_items_list = OrderedProductsList(items_frame)
        self.order_items_list.pack(fill="both", expand=True)

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

        self.order_items_list.set_items(
            [
                {"product": item[0], "qty": item[1], "price": item[2]}
                for item in database.get_order_items(order_id)
            ]
        )

    def _clear_order_details(self) -> None:
        for variable in self.order_detail_vars.values():
            variable.set("-")
        self.order_items_list.set_items([])

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
