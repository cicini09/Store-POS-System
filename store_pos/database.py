"""Database initialization and SQL helpers for the POS system."""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable

from .config import DB_PATH, LOGIN_PASSWORD_HASH, LOGIN_USERNAME, LOW_STOCK_THRESHOLD, REPORTS_DIR
from .models import Product


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with foreign keys and row access enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create required tables and ensure runtime folders exist."""
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    with closing(get_connection()) as conn, conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                price REAL NOT NULL CHECK(price >= 0),
                stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
                category TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                total_amount REAL NOT NULL CHECK(total_amount >= 0),
                email_sent INTEGER NOT NULL DEFAULT 0 CHECK(email_sent IN (0, 1)),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
            """
        )

        conn.execute(
            """
            INSERT INTO users (username, password)
            VALUES (?, ?)
            ON CONFLICT(username) DO NOTHING
            """,
            (LOGIN_USERNAME, LOGIN_PASSWORD_HASH),
        )


def hash_password(password: str) -> str:
    """Return a SHA-256 hash for the given password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def validate_login(username: str, password: str) -> bool:
    """Validate login credentials against the users table."""
    password_hash = hash_password(password)
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT 1 FROM users WHERE username = ? AND password = ?",
            (username.strip(), password_hash),
        )
        return cursor.fetchone() is not None


def get_all_products(search_text: str = "") -> list[Product]:
    """Return products filtered by name or category."""
    query = """
        SELECT id, name, description, price, stock_quantity, category, created_at
        FROM products
    """
    params: list[str] = []
    if search_text.strip():
        query += " WHERE name LIKE ? OR category LIKE ?"
        like = f"%{search_text.strip()}%"
        params.extend([like, like])
    query += " ORDER BY name COLLATE NOCASE"

    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    return [Product(**dict(row)) for row in rows]


def get_product_by_id(product_id: int) -> sqlite3.Row | None:
    """Return a product row for the provided identifier."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return cursor.fetchone()


def add_product(
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
) -> int:
    """Insert a new product and return its ID."""
    with closing(get_connection()) as conn, conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            INSERT INTO products (name, description, price, stock_quantity, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name.strip(), description.strip(), round(price, 2), stock_quantity, category.strip()),
        )
        return int(cursor.lastrowid)


