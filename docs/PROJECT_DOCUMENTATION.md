# Store Inventory and POS System Documentation

## 1. Project Title

Store Inventory and POS System for ElectroHub

## 2. Project Overview

This project is a desktop-based Store Inventory and Point of Sale System developed in Python using Tkinter for the user interface and SQLite for persistent storage. It is designed for a small electronics retail store named ElectroHub. The system helps the store manage product inventory, process customer orders, automatically deduct stock, monitor low-stock products, and generate printable PDF reports.

The project was built as a final course requirement and focuses on applying database design, form validation, object-oriented programming, user interface design, reporting, and documentation in one working business system.

## 3. Business Context

ElectroHub is a sample electronics store that sells products such as laptops, monitors, accessories, storage devices, cameras, and furniture. In a manual setup, the store staff would often face the following problems:

- Product stock counts can become inaccurate after repeated sales.
- Writing invoices or sales records by hand is slow and error-prone.
- It is difficult to know which items are low in stock.
- Reviewing sales history takes time when records are scattered.
- Managers need a quick summary of products, sales, and revenue.

This system addresses those problems by centralizing inventory, customer, order, and reporting workflows into a single desktop application.

## 4. General Objective

To develop a functional desktop Store Inventory and POS System that supports inventory management, customer order processing, stock monitoring, and report generation for a small retail store.

## 5. Specific Objectives

- Record and maintain product information accurately.
- Allow the user to add, edit, search, and delete products.
- Store customer information during order processing.
- Process customer orders with one or more line items.
- Automatically deduct sold quantities from available stock.
- Prevent invalid orders such as empty carts or quantities beyond available stock.
- Show business summaries through a dashboard.
- Generate products and orders reports in PDF format.
- Provide a login screen before accessing the main system.

## 6. Scope of the System

The system currently covers the following scope:

- Login using stored user credentials
- Product management
- Customer capture during sales
- Cart-based order creation
- Automatic inventory deduction
- Order receipt preparation and email sending
- Dashboard statistics and sales snapshot
- Inventory and orders reporting
- PDF export for reports

The system does not currently cover the following:

- Multi-user roles and permissions
- Supplier management
- Purchase order management
- Barcode scanning
- Sales returns and refunds
- Logout and profile management
- Online cloud synchronization

## 7. Target Users

- Store owner
- Cashier
- Inventory staff
- Manager

## 8. Major Features

### 8.1 Login Module

The system starts with a login screen before the user can access the dashboard. This adds a basic access-control layer and creates a more complete application flow.

### 8.2 Dashboard Module

The dashboard displays:

- Total number of products
- Total number of orders
- Number of low-stock items
- Total revenue
- A simple top-selling products chart
- A low-stock products table

### 8.3 Product Management Module

The Products page allows the user to:

- Add a new product
- Edit an existing product
- Delete products not protected by order references
- Search products by name or category
- View inventory details in a sortable table

### 8.4 Order Processing Module

The New Order page allows the user to:

- Enter customer details
- Search available products
- Add one or more products to a cart
- Set product quantities
- Compute the order total automatically
- Save the order and deduct stock
- Send or log a customer receipt after the order is completed

### 8.5 Reports Module

The Reports page allows the user to:

- View a products report
- View an orders report
- Search report data
- View order details and ordered products
- Export reports as PDF files

## 9. Architectural Pattern Used

The project follows a simple layered desktop application structure:

- `store_pos/main.py`
  - application entry point
- `store_pos/config.py`
  - central configuration values
- `store_pos/database.py`
  - schema creation and SQL operations
- `store_pos/models.py`
  - data classes for domain entities
- `store_pos/gui/`
  - user interface modules
- `store_pos/utils/`
  - reusable helper functions for validation, PDF generation, and email sending

This structure separates responsibilities instead of putting all code in one file. That makes the project easier to understand, maintain, and explain during defense.

## 10. Technology Stack

The system uses the following technologies:

- Python 3
- Tkinter and ttk for the graphical user interface
- SQLite through the built-in `sqlite3` module
- ReportLab for PDF report generation
- `smtplib`, `ssl`, and `email.message` for receipt emailing

## 11. Object-Oriented Programming Concepts Applied

The system applies object-oriented concepts through:

- class-based GUI views such as `LoginWindow`, `MainApplication`, `ProductsView`, `OrdersView`, and `ReportsView`
- reusable table component design through `ModernDataTable`
- data models using dataclasses: `Product`, `Customer`, `Order`, and `OrderItem`
- encapsulated methods for view behavior, validation handling, and report generation

## 12. Validation Rules Implemented

The system includes validation for:

- required product fields
- required customer name and email
- valid email format
- numeric product price
- non-negative stock quantity
- positive cart quantity
- prevention of empty orders
- prevention of orders that exceed available stock

These validations help protect data quality and improve reliability.

## 13. Reports Produced by the System

The system generates two main reports:

### 13.1 Products Report

Contains:

- product name
- category
- price
- current stock on hand
- units sold

### 13.2 Orders Report

Contains:

- order ID
- customer information
- ordered items summary
- total units
- total amount
- order date
- receipt sending status

Both reports can be exported as PDF files for printing and submission.

## 14. Realistic Data Used in the System

The system seeds realistic electronics-store data including:

- laptops
- monitors
- keyboards
- mice
- headphones
- storage devices
- cameras
- desks and chairs
- named customers with email addresses and phone numbers
- multi-line sample orders

This makes the demonstration more aligned with a real store workflow instead of using random placeholder values.

## 15. How the System Solves the Business Problem

The system improves store operations in the following ways:

- It replaces scattered manual inventory tracking with one stored database.
- It reduces order-entry mistakes by validating fields and quantities.
- It updates stock automatically after each confirmed order.
- It gives the owner fast visibility through dashboard statistics.
- It helps business review through generated reports.
- It prepares receipt output for customer communication.

## 16. Limitations

The following limitations still exist in the current version:

- Login is basic and uses one stored credential setup.
- There is no dedicated profile page or logout flow.
- Email receipt delivery depends on SMTP configuration.
- The system is intended for local desktop use on one machine.
- There is no advanced audit log, role management, or supplier module.

## 17. Conclusion

The Store Inventory and POS System for ElectroHub is a complete desktop business application that demonstrates the practical use of Python GUI development, relational database design, validation, reporting, and object-oriented programming. It is suitable for demonstration as a final project because it solves a realistic store problem with connected modules instead of isolated forms.
