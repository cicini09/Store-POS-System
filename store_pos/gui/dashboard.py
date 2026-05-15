"""Main application window and dashboard view."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import database
from ..config import APP_GEOMETRY, APP_TITLE, LOW_STOCK_THRESHOLD, STORE_NAME
from .data_table import ModernDataTable, TableColumn
from .orders import OrdersView
from .products import ProductsView
from .reports import ReportsView


SURFACE = "#FDFDFD"
CARD = "#FFFFFF"
ACCENT = "#DBEAFE"
ACCENT_STRONG = "#60A5FA"
TEXT = "#0F172A"
MUTED = "#64748B"
BORDER = "#E2E8F0"
SIDEBAR = "#111827"
SIDEBAR_MUTED = "#9CA3AF"
SIDEBAR_ACTIVE = "#2563EB"
SIDEBAR_HOVER = "#1F2937"


NAVIGATION_ITEMS = [
    ("Dashboard", "Overview and stock health"),
    ("Products", "Manage inventory"),
    ("New Order", "Create customer sales"),
    ("Reports", "Export and review"),
]


class DashboardView(ttk.Frame):
    """Landing dashboard with quick stats and analytics."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=16, style="App.TFrame")
        self.cards: dict[str, tk.StringVar] = {}
        self.best_seller_var = tk.StringVar(value="Top seller: No sales yet")

        ttk.Label(
            self,
            text="Store Overview",
            font=("Segoe UI Semibold", 18),
            style="App.Title.TLabel",
        ).pack(anchor="w", pady=(0, 16))

        card_grid = ttk.Frame(self, style="App.TFrame")
        card_grid.pack(fill="x")

        card_config = [
            ("total_products", "Total Products", "#EFF6FF"),
            ("total_orders", "Total Orders", "#F0FDF4"),
            ("low_stock_count", f"Low Stock (<= {LOW_STOCK_THRESHOLD})", "#FFF7ED"),
            ("total_revenue", "Total Revenue", "#F8FAFC"),
        ]

        for index, (key, title, background) in enumerate(card_config):
            card = tk.Frame(
                card_grid,
                bg=background,
                bd=0,
                highlightthickness=1,
                highlightbackground=BORDER,
                padx=18,
                pady=18,
            )
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 10, 0))
            card_grid.columnconfigure(index, weight=1)
            label_style = {"bg": background, "anchor": "w", "fg": MUTED}
            tk.Label(card, text=title, font=("Segoe UI Semibold", 10), **label_style).pack(anchor="w")
            value_var = tk.StringVar(value="0")
            tk.Label(
                card,
                textvariable=value_var,
                font=("Segoe UI Semibold", 22),
                bg=background,
                fg=TEXT,
                anchor="w",
            ).pack(anchor="w", pady=(8, 0))
            self.cards[key] = value_var

        ttk.Label(
            self,
            text="Track sales, spot low stock items, and jump into products, orders, and reports from the side menu.",
            style="App.Subtle.TLabel",
        ).pack(anchor="w", pady=(24, 0))

        insights = ttk.Frame(self, style="App.TFrame")
        insights.pack(fill="both", expand=True, pady=(18, 0))
        insights.columnconfigure(0, weight=3)
        insights.columnconfigure(1, weight=2)
        insights.rowconfigure(0, weight=1)

        chart_frame = ttk.LabelFrame(insights, text="Sales Snapshot", padding=14, style="App.TLabelframe")
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ttk.Label(chart_frame, textvariable=self.best_seller_var, style="App.Subtle.TLabel").pack(anchor="w")
        self.chart_canvas = tk.Canvas(chart_frame, height=280, bg=CARD, highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True, pady=(10, 0))

        low_stock_frame = ttk.LabelFrame(
            insights,
            text=f"Low Stock Items (<= {LOW_STOCK_THRESHOLD})",
            padding=14,
            style="App.TLabelframe",
        )
        low_stock_frame.grid(row=0, column=1, sticky="nsew")
        self.low_stock_table = ModernDataTable(
            low_stock_frame,
            [
                TableColumn("name", "Product", 190, frozen=True, can_hide=False),
                TableColumn("category", "Category", 130),
                TableColumn("stock", "Stock", 90, sort_type="int"),
            ],
            height=10,
            empty_message="No low stock items",
            selectmode="browse",
        )
        self.low_stock_table.pack(fill="both", expand=True)

        self.refresh_stats()

    def refresh_stats(self) -> None:
        stats = database.get_dashboard_stats()
        self.cards["total_products"].set(str(stats["total_products"]))
        self.cards["total_orders"].set(str(stats["total_orders"]))
        self.cards["low_stock_count"].set(str(stats["low_stock_count"]))
        self.cards["total_revenue"].set(f"PHP {stats['total_revenue']:,.2f}")
        self._refresh_chart()
        self._refresh_low_stock_list()

    def _refresh_chart(self) -> None:
        top_sellers = database.get_top_selling_products()
        self.chart_canvas.delete("all")
        self.chart_canvas.update_idletasks()

        canvas_width = max(self.chart_canvas.winfo_width(), 520)
        canvas_height = max(self.chart_canvas.winfo_height(), 280)
        if not top_sellers or top_sellers[0][1] <= 0:
            self.best_seller_var.set("Top seller: No completed sales yet")
            self.chart_canvas.create_text(
                canvas_width / 2,
                canvas_height / 2,
                text="No sales data available yet",
                fill=MUTED,
                font=("Segoe UI", 11),
            )
            return

        top_name, top_units = top_sellers[0]
        self.best_seller_var.set(f"Top seller: {top_name} ({top_units} units sold)")

        left_margin = 60
        right_margin = 20
        top_margin = 30
        bottom_margin = 70
        chart_height = canvas_height - top_margin - bottom_margin
        chart_width = canvas_width - left_margin - right_margin
        max_units = max(int(units) for _, units in top_sellers) or 1
        bar_width = max(60, int(chart_width / max(len(top_sellers), 1)) - 20)
        gap = max(18, int((chart_width - (bar_width * len(top_sellers))) / max(len(top_sellers), 1)))

        self.chart_canvas.create_line(left_margin, top_margin, left_margin, top_margin + chart_height, fill=BORDER)
        self.chart_canvas.create_line(
            left_margin,
            top_margin + chart_height,
            left_margin + chart_width,
            top_margin + chart_height,
            fill=BORDER,
        )

        for tick in range(0, 5):
            tick_value = round(max_units * (4 - tick) / 4)
            y_pos = top_margin + (chart_height * tick / 4)
            self.chart_canvas.create_line(left_margin - 6, y_pos, left_margin + chart_width, y_pos, fill="#EEF2F7")
            self.chart_canvas.create_text(left_margin - 12, y_pos, text=str(tick_value), anchor="e", fill=MUTED)

        for index, (name, units) in enumerate(top_sellers):
            x0 = left_margin + gap + index * (bar_width + gap)
            x1 = x0 + bar_width
            bar_height = 0 if max_units == 0 else (int(units) / max_units) * chart_height
            y0 = top_margin + chart_height - bar_height
            y1 = top_margin + chart_height
            color = "#2563EB" if index == 0 else ACCENT_STRONG
            self.chart_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            self.chart_canvas.create_text((x0 + x1) / 2, y0 - 12, text=str(int(units)), fill=TEXT)
            self.chart_canvas.create_text(
                (x0 + x1) / 2,
                y1 + 18,
                text=_shorten_label(name, 16),
                width=bar_width + 10,
                fill=TEXT,
            )

    def _refresh_low_stock_list(self) -> None:
        low_stock_items = database.get_low_stock_products()
        rows = [
            {"name": name, "category": category, "stock": stock}
            for name, category, stock in low_stock_items
        ]
        self.low_stock_table.set_rows(rows)