def update_product(
    product_id: int,
    name: str,
    description: str,
    price: float,
    stock_quantity: int,
    category: str,
) -> None:
    """Update an existing product."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            """
            UPDATE products
            SET name = ?, description = ?, price = ?, stock_quantity = ?, category = ?
            WHERE id = ?
            """,
            (
                name.strip(),
                description.strip(),
                round(price, 2),
                stock_quantity,
                category.strip(),
                product_id,
            ),
        )


def delete_product(product_id: int) -> None:
    """Delete a product by ID."""
    with closing(get_connection()) as conn, conn:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


def get_or_create_customer(name: str, email: str, phone: str) -> int:
    """Return an existing customer ID or create the customer if missing."""
    normalized_email = email.strip().lower()
    with closing(get_connection()) as conn, conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT id FROM customers WHERE email = ?", (normalized_email,))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "UPDATE customers SET name = ?, phone = ? WHERE id = ?",
                (name.strip(), phone.strip(), row["id"]),
            )
            return int(row["id"])

        cursor.execute(
            """
            INSERT INTO customers (name, email, phone)
            VALUES (?, ?, ?)
            """,
            (name.strip(), normalized_email, phone.strip()),
        )
        return int(cursor.lastrowid)


def save_order(
    customer_id: int,
    items: Iterable[dict[str, int | float]],
    email_sent: int = 0,
) -> int:
    """Save an order, its items, and deduct inventory within one transaction."""
    item_list = list(items)
    if not item_list:
        raise ValueError("Order must contain at least one item.")

    with closing(get_connection()) as conn:
        try:
            conn.execute("BEGIN")
            total_amount = 0.0

            for item in item_list:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
                cursor = conn.execute(
                    "SELECT name, price, stock_quantity FROM products WHERE id = ?",
                    (product_id,),
                )
                product = cursor.fetchone()
                if product is None:
                    raise ValueError(f"Product ID {product_id} no longer exists.")
                if quantity <= 0:
                    raise ValueError(f"Quantity for {product['name']} must be greater than zero.")
                if quantity > int(product["stock_quantity"]):
                    raise ValueError(f"Insufficient stock for {product['name']}.")

                total_amount += round(float(product["price"]) * quantity, 2)

            order_cursor = conn.execute(
                """
                INSERT INTO orders (customer_id, total_amount, email_sent)
                VALUES (?, ?, ?)
                """,
                (customer_id, round(total_amount, 2), email_sent),
            )
            order_id = int(order_cursor.lastrowid)

            for item in item_list:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
                product = conn.execute(
                    "SELECT price FROM products WHERE id = ?",
                    (product_id,),
                ).fetchone()
                unit_price = round(float(product["price"]), 2)

                conn.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, product_id, quantity, unit_price),
                )
                conn.execute(
                    """
                    UPDATE products
                    SET stock_quantity = stock_quantity - ?
                    WHERE id = ?
                    """,
                    (quantity, product_id),
                )

            conn.commit()
            return order_id
        except Exception:
            conn.rollback()
            raise


def set_order_email_status(order_id: int, sent: bool) -> None:
    """Persist the final email status for an order."""
    with closing(get_connection()) as conn, conn:
        conn.execute(
            "UPDATE orders SET email_sent = ? WHERE id = ?",
            (1 if sent else 0, order_id),
        )


def get_order_receipt_data(order_id: int) -> dict:
    """Return order details formatted for email receipts."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT
                o.id,
                o.created_at,
                o.total_amount,
                c.name AS customer_name,
                c.email AS customer_email,
                c.phone AS customer_phone
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = ?
            """,
            (order_id,),
        )
        order_row = cursor.fetchone()
        if order_row is None:
            raise ValueError("Order not found.")

        cursor.execute(
            """
            SELECT
                p.name AS product_name,
                oi.quantity,
                oi.unit_price,
                ROUND(oi.quantity * oi.unit_price, 2) AS subtotal
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY p.name COLLATE NOCASE
            """,
            (order_id,),
        )
        item_rows = cursor.fetchall()

    return {
        "order_id": order_row["id"],
        "created_at": order_row["created_at"],
        "total_amount": round(float(order_row["total_amount"]), 2),
        "customer_name": order_row["customer_name"],
        "customer_email": order_row["customer_email"],
        "customer_phone": order_row["customer_phone"] or "",
        "items": [dict(row) for row in item_rows],
    }


def get_order_items(order_id: int) -> list[tuple]:
    """Return item-level details for a specific order."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT
                p.name,
                oi.quantity,
                ROUND(oi.unit_price, 2),
                ROUND(oi.quantity * oi.unit_price, 2)
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY p.name COLLATE NOCASE
            """,
            (order_id,),
        )
        return [tuple(row) for row in cursor.fetchall()]


def get_dashboard_stats() -> dict[str, float | int]:
    """Return summary values for the dashboard cards."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = int(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = int(cursor.fetchone()[0])

        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE stock_quantity <= ?",
            (LOW_STOCK_THRESHOLD,),
        )
        low_stock_count = int(cursor.fetchone()[0])

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders")
        total_revenue = round(float(cursor.fetchone()[0]), 2)

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "low_stock_count": low_stock_count,
        "total_revenue": total_revenue,
    }


def get_top_selling_products(limit: int = 5) -> list[tuple]:
    """Return the most sold products and their order quantities."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT
                p.name,
                COALESCE(SUM(oi.quantity), 0) AS units_sold
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            GROUP BY p.id, p.name
            ORDER BY units_sold DESC, p.name COLLATE NOCASE
            LIMIT ?
            """,
            (limit,),
        )
        return [tuple(row) for row in cursor.fetchall()]


def get_low_stock_products(limit: int = 8) -> list[tuple]:
    """Return products at or below the configured low-stock threshold."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT name, COALESCE(category, ''), stock_quantity
            FROM products
            WHERE stock_quantity <= ?
            ORDER BY stock_quantity ASC, name COLLATE NOCASE
            LIMIT ?
            """,
            (LOW_STOCK_THRESHOLD, limit),
        )
        return [tuple(row) for row in cursor.fetchall()]


def get_inventory_report() -> list[tuple]:
    """Return product inventory totals including units sold."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT
                p.name,
                COALESCE(p.category, ''),
                ROUND(p.price, 2),
                p.stock_quantity,
                COALESCE(SUM(oi.quantity), 0) AS units_sold
            FROM products p
            LEFT JOIN order_items oi ON oi.product_id = p.id
            GROUP BY p.id, p.name, p.category, p.price, p.stock_quantity
            ORDER BY p.name COLLATE NOCASE
            """
        )
        return [tuple(row) for row in cursor.fetchall()]


