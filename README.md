# FreshBasket: Grocery Inventory & Billing System

A desktop billing and inventory system for local grocery shopkeepers, built with Python (Tkinter) and MySQL.

## Features
- Product dashboard with photos, search and category filters
- UPI QR payments (GPay, PhonePe, Paytm), card, cash and credit ledger (khata)
- Unique bill numbers, printable receipts and WhatsApp e-bills
- Returns workflow that restores stock
- Expiry-date warnings and low-stock alerts
- SQL reports (sales by category, top products, pending dues, expiring items)
- Multi-language interface (English, Hindi, Tamil)

## Setup
1. Install Python 3.12 and MySQL Server.
2. Create a virtual environment and install packages:
   ```
   py -3.12 -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   ```
3. Copy `db_config.example.py` to `db_config.py` and enter your MySQL password.
4. Put product photos in an `images/` folder (file names are listed in `db.py`).
5. Run the app (the database and tables are created automatically):
   ```
   python app.py
   ```

## Tech stack
Python, Tkinter, MySQL, Pillow, qrcode