class MainApplication(tk.Tk):
    """Tk root window for the POS system."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        self.minsize(1100, 680)
        self.configure(bg=SURFACE)
        self._open_maximized()

        self._configure_style()
        self._disable_double_click_focus()

        container = ttk.Frame(self, padding=0, style="App.TFrame")
        container.pack(fill="both", expand=True)

        self.navigation_buttons: list[tk.Button] = []
        self._build_sidebar(container)

        content_panel = ttk.Frame(container, padding=14, style="App.TFrame")
        content_panel.pack(side="left", fill="both", expand=True)

        self.notebook = ttk.Notebook(content_panel, style="Main.TNotebook", takefocus=False)
        self.notebook.pack(fill="both", expand=True)

        self.dashboard_view = DashboardView(self.notebook)
        self.products_view = ProductsView(self.notebook, self)
        self.orders_view = OrdersView(self.notebook, self)
        self.reports_view = ReportsView(self.notebook, self)

        self.notebook.add(self.dashboard_view, text="Dashboard")
        self.notebook.add(self.products_view, text="Products")
        self.notebook.add(self.orders_view, text="New Order")
        self.notebook.add(self.reports_view, text="Reports")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_page_changed)
        self._update_navigation_state(0)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel", anchor="w").pack(fill="x", padx=12, pady=(0, 12))

    def show_main(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        self.set_status("Login successful. Welcome back.")

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def refresh_all(self) -> None:
        self.dashboard_view.refresh_stats()
        self.products_view.load_products()
        self.orders_view.refresh_products()
        self.reports_view.refresh_reports()

    def _build_sidebar(self, parent: tk.Misc) -> None:
        sidebar = tk.Frame(parent, bg=SIDEBAR, width=260, padx=18, pady=20)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text=APP_TITLE,
            bg=SIDEBAR,
            fg="#F9FAFB",
            font=("Segoe UI Semibold", 17),
            anchor="w",
            justify="left",
            wraplength=210,
        ).pack(fill="x", anchor="w")
        tk.Label(
            sidebar,
            text=f"{STORE_NAME} control center",
            bg=SIDEBAR,
            fg=SIDEBAR_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", anchor="w", pady=(6, 26))

        for page_index, (label, description) in enumerate(NAVIGATION_ITEMS):
            button_text = f"{label}\n{description}"
            nav_button = tk.Button(
                sidebar,
                text=button_text,
                command=lambda index=page_index: self.show_page(index),
                bg=SIDEBAR,
                fg=SIDEBAR_MUTED,
                activebackground=SIDEBAR_HOVER,
                activeforeground="#F9FAFB",
                bd=0,
                relief="flat",
                cursor="hand2",
                anchor="w",
                justify="left",
                padx=14,
                pady=12,
                font=("Segoe UI", 10),
                takefocus=False,
            )
            nav_button.pack(fill="x", pady=3)
            nav_button.bind("<Enter>", lambda event, index=page_index: self._on_navigation_hover(event, index))
            nav_button.bind("<Leave>", lambda event, index=page_index: self._on_navigation_leave(event, index))
            self.navigation_buttons.append(nav_button)

        tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Label(
            sidebar,
            text="Ready for sales, stock checks, and end-of-day reports.",
            bg=SIDEBAR,
            fg=SIDEBAR_MUTED,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=210,
        ).pack(fill="x", anchor="w")

    def show_page(self, page_index: int) -> None:
        self.notebook.select(page_index)
        self._update_navigation_state(page_index)

    def _on_page_changed(self, _event: tk.Event) -> None:
        selected_tab_id = self.notebook.select()
        if not selected_tab_id:
            return
        page_index = self.notebook.index(selected_tab_id)
        self._update_navigation_state(page_index)

    def _on_navigation_hover(self, event: tk.Event, page_index: int) -> None:
        if self.notebook.index(self.notebook.select()) != page_index:
            event.widget.configure(bg=SIDEBAR_HOVER, fg="#F9FAFB")

    def _on_navigation_leave(self, event: tk.Event, page_index: int) -> None:
        if self.notebook.index(self.notebook.select()) != page_index:
            event.widget.configure(bg=SIDEBAR, fg=SIDEBAR_MUTED)

    def _update_navigation_state(self, selected_index: int) -> None:
        for index, button in enumerate(self.navigation_buttons):
            if index == selected_index:
                button.configure(
                    bg=SIDEBAR_ACTIVE,
                    fg="#FFFFFF",
                    activebackground=SIDEBAR_ACTIVE,
                    activeforeground="#FFFFFF",
                    font=("Segoe UI Semibold", 10),
                )
            else:
                button.configure(
                    bg=SIDEBAR,
                    fg=SIDEBAR_MUTED,
                    activebackground=SIDEBAR_HOVER,
                    activeforeground="#F9FAFB",
                    font=("Segoe UI", 10),
                )

    def _open_maximized(self) -> None:
        try:
            self.state("zoomed")
            return
        except tk.TclError:
            pass

        try:
            self.attributes("-zoomed", True)
            return
        except tk.TclError:
            pass

        try:
            self.attributes("-fullscreen", True)
        except tk.TclError:
            pass

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            style.theme_use("clam")

        style.configure(".", background=SURFACE, foreground=TEXT, fieldbackground=CARD)
        style.configure("App.TFrame", background=SURFACE)
        style.configure("TLabel", background=SURFACE, foreground=TEXT)
        style.configure("App.Title.TLabel", background=SURFACE, foreground=TEXT)
        style.configure("App.Subtle.TLabel", background=SURFACE, foreground=MUTED)
        style.configure("Status.TLabel", background=CARD, foreground=MUTED, padding=(12, 10))
        style.configure("TLabelframe", background=SURFACE, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=SURFACE, foreground=TEXT)
        style.configure("App.TLabelframe", background=SURFACE, borderwidth=1, relief="solid")
        style.configure("App.TLabelframe.Label", background=SURFACE, foreground=TEXT)
        style.configure("TEntry", fieldbackground=CARD, foreground=TEXT, borderwidth=1, padding=8)
        style.configure("TCombobox", fieldbackground=CARD, foreground=TEXT, borderwidth=1, padding=6)
        style.configure(
            "TButton",
            background=CARD,
            foreground=TEXT,
            borderwidth=1,
            focusthickness=0,
            focuscolor=SURFACE,
            padding=(14, 9),
            relief="solid",
        )
        style.map(
            "TButton",
            background=[("pressed", ACCENT), ("active", "#EFF6FF")],
            foreground=[("pressed", TEXT), ("active", TEXT)],
            bordercolor=[("active", ACCENT_STRONG), ("!active", BORDER)],
            lightcolor=[("active", CARD), ("!active", CARD)],
            darkcolor=[("active", CARD), ("!active", CARD)],
            focuscolor=[("focus", SURFACE), ("!focus", SURFACE)],
        )
        style.configure(
            "Ghost.TButton",
            background="#F8FAFC",
            foreground=TEXT,
            borderwidth=1,
            focusthickness=0,
            focuscolor=SURFACE,
            padding=(8, 8),
            relief="solid",
        )
        style.map(
            "Ghost.TButton",
            background=[("pressed", ACCENT), ("active", "#EFF6FF")],
            foreground=[("pressed", TEXT), ("active", TEXT)],
            bordercolor=[("active", ACCENT_STRONG), ("!active", BORDER)],
            lightcolor=[("active", CARD), ("!active", CARD)],
            darkcolor=[("active", CARD), ("!active", CARD)],
        )
        style.configure(
            "Ghost.TMenubutton",
            background="#F8FAFC",
            foreground=TEXT,
            borderwidth=1,
            focusthickness=0,
            focuscolor=SURFACE,
            padding=(12, 8),
            relief="solid",
        )
        style.map(
            "Ghost.TMenubutton",
            background=[("pressed", ACCENT), ("active", "#EFF6FF")],
            foreground=[("pressed", TEXT), ("active", TEXT)],
            bordercolor=[("active", ACCENT_STRONG), ("!active", BORDER)],
            lightcolor=[("active", CARD), ("!active", CARD)],
            darkcolor=[("active", CARD), ("!active", CARD)],
        )
        style.configure(
            "Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            rowheight=32,
            borderwidth=1,
            relief="solid",
        )
        style.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", TEXT)])
        style.configure("Treeview.Heading", background="#EEF6FF", foreground="black", relief="raised", padding=(12, 10))
        style.map("Treeview.Heading", background=[("active", "#E0F2FE")], foreground=[("active", TEXT)])
        style.configure(
            "DataTable.Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            rowheight=42,
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 10),
        )
        style.map("DataTable.Treeview", background=[("selected", "#DCEBFF")], foreground=[("selected", TEXT)])
        style.configure(
            "DataTable.Treeview.Heading",
            background="#EEF2F7",
            foreground=TEXT,
            relief="flat",
            padding=(14, 13),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "DataTable.Treeview.Heading",
            background=[("active", "#EEF6FF")],
            foreground=[("active", TEXT)],
        )
        style.configure("Table.Empty.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("App.TNotebook", background=SURFACE, borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure(
            "App.TNotebook.Tab",
            background="#F8FAFC",
            foreground=MUTED,
            padding=(18, 12),
            borderwidth=0,
            focuscolor=SURFACE,
        )
        style.map(
            "App.TNotebook.Tab",
            background=[("selected", ACCENT), ("active", "#EFF6FF")],
            foreground=[("selected", TEXT), ("active", TEXT)],
            expand=[("selected", (0, 0, 0, 0)), ("!selected", (0, 0, 0, 0))],
            padding=[("selected", (18, 12)), ("!selected", (18, 12))],
            focuscolor=[("focus", SURFACE), ("!focus", SURFACE)],
        )
        style.layout("App.TNotebook", style.layout("TNotebook"))
        style.layout("App.TNotebook.Tab", style.layout("TNotebook.Tab"))
        style.configure("Main.TNotebook", background=SURFACE, borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.layout("Main.TNotebook", style.layout("TNotebook"))
        style.layout("Main.TNotebook.Tab", [])

    def _disable_double_click_focus(self) -> None:
        self.bind_class("TButton", "<Double-Button-1>", lambda _event: "break")
        self.bind_class("TNotebook", "<Double-Button-1>", lambda _event: "break")


def _shorten_label(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."
