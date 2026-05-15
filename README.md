# Store Inventory and POS System

A desktop final project for a small electronics store named ElectroHub. The system was built with Python, Tkinter, SQLite, ReportLab, and standard-library email tools to handle product management, customer orders, automatic stock deduction, dashboard monitoring, PDF report generation, and receipt processing.

## Core Features

- login screen before entering the main system
- dashboard with product, order, revenue, and low-stock summaries
- product add, edit, delete, and search workflow
- customer order processing with cart-based line items
- automatic stock deduction after each completed sale
- inventory and orders reports with PDF export
- receipt processing with email and logging support

## Tech Stack

- Python 3
- Tkinter and ttk
- SQLite via `sqlite3`
- ReportLab
- `smtplib`, `ssl`, and `email.message`

## Project Structure

- `store_pos/main.py` - application entry point
- `store_pos/config.py` - shared configuration values
- `store_pos/database.py` - database schema and SQL helpers
- `store_pos/models.py` - dataclasses for Product, Customer, Order, and OrderItem
- `store_pos/gui/` - login, dashboard, products, orders, and reports views
- `store_pos/utils/` - validators, email sender, and PDF report helpers
- `docs/` - project documentation, database notes, sample problems, and user guide

## Setup

1. Install dependencies:
   `pip install reportlab`
2. Start the app:
   `python -m store_pos.main`

## Demo Login

- Username: `admin`
- Password: `admin123`

## Documentation

The project documentation pack is organized in the `docs/` folder:

- [Project Documentation](docs/PROJECT_DOCUMENTATION.md)
- [Sample Problems](docs/SAMPLE_PROBLEMS.md)
- [Database Design](docs/DATABASE_DESIGN.md)
- [User Guide](docs/USER_GUIDE.md)
- [Rubric Evidence Guide](docs/RUBRIC_EVIDENCE.md)

## Email Notes

- Email receipts use the SMTP path when configuration is available.
- Set `STORE_POS_SMTP_USERNAME` and `STORE_POS_SMTP_PASSWORD` in your environment.
- Optional overrides: `STORE_POS_SMTP_HOST`, `STORE_POS_SMTP_PORT`, `STORE_POS_SMTP_USE_SSL`, `STORE_POS_SMTP_FROM_NAME`.
- Delivery attempts and failures are logged to `store_pos/reports/email_receipts.log`.

## Demo Flow

1. Log in with the demo admin account.
2. Review the dashboard summary cards.
3. Add or edit products in the Products tab.
4. Create a multi-item customer order in New Order.
5. Verify stock deduction and receipt status.
6. Export inventory and orders reports to PDF from the Reports tab.
