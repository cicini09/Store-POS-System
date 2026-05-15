# User Guide

## 1. System Requirements

- Python 3
- Tkinter support
- SQLite support
- ReportLab for PDF export

## 2. Running the Application

From the project root:

```bash
python -m store_pos.main
```

## 3. Default Login

- Username: `admin`
- Password: `admin123`

## 4. Main Workflow

### Step 1: Log in

Open the application and enter the login credentials to access the main window.

### Step 2: Review the dashboard

The Dashboard shows the current store status:

- total products
- total orders
- low-stock count
- total revenue
- sales snapshot

### Step 3: Manage products

Go to the Products page to:

- add a product
- edit a selected product
- delete selected products
- search by product name or category

### Step 4: Create an order

Go to the New Order page to:

- enter customer information
- select products from the list
- set quantities
- add products to the cart
- review the total
- place the order

When the order is saved:

- the order is recorded
- stock is reduced
- receipt processing is started

### Step 5: Review reports

Go to the Reports page to:

- inspect the products report
- inspect the orders report
- view order details
- export reports to PDF

## 5. Validation Rules Visible to the User

The system checks:

- required fields must not be blank
- email must be valid
- quantity must be a positive whole number
- stock must not be negative
- price must be numeric and non-negative
- cart must not be empty before placing an order
- requested quantity must not exceed stock

## 6. Report Outputs

Generated files are saved under:

- `store_pos/reports/`

The system can produce:

- products report PDF
- orders report PDF
- email receipt logs

## 7. Troubleshooting

### PDF export does not work

Install ReportLab and run the program again.

### Receipt was not sent

Check SMTP configuration values or environment variables.

### Product cannot be deleted

The product may already be referenced by a saved order. This is expected behavior to protect sales history.
