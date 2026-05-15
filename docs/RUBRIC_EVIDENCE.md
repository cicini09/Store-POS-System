# Rubric Evidence Guide

## Purpose

This document maps the system deliverables to the project rubric so the project can be defended with direct evidence.

## Database Design

Evidence:

- relational schema with five tables
- primary keys and foreign keys
- constraints for price, stock, quantity, and email status
- preserved order history through relationship rules

Primary source:

- `store_pos/database.py`

## Data Entry and Test Data

Evidence:

- realistic electronics inventory
- realistic customer records
- realistic multi-item seeded orders

Primary source:

- `store_pos/database.py`

## Form Validations

Evidence:

- required-field validation
- email-format validation
- numeric and quantity validation
- stock-availability checks

Primary source:

- `store_pos/utils/validators.py`
- `store_pos/gui/products.py`
- `store_pos/gui/orders.py`

## User Interface

Evidence:

- branded login page
- dashboard page
- sidebar navigation
- styled tables
- product, order, and report modules
- status messaging and modal dialogs

Primary source:

- `store_pos/gui/login.py`
- `store_pos/gui/dashboard.py`
- `store_pos/gui/products.py`
- `store_pos/gui/orders.py`
- `store_pos/gui/reports.py`

## Tech Stack Utilization

Evidence:

- Python
- Tkinter and ttk
- SQLite
- ReportLab
- SMTP and email tools

Primary source:

- `README.md`
- `store_pos/utils/pdf_reports.py`
- `store_pos/utils/email_sender.py`

## OOP Concepts

Evidence:

- class-based GUI structure
- reusable table component
- dataclasses for business entities
- method-based encapsulation of UI behavior

Primary source:

- `store_pos/models.py`
- `store_pos/gui/`

## Reports

Evidence:

- products report table
- orders report table
- order detail panel
- PDF export

Primary source:

- `store_pos/gui/reports.py`
- `store_pos/utils/pdf_reports.py`

## Documentation and Sample Problems

Evidence:

- project overview and business context
- user guide
- database design document
- sample problems tied to the selected store

Primary source:

- `docs/PROJECT_DOCUMENTATION.md`
- `docs/SAMPLE_PROBLEMS.md`
- `docs/DATABASE_DESIGN.md`
- `docs/USER_GUIDE.md`

## Important Honesty Note

This evidence guide improves documentation quality and defense readiness, but it does not automatically prove timeliness. Timeliness still depends on the actual submission timeline and oral defense performance.
