# Sample Problems and Business Scenarios

## Purpose

This document lists realistic business problems related to ElectroHub and explains how the system addresses each one. These scenarios can be used during project presentation, documentation review, or oral defense.

## Scenario 1: Manual stock tracking causes wrong inventory counts

### Problem

When products are sold manually and stock is updated on paper, employees may forget to subtract sold quantities. This can cause the store to think an item is available when it is already out of stock.

### System Response

The system deducts stock automatically when an order is saved. It also blocks an order if the requested quantity exceeds current stock.

### Example

- A customer orders 2 monitors.
- The order is saved.
- The system reduces the monitor stock by 2 immediately.

## Scenario 2: Sales encoding is slow when there are multiple items

### Problem

Handwritten invoices or separate product lookups slow down the cashier, especially for orders containing multiple products.

### System Response

The New Order page provides a searchable product list, a quantity selector, and a cart that combines multiple products before the order is submitted.

### Example

- A customer buys a laptop, mouse, and USB-C hub.
- The cashier adds all three to the cart.
- The system computes the total automatically.

## Scenario 3: Invalid customer email leads to unusable receipt records

### Problem

If the cashier enters an incorrect email format, the receipt destination becomes unreliable.

### System Response

The system validates email format before allowing the order to proceed.

### Example

- Input: `juan.gmail.com`
- Result: validation error
- Correct input: `juan@gmail.com`

## Scenario 4: Staff accidentally enters negative or non-numeric product values

### Problem

Users may enter an invalid price such as letters or a negative stock quantity.

### System Response

The product form validates required fields, non-negative stock, and numeric price values before saving.

### Example

- Price entered: `abc`
- Result: validation error

- Stock entered: `-5`
- Result: validation error

## Scenario 5: Store owner needs fast low-stock monitoring

### Problem

Without a summary view, low-stock items may only be noticed after customers ask for unavailable products.

### System Response

The dashboard shows low-stock counts and a dedicated low-stock table using the configured threshold.

### Example

- Standing Desk stock falls to 4.
- It appears in the low-stock list because the threshold is 5.

## Scenario 6: Products already linked to sales should not be deleted freely

### Problem

Deleting a product that already appears in past orders can damage report consistency.

### System Response

The database uses a foreign key restriction to prevent deleting products already referenced by order items.

### Example

- A keyboard has already been sold in previous orders.
- A delete action is attempted.
- The system blocks the delete and preserves history integrity.

## Scenario 7: The manager needs a printable report for inventory review

### Problem

Managers often need a readable inventory list for meetings, checking stock, or submission requirements.

### System Response

The Reports module can generate a Products Report PDF that includes product name, category, price, stock on hand, and units sold.

## Scenario 8: The manager needs a sales history report

### Problem

It is difficult to review completed sales without a consolidated order report.

### System Response

The Orders Report shows customer details, line counts, unit totals, order totals, receipt status, and order dates, and can also be exported to PDF.

## Scenario 9: The system should look like a real business application, not default forms only

### Problem

A final project should not appear as disconnected default input boxes without workflow structure.

### System Response

The application includes:

- a login screen
- a dashboard
- navigation sidebar
- modular product, order, and report pages
- styled tables
- status messages
- PDF export actions

## Scenario 10: The owner wants a quick summary of business activity

### Problem

Reviewing all tables manually is slow when the owner only wants the current status of the store.

### System Response

The dashboard summarizes:

- total products
- total orders
- low-stock count
- total revenue
- top-selling products

## Summary

These sample problems are directly related to the selected business context of a small electronics store. They show that the system is not just a set of forms, but a connected solution to realistic operational problems.
