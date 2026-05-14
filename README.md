# Store Inventory & POS System

A desktop Python final project built with Tkinter, SQLite, ReportLab, and standard-library email tools. The app supports product management, customer orders, automatic stock deduction, PDF report exports, and receipt handling with a mock-first email workflow.

## Tech Stack

- Python 3
- Tkinter / ttk
- SQLite via `sqlite3`
- ReportLab
- `smtplib`, `ssl`, and `email.message`

## Project Structure

- `store_pos/main.py` - app entry point
- `store_pos/database.py` - database schema and SQL helpers
- `store_pos/models.py` - dataclasses for Product, Customer, Order, and OrderItem
- `store_pos/gui/` - login, dashboard, products, orders, and reports views
- `store_pos/utils/` - validators, email sender, and PDF report helpers

## Setup

1. Install dependencies:
   `pip install -r requirements.txt`
2. Start the app:
   `python -m store_pos.main`

## Demo Login

- Username: `admin`
- Password: `admin123`

## Email Notes

- Email receipts now use the real SMTP path when credentials are configured.
- Set `STORE_POS_SMTP_USERNAME` and `STORE_POS_SMTP_PASSWORD` in your environment, or replace the placeholders in `store_pos/config.py`.
- Optional overrides: `STORE_POS_SMTP_HOST`, `STORE_POS_SMTP_PORT`, `STORE_POS_SMTP_USE_SSL`, `STORE_POS_SMTP_FROM_NAME`.
- Delivery attempts and failures are logged to `store_pos/reports/email_receipts.log`.

## Demo Flow

1. Log in with the demo admin account.
2. Review dashboard summary cards.
3. Add or edit products in the Products tab.
4. Create a multi-item customer order in New Order.
5. Verify the stock deduction and receipt status.
6. Export inventory and orders reports to PDF from the Reports tab.
