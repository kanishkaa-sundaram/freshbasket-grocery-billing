# FreshBasket: Grocery Inventory & Billing Management System

A desktop billing and inventory system for local grocery shopkeepers, built with **Python (Tkinter)** and **MySQL**. It was originally built as a DBMS mini project and grew into a complete shop-owner dashboard.

Instead of paper ledgers and manual totals, the owner gets a visual, shop-style screen: pick products, take payment, print or send the bill, and see stock, dues and sales update automatically.

## The problem it solves
Small grocery shops usually track stock in notebooks, add up bills by hand, and keep "pay later" (khata) accounts on paper. This leads to billing mistakes, forgotten dues, expired stock and no clear picture of what sells. FreshBasket puts all of this in one app that works on a normal shop computer.

## Features

### Billing
- Product dashboard with photos, category filters and live search
- Current bill panel that scrolls on its own, with the checkout button always visible
- Welcome message at the start of billing and a "Thank you! Visit again!" message on every receipt
- Customer name and phone number captured for every bill

### Payments
- **UPI QR codes** for GPay, PhonePe and Paytm, generated for the exact bill amount
- Card and cash payments
- **Credit Ledger (khata):** the customer takes the goods now and pays later, and the owner marks the entry as paid when the money arrives

### Bills and receipts
- Unique bill number for every bill, for example `FB-20261112-0007`
- Print button that sends the receipt to the default printer (Windows)
- **E-bill on WhatsApp:** opens WhatsApp with the receipt and the customer's number filled in, ready to send

### Returns and sales log
- Full return flow: pick the bill, choose the items, give a reason, and the stock is restored automatically
- Sales Log with search by customer, phone number or bill number
- Delete a bill safely, with a clear prompt if the bill is linked to a Credit Ledger entry

### Inventory
- Add, update and delete products, add categories, and attach a product photo
- A product that has already been sold can still be deleted, and its old bills still show the correct item name
- Expiry date for each product, with colour-coded warnings on the product card: "Expires in 3d", "Expires today" and "Expired"
- Low-stock warnings on cards, plus live counters for products, low stock and today's sales in the header

### Reports
One-click SQL reports that also display the query being run: low stock, today's sales, sales by category, top 5 products, items expiring within 7 days, pending credit dues and the returns log.

### Language support
The interface can be switched between **English, Hindi and Tamil** so shopkeepers can work in the language they are comfortable with.

## Database design
The MySQL database (`grocery_db`) is created automatically on first run and contains 7 tables:

| Table | Purpose |
|---|---|
| `categories` | Product categories |
| `products` | Name, category, price, stock, unit, image, expiry date |
| `customers` | Name and phone number |
| `bills` | One row per sale, with total, payment mode and status |
| `bill_items` | The items in each bill, with the product name saved at the time of sale |
| `returns` | Returned items with reason and date |
| `khata` | Credit ledger entries with paid or pending status |

DBMS concepts demonstrated: table creation, primary and foreign keys, `CHECK` constraints, `ON DELETE CASCADE` and `ON DELETE SET NULL`, joins, aggregate queries with `GROUP BY`, `LIKE` searching, and a **transaction** at checkout that creates the bill, saves its items and reduces stock together (and rolls back if stock is insufficient).

## Project structure
```
app.py                 Tkinter interface and application logic
db.py                  Database connection, schema, seed data and queries
db_config.example.py   Template for your MySQL password file
requirements.txt       Python packages
images/                Product photos
receipts/              Receipts saved when printing (created automatically)
```

## Setup
1. Install Python 3.12 and MySQL Server.
2. Create a virtual environment and install the packages:
   ```
   py -3.12 -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   ```
3. Copy `db_config.example.py` to `db_config.py` and enter your MySQL password. This file is ignored by Git, so your password is never uploaded.
4. Run the app. The database, tables and sample products are created automatically:
   ```
   python app.py
   ```

## Limitations
- Single computer: the app talks to a local MySQL server, so it is not built for several counters at once
- No login screen yet, so anyone who opens the app has full access
- The WhatsApp e-bill opens a pre-filled message for the owner to send. Automatic SMS or WhatsApp delivery would need a paid messaging service
- The print button uses the Windows print command

## Future improvements
Owner login with roles, barcode scanning, a multi-counter client-server version, supplier and purchase tracking, and automatic e-bill delivery.

## Tech stack
Python, Tkinter, MySQL, Pillow, qrcode

## Author
Built by KANISHKAA S
