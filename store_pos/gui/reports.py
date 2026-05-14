"""Reporting view for products and orders."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk

from .. import database
from ..utils import pdf_reports
from ..utils.treeview_sort import attach_sorting


class ReportsView(ttk.Frame):
    """Frame containing products and orders reports."""

    def __init__(self, master: tk.Misc, app) -> None:
        super().__init__(master, padding=16)
        self.app = app
        self.inventory_rows: list[tuple] = []
        self.orders_rows: list[tuple] = []

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
        ttk.Button(
            top_bar,
            text="Export Products PDF",
            command=self.export_inventory_pdf,
            takefocus=False,
        ).pack(side="right")

        self.inventory_tree = self._build_tree(
            self.inventory_tab,
            ("product", "category", "price", "on_hand", "sold"),
            [
                ("product", "Product", 250),
                ("category", "Category", 150),
                ("price", "Price", 130),
                ("on_hand", "On Hand", 100),
                ("sold", "Units Sold", 100),
            ],
            fill_parent=True,
        )
        attach_sorting(self.inventory_tree, {"price": "float", "on_hand": "int", "sold": "int"})

    def _build_orders_tab(self) -> None:
        top_bar = ttk.Frame(self.orders_tab, style="App.TFrame")
        top_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(top_bar, text="Search Orders Report").pack(side="left")
        self.orders_search_var = tk.StringVar()
        self.orders_search_var.trace_add("write", lambda *_args: self._render_orders_rows())
        ttk.Entry(top_bar, textvariable=self.orders_search_var, width=36).pack(side="left", padx=8)
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

        self.orders_tree = self._build_tree(
            left_panel,
            ("order_id", "customer", "email", "date", "total", "email_sent"),
            [
                ("order_id", "Order ID", 90),
                ("customer", "Customer", 170),
                ("email", "Email", 220),
                ("date", "Date", 170),
                ("total", "Total", 120),
                ("email_sent", "Email Sent", 100),
            ],
            fill_parent=True,
        )
        attach_sorting(
            self.orders_tree,
            {"order_id": "int", "date": "date", "total": "float", "email_sent": "bool_text"},
        )
        self.orders_tree.bind("<<TreeviewSelect>>", self._on_order_select)

        detail_header = ttk.LabelFrame(right_panel, text="Order Details", padding=14)
        detail_header.pack(fill="x")
        self.order_detail_vars = {
            "order_id": tk.StringVar(value="-"),
            "customer": tk.StringVar(value="-"),
            "email": tk.StringVar(value="-"),
            "date": tk.StringVar(value="-"),
            "total": tk.StringVar(value="-"),
            "status": tk.StringVar(value="-"),
        }
        for label_text, key in [
            ("Order ID", "order_id"),
            ("Customer", "customer"),
            ("Email", "email"),
            ("Date", "date"),
            ("Total", "total"),
            ("Email Sent", "status"),
        ]:
            row = ttk.Frame(detail_header, style="App.TFrame")
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=f"{label_text}:", width=12).pack(side="left")
            ttk.Label(row, textvariable=self.order_detail_vars[key]).pack(side="left")

        items_frame = ttk.LabelFrame(right_panel, text="Ordered Products", padding=14)
        items_frame.pack(fill="both", expand=True, pady=(12, 0))
        self.order_items_tree = self._build_tree(
            items_frame,
            ("product", "qty", "price", "subtotal"),
            [
                ("product", "Product", 240),
                ("qty", "Qty", 70),
                ("price", "Unit Price", 120),
                ("subtotal", "Subtotal", 120),
            ],
            fill_parent=True,
        )
        attach_sorting(self.order_items_tree, {"qty": "int", "price": "float", "subtotal": "float"})
        self._build_order_item_scroll_buttons(items_frame)

    def _build_tree(
        self,
        parent: ttk.Frame,
        columns: tuple[str, ...],
        column_spec: list[tuple[str, str, int]],
        fill_parent: bool = False,
    ) -> ttk.Treeview:
        wrapper = ttk.Frame(parent, style="App.TFrame")
        wrapper.pack(fill="both", expand=fill_parent)
        tree = ttk.Treeview(wrapper, columns=columns, show="headings", height=18)
        for key, label, width in column_spec:
            tree.heading(key, text=label)
            tree.column(key, width=width, minwidth=width, anchor="w", stretch=False)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")
        return tree

    def _build_order_item_scroll_buttons(self, parent: ttk.LabelFrame) -> None:
        self.order_items_prev_button = ttk.Button(
            parent,
            text="<",
            width=2,
            style="Ghost.TButton",
            takefocus=False,
            command=lambda: self._animate_order_items_scroll(-1),
        )
        self.order_items_next_button = ttk.Button(
            parent,
            text=">",
            width=2,
            style="Ghost.TButton",
            takefocus=False,
            command=lambda: self._animate_order_items_scroll(1),
        )
        self._hide_order_item_buttons()

        for widget in (parent, self.order_items_tree):
            widget.bind("<Leave>", self._hide_order_item_buttons, add="+")
            widget.bind("<Motion>", self._update_order_item_buttons, add="+")
        for button in (self.order_items_prev_button, self.order_items_next_button):
            button.bind("<Enter>", self._show_both_order_item_buttons, add="+")
            button.bind("<Leave>", self._hide_order_item_buttons, add="+")

    def _show_both_order_item_buttons(self, _event=None) -> None:
        self.order_items_prev_button.place(relx=0.02, rely=0.5, anchor="w")
        self.order_items_next_button.place(relx=0.98, rely=0.5, anchor="e")

    def _update_order_item_buttons(self, event) -> None:
        width = max(event.widget.winfo_width(), 1)
        threshold = 48
        if event.x <= threshold:
            self.order_items_prev_button.place(relx=0.02, rely=0.5, anchor="w")
            self.order_items_next_button.place_forget()
        elif event.x >= width - threshold:
            self.order_items_next_button.place(relx=0.98, rely=0.5, anchor="e")
            self.order_items_prev_button.place_forget()
        else:
            self._hide_order_item_buttons()

    def _hide_order_item_buttons(self, _event=None) -> None:
        self.order_items_prev_button.place_forget()
        self.order_items_next_button.place_forget()

    def _animate_order_items_scroll(self, direction: int, steps: int = 8) -> None:
        def step(remaining: int) -> None:
            if remaining <= 0:
                return
            self.order_items_tree.xview_scroll(direction, "units")
            self.after(22, lambda: step(remaining - 1))

        step(steps)

    def refresh_reports(self) -> None:
        self.inventory_rows = database.get_inventory_report()
        self.orders_rows = database.get_orders_report()
        self._render_inventory_rows()
        self._render_orders_rows()

    def _render_inventory_rows(self) -> None:
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        query = self.inventory_search_var.get().strip().lower()
        for row in self.inventory_rows:
            haystack = " ".join(str(value).lower() for value in row)
            if query and query not in haystack:
                continue
            self.inventory_tree.insert(
                "",
                "end",
                values=(row[0], row[1], f"PHP {row[2]:,.2f}", row[3], row[4]),
            )

    def _render_orders_rows(self) -> None:
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        query = self.orders_search_var.get().strip().lower()
        for row in self.orders_rows:
            haystack = " ".join(str(value).lower() for value in row)
            if query and query not in haystack:
                continue
            self.orders_tree.insert(
                "",
                "end",
                values=(row[0], row[1], row[2], row[3], f"PHP {row[4]:,.2f}", row[5]),
            )

        if self.orders_tree.get_children():
            first_item = self.orders_tree.get_children()[0]
            self.orders_tree.selection_set(first_item)
            self._on_order_select()
        else:
            self._clear_order_details()

    def _on_order_select(self, _event=None) -> None:
        selection = self.orders_tree.selection()
        if not selection:
            self._clear_order_details()
            return

        values = self.orders_tree.item(selection[0], "values")
        order_id = int(values[0])
        self.order_detail_vars["order_id"].set(str(order_id))
        self.order_detail_vars["customer"].set(values[1])
        self.order_detail_vars["email"].set(values[2])
        self.order_detail_vars["date"].set(values[3])
        self.order_detail_vars["total"].set(values[4])
        self.order_detail_vars["status"].set(values[5])

        for item in self.order_items_tree.get_children():
            self.order_items_tree.delete(item)

        for row in database.get_order_items(order_id):
            self.order_items_tree.insert(
                "",
                "end",
                values=(row[0], row[1], f"PHP {row[2]:,.2f}", f"PHP {row[3]:,.2f}"),
            )

    def _clear_order_details(self) -> None:
        for variable in self.order_detail_vars.values():
            variable.set("-")
        for item in self.order_items_tree.get_children():
            self.order_items_tree.delete(item)

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