def get_orders_report() -> list[tuple]:
    """Return orders with customer and item summary information."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            SELECT
                o.id,
                c.name,
                c.email,
                o.created_at,
                ROUND(o.total_amount, 2),
                CASE WHEN o.email_sent = 1 THEN 'Yes' ELSE 'No' END AS email_sent
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            ORDER BY datetime(o.created_at) DESC, o.id DESC
            """
        )
        return [tuple(row) for row in cursor.fetchall()]


def seed_demo_data() -> None:
    """Populate the database with electronics demo data once."""
    products = [
        ("Laptop Pro 14", "14-inch laptop with 16GB RAM", 64999.00, 12, "Computers"),
        ("Wireless Mouse", "Ergonomic Bluetooth mouse", 899.00, 40, "Accessories"),
        ("Mechanical Keyboard", "RGB backlit keyboard", 2499.00, 18, "Accessories"),
        ("27-inch Monitor", "Full HD IPS display", 9999.00, 10, "Displays"),
        ("USB-C Hub", "6-in-1 multiport adapter", 1599.00, 25, "Accessories"),
        ("Noise Cancelling Headphones", "Over-ear wireless headphones", 5499.00, 14, "Audio"),
        ("Portable SSD 1TB", "High-speed external storage", 4299.00, 16, "Storage"),
        ("Gaming Chair", "Lumbar support with recline", 7999.00, 8, "Furniture"),
        ("1080p Webcam", "Auto-focus video webcam", 1899.00, 20, "Cameras"),
        ("Smartphone Stand", "Adjustable aluminum stand", 499.00, 35, "Accessories"),
    ]
    customers = [
        ("Mia Santos", "mia.santos@example.com", "09171234567"),
        ("Noah Reyes", "noah.reyes@example.com", "09179876543"),
        ("Ava Cruz", "ava.cruz@example.com", "09175550123"),
    ]
    seeded_orders = [
        {
            "email": "mia.santos@example.com",
            "items": [
                {"product_name": "Laptop Pro 14", "quantity": 1},
                {"product_name": "Wireless Mouse", "quantity": 1},
            ],
        },
        {
            "email": "noah.reyes@example.com",
            "items": [
                {"product_name": "27-inch Monitor", "quantity": 2},
                {"product_name": "USB-C Hub", "quantity": 2},
            ],
        },
        {
            "email": "ava.cruz@example.com",
            "items": [
                {"product_name": "Noise Cancelling Headphones", "quantity": 1},
                {"product_name": "Portable SSD 1TB", "quantity": 1},
            ],
        },
        {
            "email": "mia.santos@example.com",
            "items": [
                {"product_name": "1080p Webcam", "quantity": 2},
                {"product_name": "Smartphone Stand", "quantity": 3},
            ],
        },
        {
            "email": "noah.reyes@example.com",
            "items": [
                {"product_name": "Mechanical Keyboard", "quantity": 1},
                {"product_name": "Wireless Mouse", "quantity": 2},
            ],
        },
    ]

    with closing(get_connection()) as conn, conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT COUNT(*) FROM orders")
        if int(cursor.fetchone()[0]) > 0:
            return

        cursor.execute("SELECT COUNT(*) FROM products")
        if int(cursor.fetchone()[0]) == 0:
            cursor.executemany(
                """
                INSERT INTO products (name, description, price, stock_quantity, category)
                VALUES (?, ?, ?, ?, ?)
                """,
                products,
            )

    for customer in customers:
        get_or_create_customer(*customer)

    product_map = {product.name: product.id for product in get_all_products()}
    customer_map = {
        row["email"]: row["id"]
        for row in _fetch_rows("SELECT id, email FROM customers")
    }

    for index, seeded_order in enumerate(seeded_orders, start=1):
        items = [
            {"product_id": product_map[item["product_name"]], "quantity": item["quantity"]}
            for item in seeded_order["items"]
        ]
        save_order(customer_map[seeded_order["email"]], items, email_sent=1 if index % 2 else 0)


def _fetch_rows(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Run a query and return all rows."""
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("Database initialized and demo data seeded.")
    print(get_dashboard_stats())
