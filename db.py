import mysql.connector
from datetime import datetime, date, timedelta

try:
    from db_config import CFG  # your real password lives in this local, git-ignored file
except ImportError:
    CFG = dict(host="localhost", user="root", password="kanishkaa")  # fallback placeholder
DB = "grocery_db"


def connect(use_db=True):
    if use_db:
        return mysql.connector.connect(database=DB, charset="utf8mb4", **CFG)
    return mysql.connector.connect(charset="utf8mb4", **CFG)


def run(sql, params=(), fetch=False):
    con = connect()
    cur = con.cursor()
    try:
        cur.execute(sql, params)
        if fetch:
            return cur.fetchall()
        con.commit()
        return cur.lastrowid
    finally:
        cur.close()
        con.close()


def query(sql, params=()):
    con = connect()
    cur = con.cursor()
    try:
        cur.execute(sql, params)
        return [d[0] for d in cur.description], cur.fetchall()
    finally:
        cur.close()
        con.close()


# ---------------------------------------------------------------- SCHEMA
# NOTE: bill_items.name is a SNAPSHOT of the product name at sale time, and
# product_id is nullable with ON DELETE SET NULL. This means a shopkeeper can
# delete a product from Inventory at any time -- even one that was sold in
# the past -- and old bills still display correctly using the saved name.
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS categories(
        category_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE) CHARACTER SET utf8mb4""",
    """CREATE TABLE IF NOT EXISTS products(
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(80) NOT NULL,
        category_id INT NOT NULL,
        price DECIMAL(8,2) NOT NULL CHECK (price >= 0),
        stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
        unit VARCHAR(20) DEFAULT '1 pc',
        image VARCHAR(120),
        expiry_date DATE DEFAULT NULL,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)) CHARACTER SET utf8mb4""",
    """CREATE TABLE IF NOT EXISTS customers(
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(60) NOT NULL,
        phone VARCHAR(15) NOT NULL UNIQUE) CHARACTER SET utf8mb4""",
    """CREATE TABLE IF NOT EXISTS bills(
        bill_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT NOT NULL,
        bill_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total DECIMAL(10,2) NOT NULL,
        mode VARCHAR(20) NOT NULL DEFAULT 'cash',
        status VARCHAR(20) NOT NULL DEFAULT 'Completed',
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)) CHARACTER SET utf8mb4""",
    """CREATE TABLE IF NOT EXISTS bill_items(
        item_id INT AUTO_INCREMENT PRIMARY KEY,
        bill_id INT NOT NULL,
        product_id INT NULL,
        name VARCHAR(80) NOT NULL,
        qty INT NOT NULL,
        price DECIMAL(8,2) NOT NULL,
        FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL) CHARACTER SET utf8mb4""",
    """CREATE TABLE IF NOT EXISTS returns(
        return_id INT AUTO_INCREMENT PRIMARY KEY,
        bill_id INT NULL,
        product_id INT NULL,
        name VARCHAR(80) NOT NULL,
        qty INT NOT NULL DEFAULT 1,
        reason VARCHAR(150),
        return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE SET NULL,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL) CHARACTER SET utf8mb4""",
    """CREATE TABLE IF NOT EXISTS khata(
        khata_id INT AUTO_INCREMENT PRIMARY KEY,
        bill_id INT NULL,
        name VARCHAR(60) NOT NULL,
        phone VARCHAR(15) NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        paid BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bill_id) REFERENCES bills(bill_id) ON DELETE SET NULL) CHARACTER SET utf8mb4""",
]

# Last item in each tuple is "days from today until expiry" (None = non-perishable /
# no expiry tracked, e.g. rice, sugar). A couple of dairy items are seeded close to
# expiry on purpose so the near-expiry display has something to show right away.
SEED = {
    "Fruits & Vegetables": [("Tomato", 30, 50, "1 kg", "tomato.jpg", None), ("Onion", 40, 60, "1 kg", "onion.jpg", None),
                            ("Banana", 50, 40, "1 dozen", "banana.jpg", 5), ("Potato", 35, 55, "1 kg", "potato.jpg", None)],
    "Dairy": [("Milk", 28, 30, "500 ml", "milk.jpg", 2), ("Curd", 35, 25, "400 g", "curd.jpg", 3),
              ("Butter", 58, 20, "100 g", "butter.jpg", 30), ("Paneer", 90, 15, "200 g", "paneer.jpg", 4)],
    "Staples": [("Rice", 65, 80, "1 kg", "rice.jpg", None), ("Toor Dal", 140, 40, "1 kg", "dal.jpg", None),
                ("Wheat Atta", 55, 45, "1 kg", "atta.jpg", 60), ("Sugar", 45, 60, "1 kg", "sugar.jpg", None)],
    "Snacks": [("Biscuits", 20, 70, "1 pack", "biscuits.jpg", 90), ("Chips", 20, 8, "1 pack", "chips.jpg", 60)],
    "Beverages": [("Tea Powder", 120, 30, "250 g", "tea.jpg", None), ("Coffee", 150, 6, "100 g", "coffee.jpg", None),
                  ("Orange Juice", 95, 18, "1 L", "juice.jpg", 6)],
}


def setup():
    con = connect(False)
    cur = con.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB} CHARACTER SET utf8mb4")
    cur.execute(f"USE {DB}")
    for s in SCHEMA:
        cur.execute(s)
    # Auto-repair databases created before khata/returns.bill_id became nullable --
    # harmless (and cheap) to run every time, including on an already-migrated DB.
    for stmt in ("ALTER TABLE khata MODIFY COLUMN bill_id INT NULL",
                 "ALTER TABLE returns MODIFY COLUMN bill_id INT NULL",
                 "ALTER TABLE products ADD COLUMN expiry_date DATE DEFAULT NULL"):
        try:
            cur.execute(stmt)
        except Exception:
            pass

    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        for cat, items in SEED.items():
            cur.execute("INSERT INTO categories(name) VALUES(%s)", (cat,))
            cid = cur.lastrowid
            cur.executemany(
                "INSERT INTO products(name,category_id,price,stock,unit,image,expiry_date) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                [(n, cid, p, s, u, i, (date.today() + timedelta(days=d)) if d is not None else None)
                 for n, p, s, u, i, d in items])
    con.commit()
    cur.close()
    con.close()


def bill_number(bill_id):
    """Human-friendly unique bill number for printing/receipts, e.g. FB-20260930-0007."""
    return f"FB-{datetime.now().strftime('%Y%m%d')}-{bill_id:04d}"


def checkout(name, phone, cart, mode="cash"):
    """
    cart = {product_id: (name, price, qty)}.
    mode = 'gpay' | 'phonepe' | 'paytm' | 'card' | 'cash' | 'khata'
    For 'khata', the full amount is recorded as credit owed -- no money changes hands yet.
    Returns (bill_id, total).
    """
    con = connect()
    cur = con.cursor()
    try:
        cur.execute("SELECT customer_id FROM customers WHERE phone=%s", (phone,))
        r = cur.fetchone()
        if r:
            cid = r[0]
        else:
            cur.execute("INSERT INTO customers(name,phone) VALUES(%s,%s)", (name, phone))
            cid = cur.lastrowid

        total = sum(p * q for _, p, q in cart.values())
        cur.execute("INSERT INTO bills(customer_id,total,mode) VALUES(%s,%s,%s)", (cid, total, mode))
        bid = cur.lastrowid

        for pid, (n, p, q) in cart.items():
            cur.execute("UPDATE products SET stock=stock-%s WHERE product_id=%s AND stock>=%s", (q, pid, q))
            if cur.rowcount == 0:
                raise ValueError(f"Not enough stock for {n}")
            # name is snapshotted here so the bill survives a future product deletion
            cur.execute("INSERT INTO bill_items(bill_id,product_id,name,qty,price) VALUES(%s,%s,%s,%s,%s)",
                        (bid, pid, n, q, p))

        if mode == "khata":
            cur.execute("INSERT INTO khata(bill_id,name,phone,amount) VALUES(%s,%s,%s,%s)", (bid, name, phone, total))

        con.commit()
        return bid, total
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
        con.close()


def delete_product(pid):
    """Delete a product from Inventory -- allowed even if it appears in past bills.
    Those bills keep showing the correct item name via the bill_items.name snapshot."""
    run("DELETE FROM products WHERE product_id=%s", (pid,))


def create_return(bill_id, product_id, name, qty, reason):
    """Logs a return, restocks the product (if it still exists), and flags the bill."""
    con = connect()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO returns(bill_id,product_id,name,qty,reason) VALUES(%s,%s,%s,%s,%s)",
                    (bill_id, product_id, name, qty, reason))
        if product_id:
            cur.execute("UPDATE products SET stock = stock + %s WHERE product_id=%s", (qty, product_id))
        cur.execute("UPDATE bills SET status='Return Requested' WHERE bill_id=%s", (bill_id,))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
        con.close()


def get_khata_for_bill(bill_id):
    """Returns (khata_id, amount, paid) if this bill has a Credit Ledger entry, else None."""
    rows = run("SELECT khata_id, amount, paid FROM khata WHERE bill_id=%s", (bill_id,), fetch=True)
    return rows[0] if rows else None


def delete_bill(bill_id, remove_khata=False):
    """Deletes a bill and its line items. Stock is NOT restored (the sale is simply
    erased from the record, not reversed).

    remove_khata=False (default): any khata entry for this bill is KEPT, just detached
        (its bill_id is cleared) so it still shows in the Credit Ledger.
    remove_khata=True: the khata entry for this bill is deleted along with the bill.

    Returns entries are always kept (detached), never deleted by this function.
    This detaches rows explicitly in Python rather than relying on the database's
    own ON DELETE behavior, so it works correctly even on a database created
    before the Credit Ledger schema was last updated."""
    con = connect()
    cur = con.cursor()
    try:
        if remove_khata:
            cur.execute("DELETE FROM khata WHERE bill_id=%s", (bill_id,))
        else:
            cur.execute("UPDATE khata SET bill_id=NULL WHERE bill_id=%s", (bill_id,))
        cur.execute("UPDATE returns SET bill_id=NULL WHERE bill_id=%s", (bill_id,))
        cur.execute("DELETE FROM bills WHERE bill_id=%s", (bill_id,))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
        con.close()


def mark_khata_paid(khata_id):
    run("UPDATE khata SET paid=TRUE WHERE khata_id=%s", (khata_id,))
