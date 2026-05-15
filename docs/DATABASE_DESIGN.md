# Database Design Documentation

## Overview

The system uses SQLite as its relational database. The database file is stored at:

- `store_pos/inventory.db`

The schema is created in:

- `store_pos/database.py`

## Design Goals

- keep product and order records structured
- maintain referential integrity between tables
- prevent invalid numeric values
- support reporting and dashboard summaries
- preserve order history

## Tables

### 1. `products`

Stores all inventory items sold by the store.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | primary key |
| `name` | TEXT | product name |
| `description` | TEXT | product description |
| `price` | REAL | selling price |
| `stock_quantity` | INTEGER | quantity currently in stock |
| `category` | TEXT | product category |
| `created_at` | TEXT | creation timestamp |

### 2. `customers`

Stores customer details used during order processing.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | primary key |
| `name` | TEXT | customer name |
| `email` | TEXT | customer email, unique |
| `phone` | TEXT | contact number |
| `created_at` | TEXT | creation timestamp |

### 3. `orders`

Stores each submitted sale.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | primary key |
| `customer_id` | INTEGER | foreign key to `customers.id` |
| `total_amount` | REAL | final order total |
| `email_sent` | INTEGER | receipt delivery status |
| `created_at` | TEXT | order timestamp |

### 4. `order_items`

Stores the individual products included in an order.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | primary key |
| `order_id` | INTEGER | foreign key to `orders.id` |
| `product_id` | INTEGER | foreign key to `products.id` |
| `quantity` | INTEGER | ordered quantity |
| `unit_price` | REAL | product price at time of sale |

### 5. `users`

Stores the login credential data used by the application.

| Field | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | primary key |
| `username` | TEXT | login username |
| `password` | TEXT | hashed password |

## Relationships

The database relationships are:

- one customer can have many orders
- one order can have many order items
- one product can appear in many order items

### Relationship Diagram

```text
customers (1) -------- (many) orders
orders (1) ----------- (many) order_items
products (1) --------- (many) order_items
users -> used for login authentication
```

## Integrity Rules

The schema includes several constraints to improve data quality:

- `price >= 0`
- `stock_quantity >= 0`
- `quantity > 0`
- `total_amount >= 0`
- `email_sent IN (0, 1)`
- `customers.email` must be unique
- deleting an order removes its order items through `ON DELETE CASCADE`
- deleting a product referenced by order items is blocked through `ON DELETE RESTRICT`

## Why the Design is Appropriate

This design is appropriate because:

- product records are separated from order transactions
- customer data is reusable across multiple purchases
- order headers and order items are normalized into different tables
- history is preserved because sold products cannot be deleted carelessly
- report queries can be built using joins and aggregates

## Queries Supported by the Design

The database design supports:

- product searching
- product add, edit, and delete
- customer lookup by email
- order saving with multiple items
- stock deduction after sale
- dashboard totals
- top-selling products
- low-stock monitoring
- inventory report generation
- orders report generation

## Notes for Defense

The database is not just storing flat records. It uses relational structure, foreign keys, and validation constraints, which makes it more aligned with real business systems than a single-table design.
