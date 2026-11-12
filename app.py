"""
FreshBasket -- Shop Owner Billing Dashboard (Tkinter + MySQL)

Layout: a left sidebar for navigation (Billing / Inventory / Sales Log /
Returns / Credit Ledger / SQL Reports) plus a clean single-row header --
no absolute-position overlays, so nothing overlaps or ghosts on resize.
Product and category cards use real rounded corners (drawn on a Canvas)
for a closer look to modern grocery apps. The Current Bill panel has its
own internally-scrolling item list with the totals/checkout footer
pinned at the bottom, so it's always reachable no matter how many items
are in the cart.
"""
import os
import shutil
import webbrowser
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk, ImageDraw
import db

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
RECEIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
os.makedirs(RECEIPT_DIR, exist_ok=True)

ORANGE, ORANGE_DARK, GREEN, RED = "#fc8019", "#e0691a", "#0c831f", "#cb202d"
BG, CARD, SIDEBAR, MUTED = "#f4f5f7", "#ffffff", "#ffffff", "#8a8a93"
_cache = {}

# ----------------------------------------------------------------- i18n
# "Khata" is shown in English as "Credit Ledger" per the shop owner's request;
# Hindi/Tamil keep their own native words since those already read naturally there.
TR = {
    "English": {
        "app_title": "FreshBasket", "tagline": "Shop Owner Dashboard",
        "nav_shop": "Billing", "nav_inv": "Inventory", "nav_bills": "Sales Log",
        "nav_returns": "Returns", "nav_khata": "Credit Ledger", "nav_reports": "SQL Reports",
        "welcome": "👋 Welcome! Pick items below to start a new bill",
        "search_ph": "Search product...", "all_cat": "All",
        "add": "ADD", "cart_title": "Current Bill", "checkout": "Proceed to Payment",
        "cust_name": "Customer Name", "phone": "Phone Number", "total": "Total",
        "pay_title": "Select Payment Mode", "confirm_pay": "Confirm Payment",
        "thank_you": "🙏 Thank you! Visit again!", "print_bill": "🖨 Print Bill",
        "send_ebill": "📲 Send E-Bill (WhatsApp)", "new_bill": "Start New Bill",
        "return_btn": "↩ Return Item(s)", "mark_paid": "Mark Paid",
        "low_stock": "Low stock", "products": "Products", "today_sales": "Today's sales",
        "khata_mode": "📒 Credit (Pay Later)", "khata_title": "Credit Ledger",
    },
    "Hindi": {
        "app_title": "फ्रेशबास्केट", "tagline": "दुकान डैशबोर्ड",
        "nav_shop": "बिलिंग", "nav_inv": "इन्वेंटरी", "nav_bills": "बिक्री सूची",
        "nav_returns": "वापसी", "nav_khata": "खाता", "nav_reports": "SQL रिपोर्ट",
        "welcome": "👋 स्वागत है! बिल शुरू करने के लिए सामान चुनें",
        "search_ph": "उत्पाद खोजें...", "all_cat": "सभी",
        "add": "जोड़ें", "cart_title": "वर्तमान बिल", "checkout": "भुगतान करें",
        "cust_name": "ग्राहक का नाम", "phone": "फ़ोन नंबर", "total": "कुल",
        "pay_title": "भुगतान का तरीका चुनें", "confirm_pay": "भुगतान की पुष्टि करें",
        "thank_you": "🙏 धन्यवाद! फिर से पधारें!", "print_bill": "🖨 बिल प्रिंट करें",
        "send_ebill": "📲 ई-बिल भेजें (WhatsApp)", "new_bill": "नया बिल शुरू करें",
        "return_btn": "↩ सामान वापस करें", "mark_paid": "भुगतान हो गया",
        "low_stock": "कम स्टॉक", "products": "उत्पाद", "today_sales": "आज की बिक्री",
        "khata_mode": "📒 खाता (बाद में भुगतान)", "khata_title": "खाता",
    },
    "Tamil": {
        "app_title": "ஃப்ரெஷ்பாஸ்கெட்", "tagline": "கடை முகப்புப் பலகை",
        "nav_shop": "பில்லிங்", "nav_inv": "இருப்பு", "nav_bills": "விற்பனை பட்டியல்",
        "nav_returns": "திரும்பப் பெறுதல்", "nav_khata": "கடன் கணக்கு", "nav_reports": "SQL அறிக்கைகள்",
        "welcome": "👋 வரவேற்கிறோம்! பொருட்களைத் தேர்ந்தெடுத்து பில் தொடங்குங்கள்",
        "search_ph": "பொருளைத் தேடுங்கள்...", "all_cat": "அனைத்தும்",
        "add": "சேர்", "cart_title": "தற்போதைய பில்", "checkout": "பணம் செலுத்த தொடரவும்",
        "cust_name": "வாடிக்கையாளர் பெயர்", "phone": "தொலைபேசி எண்", "total": "மொத்தம்",
        "pay_title": "பணம் செலுத்தும் முறையைத் தேர்ந்தெடுக்கவும்", "confirm_pay": "பணம் செலுத்துதலை உறுதிப்படுத்தவும்",
        "thank_you": "🙏 நன்றி! மீண்டும் வருக!", "print_bill": "🖨 பில் அச்சிடு",
        "send_ebill": "📲 இ-பில் அனுப்பு (WhatsApp)", "new_bill": "புதிய பில் தொடங்கு",
        "return_btn": "↩ பொருளைத் திருப்பி அனுப்பு", "mark_paid": "செலுத்தப்பட்டது",
        "low_stock": "குறைந்த இருப்பு", "products": "பொருட்கள்", "today_sales": "இன்றைய விற்பனை",
        "khata_mode": "📒 கடன் (பின்னர் செலுத்தவும்)", "khata_title": "கடன் கணக்கு",
    },
}
CAT_ICON = {"Fruits & Vegetables": "🥦", "Dairy": "🥛", "Staples": "🌾", "Snacks": "🍪", "Beverages": "🧃"}
NAV_ITEMS = [("shop", "🧾", "nav_shop"), ("inv", "📦", "nav_inv"), ("bills", "📜", "nav_bills"),
             ("returns", "↩", "nav_returns"), ("khata", "📒", "nav_khata"), ("reports", "📊", "nav_reports")]


def load_img(fname, size=(100, 100), label="?"):
    key = (fname, size, label)
    if key not in _cache:
        path = os.path.join(IMG_DIR, fname or "")
        if fname and os.path.isfile(path):
            im = Image.open(path).convert("RGB").resize(size)
        else:
            im = Image.new("RGB", size, "#ffe9d6")
            ImageDraw.Draw(im).text((size[0] // 2 - 6, size[1] // 2 - 8), (label or "?")[:1].upper(), fill=ORANGE)
        _cache[key] = ImageTk.PhotoImage(im)
    return _cache[key]


def round_points(x1, y1, x2, y2, r):
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


def make_card(parent, w, h, r=14, fill=CARD, outline="#ebebef"):
    """A rounded-corner card: a Canvas with the rounded rect drawn, holding an
    inner Frame (same bg) where real widgets go via canvas.create_window."""
    cv = tk.Canvas(parent, width=w, height=h, highlightthickness=0, bg=parent.cget("bg"))
    cv.create_polygon(round_points(1, 1, w - 1, h - 1, r), smooth=True, fill=fill, outline=outline)
    inner = tk.Frame(cv, bg=fill)
    cv.create_window(w // 2, h // 2, window=inner)
    return cv, inner


def circle_btn(parent, d=32, bg=GREEN, fg="white", text="+", command=None, font_size=14):
    cv = tk.Canvas(parent, width=d, height=d, highlightthickness=0, bg=parent.cget("bg"))
    oid = cv.create_oval(2, 2, d - 2, d - 2, fill=bg, outline="")
    tid = cv.create_text(d // 2, d // 2, text=text, fill=fg, font=("Segoe UI", font_size, "bold"))
    if command:
        cv.tag_bind(oid, "<Button-1>", lambda e: command())
        cv.tag_bind(tid, "<Button-1>", lambda e: command())
        cv.configure(cursor="hand2")
    return cv


def fill(tree, headers, rows):
    tree["columns"] = headers
    tree["show"] = "headings"
    for h in headers:
        tree.heading(h, text=h)
        tree.column(h, width=130, anchor="w")
    tree.delete(*tree.get_children())
    for r in rows:
        tree.insert("", "end", values=r)


REPORTS = {
    "Low stock (< 10)": "SELECT name, stock, unit FROM products WHERE stock < 10 ORDER BY stock",
    "Today's sales": "SELECT COUNT(*) AS bills, IFNULL(SUM(total),0) AS revenue FROM bills WHERE DATE(bill_date)=CURDATE()",
    "Sales by category": "SELECT c.name AS category, SUM(bi.qty) AS qty_sold, SUM(bi.qty*bi.price) AS revenue "
                         "FROM bill_items bi JOIN products p ON bi.product_id=p.product_id JOIN categories c ON p.category_id=c.category_id "
                         "GROUP BY c.name ORDER BY revenue DESC",
    "Top 5 products": "SELECT bi.name, SUM(bi.qty) AS sold FROM bill_items bi GROUP BY bi.name ORDER BY sold DESC LIMIT 5",
    "Expiring soon (<=7 days)": "SELECT name, expiry_date, DATEDIFF(expiry_date, CURDATE()) AS days_left FROM products "
                                "WHERE expiry_date IS NOT NULL AND DATEDIFF(expiry_date, CURDATE()) <= 7 ORDER BY expiry_date",
    "Pending credit dues": "SELECT name, phone, amount, created_at FROM khata WHERE paid=FALSE ORDER BY created_at",
    "Returns log": "SELECT name, qty, reason, return_date FROM returns ORDER BY return_date DESC",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "English"
        self.title("FreshBasket")
        self.geometry("1360x780")
        self.configure(bg=BG)
        self.cart = {}
        self.sel_id = None
        self.current_page = "shop"

        self.build_header()
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        self.build_sidebar(body)

        self.pages_container = tk.Frame(body, bg=BG)
        self.pages_container.pack(side="left", fill="both", expand=True)
        self.pages = {}
        for key, _, _ in NAV_ITEMS:
            f = tk.Frame(self.pages_container, bg=BG)
            f.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = f
        self.pages_container.grid_rowconfigure(0, weight=1)
        self.pages_container.grid_columnconfigure(0, weight=1)

        self.build_shop(self.pages["shop"])
        self.build_inv(self.pages["inv"])
        self.build_bills(self.pages["bills"])
        self.build_returns(self.pages["returns"])
        self.build_khata(self.pages["khata"])
        self.build_reports(self.pages["reports"])

        self.set_language("English")
        self.show_page("shop")
        self.refresh_all()

    def t(self, key):
        return TR.get(self.lang, TR["English"]).get(key, TR["English"].get(key, key))

    # ============================================================ HEADER / SIDEBAR
    def build_header(self):
        header = tk.Frame(self, bg=ORANGE, height=56)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        self.logo_lbl = tk.Label(header, bg=ORANGE, fg="white", font=("Segoe UI", 16, "bold"))
        self.logo_lbl.pack(side="left", padx=18)

        self.q = tk.StringVar()
        search_wrap = tk.Frame(header, bg="white")
        search_wrap.pack(side="left", padx=10, pady=12, fill="y")
        tk.Label(search_wrap, text="🔍", bg="white", fg=MUTED).pack(side="left", padx=(8, 2))
        e = tk.Entry(search_wrap, textvariable=self.q, width=34, font=("Segoe UI", 10), bd=0, bg="white")
        e.pack(side="left", padx=(0, 10), ipady=4)
        e.bind("<KeyRelease>", lambda ev: self.refresh_grid())

        right = tk.Frame(header, bg=ORANGE)
        right.pack(side="right", padx=18)
        self.lang_var = tk.StringVar(value="English")
        lang_box = ttk.Combobox(right, textvariable=self.lang_var, state="readonly", width=9,
                                 values=list(TR.keys()))
        lang_box.pack(side="right")
        lang_box.bind("<<ComboboxSelected>>", lambda e: self.set_language(self.lang_var.get()))
        tk.Label(right, text="🌐", bg=ORANGE, fg="white", font=("Segoe UI", 12)).pack(side="right", padx=(0, 6))
        self.stats = tk.Label(right, bg=ORANGE, fg="white", font=("Segoe UI", 9))
        self.stats.pack(side="right", padx=16)

        self.welcome_bar = tk.Frame(self, bg=ORANGE_DARK, height=34)
        self.welcome_bar.pack(fill="x", side="top")
        self.welcome_bar.pack_propagate(False)
        self.welcome_lbl = tk.Label(self.welcome_bar, bg=ORANGE_DARK, fg="white", font=("Segoe UI", 10, "bold"))
        self.welcome_lbl.pack(side="left", padx=18)

    def build_sidebar(self, parent):
        side = tk.Frame(parent, bg=SIDEBAR, width=180)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Frame(side, bg="#ebebef", width=1).pack(side="right", fill="y")
        self.nav_btns = {}
        nav_wrap = tk.Frame(side, bg=SIDEBAR)
        nav_wrap.pack(fill="x", pady=14, padx=10)
        for key, icon, label_key in NAV_ITEMS:
            b = tk.Label(nav_wrap, bg=SIDEBAR, fg="#444", font=("Segoe UI", 10, "bold"),
                         anchor="w", padx=12, pady=10, cursor="hand2")
            b.pack(fill="x", pady=2)
            b.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            self.nav_btns[key] = (b, icon, label_key)

    def show_page(self, key):
        self.current_page = key
        self.pages[key].tkraise()
        for k, (b, icon, label_key) in self.nav_btns.items():
            active = k == key
            b.config(bg=("#fff3e8" if active else SIDEBAR), fg=(ORANGE if active else "#444"))
        # Welcome banner only makes sense on the Billing page
        if key == "shop":
            self.welcome_bar.pack(fill="x", side="top")
        else:
            self.welcome_bar.pack_forget()
        if key == "inv": self.refresh_inv()
        if key == "bills": self.refresh_bills()
        if key == "returns": self.refresh_returns()
        if key == "khata": self.refresh_khata()

    def set_language(self, lang):
        self.lang = lang
        self.lang_var.set(lang)
        t = self.t
        self.logo_lbl.config(text=t("app_title"))
        self.welcome_lbl.config(text=t("welcome"))
        self.checkout_btn.config(text=t("checkout"))
        self.cart_title_lbl.config(text=t("cart_title"))
        self.name_lbl.config(text=t("cust_name"))
        self.phone_lbl.config(text=t("phone"))
        for key, icon, label_key in NAV_ITEMS:
            b, _, _ = self.nav_btns[key]
            b.config(text=f"{icon}  {t(label_key)}")
        self.khata_title_lbl.config(text=t("khata_title"))
        self.refresh_all()

    def refresh_all(self):
        self.load_categories()
        self.refresh_grid()
        if self.current_page == "inv": self.refresh_inv()
        if self.current_page == "bills": self.refresh_bills()
        if self.current_page == "returns": self.refresh_returns()
        if self.current_page == "khata": self.refresh_khata()

    def load_categories(self):
        rows = db.run("SELECT category_id,name FROM categories ORDER BY name", fetch=True)
        self.cat_ids = {n: i for i, n in rows}
        self.f_cat["values"] = list(self.cat_ids)
        self.build_cat_rail()

    # ============================================================ BILLING PAGE
    def build_shop(self, parent):
        body = tk.Frame(parent, bg=BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True)

        self.cat_rail = tk.Frame(left, bg=BG)
        self.cat_rail.pack(fill="x", padx=16, pady=(14, 4))
        self.active_cat = tk.StringVar(value="All")

        cv = tk.Canvas(left, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(left, orient="vertical", command=cv.yview)
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True, padx=16)
        self.grid_f = tk.Frame(cv, bg=BG)
        cv.create_window((0, 0), window=self.grid_f, anchor="nw")
        self.grid_f.bind("<Configure>", lambda ev: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind_all("<MouseWheel>", lambda ev: cv.yview_scroll(int(-ev.delta / 120), "units"))

        # ---- Current Bill panel: footer pinned at bottom, list scrolls independently ----
        right = tk.Frame(body, width=360, bg=CARD)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        footer = tk.Frame(right, bg=CARD)
        footer.pack(side="bottom", fill="x", padx=14, pady=12)
        self.total_lbl = tk.Label(footer, text="Total: Rs 0", font=("Segoe UI", 14, "bold"), fg=GREEN, bg=CARD)
        self.total_lbl.pack(pady=(4, 8))
        self.name_lbl = tk.Label(footer, anchor="w", bg=CARD, font=("Segoe UI", 9, "bold"))
        self.name_lbl.pack(fill="x")
        self.c_name = tk.StringVar()
        tk.Entry(footer, textvariable=self.c_name, font=("Segoe UI", 10)).pack(fill="x", pady=(0, 6), ipady=3)
        self.phone_lbl = tk.Label(footer, anchor="w", bg=CARD, font=("Segoe UI", 9, "bold"))
        self.phone_lbl.pack(fill="x")
        self.c_phone = tk.StringVar()
        tk.Entry(footer, textvariable=self.c_phone, font=("Segoe UI", 10)).pack(fill="x", pady=(0, 10), ipady=3)
        self.checkout_btn = tk.Button(footer, bg=GREEN, fg="white", font=("Segoe UI", 11, "bold"), bd=0,
                                       pady=8, command=self.open_payment)
        self.checkout_btn.pack(fill="x")

        header_row = tk.Frame(right, bg=CARD)
        header_row.pack(side="top", fill="x", padx=14, pady=(14, 6))
        self.cart_title_lbl = tk.Label(header_row, font=("Segoe UI", 13, "bold"), bg=CARD)
        self.cart_title_lbl.pack(side="left")
        tk.Button(header_row, text="Clear", font=("Segoe UI", 8), bd=0, command=self.cart_clear).pack(side="right")

        list_wrap = tk.Frame(right, bg=CARD)
        list_wrap.pack(side="top", fill="both", expand=True, padx=14)
        self.cart_items_frame_cv = tk.Canvas(list_wrap, bg=CARD, highlightthickness=0)
        cart_sb = ttk.Scrollbar(list_wrap, orient="vertical", command=self.cart_items_frame_cv.yview)
        self.cart_items_frame_cv.configure(yscrollcommand=cart_sb.set)
        cart_sb.pack(side="right", fill="y")
        self.cart_items_frame_cv.pack(side="left", fill="both", expand=True)
        self.cart_items_frame = tk.Frame(self.cart_items_frame_cv, bg=CARD)
        self.cart_items_frame_cv.create_window((0, 0), window=self.cart_items_frame, anchor="nw", width=300)
        self.cart_items_frame.bind("<Configure>",
            lambda ev: self.cart_items_frame_cv.configure(scrollregion=self.cart_items_frame_cv.bbox("all")))

        self.refresh_cart()

    def build_cat_rail(self):
        for w in self.cat_rail.winfo_children():
            w.destroy()
        cats = [("All", "🧺")] + [(n, CAT_ICON.get(n, "🛒")) for n in self.cat_ids]
        for name, icon in cats:
            sel = self.active_cat.get() == name
            cv, inner = make_card(self.cat_rail, 86, 78, r=14,
                                   fill="#fff3e8" if sel else CARD,
                                   outline=ORANGE if sel else "#ebebef")
            cv.pack(side="left", padx=5)
            tk.Label(inner, text=icon, font=("Segoe UI", 20), bg=inner["bg"]).pack(pady=(8, 0))
            tk.Label(inner, text=name, font=("Segoe UI", 8, "bold"), bg=inner["bg"],
                     fg=ORANGE if sel else "#555", wraplength=78, justify="center").pack()
            for w in (cv,) + tuple(inner.winfo_children()):
                w.bind("<Button-1>", lambda e, n=name: self.select_cat(n))
            cv.configure(cursor="hand2")

    def select_cat(self, name):
        self.active_cat.set(name)
        self.build_cat_rail()
        self.refresh_grid()

    def expiry_text(self, exp):
        if not exp:
            return ""
        exp_date = exp if isinstance(exp, date) else datetime.strptime(str(exp), "%Y-%m-%d").date()
        days = (exp_date - date.today()).days
        if days < 0:
            return "⚠ Expired"
        if days == 0:
            return "⚠ Expires today"
        if days <= 7:
            return f"⏰ Expires in {days}d"
        return f"Exp: {exp_date.strftime('%d %b %Y')}"

    def expiry_color(self, exp):
        if not exp:
            return MUTED
        exp_date = exp if isinstance(exp, date) else datetime.strptime(str(exp), "%Y-%m-%d").date()
        days = (exp_date - date.today()).days
        return RED if days <= 7 else MUTED

    def refresh_grid(self):
        for w in self.grid_f.winfo_children():
            w.destroy()
        sql = ("SELECT p.product_id,p.name,p.price,p.stock,p.unit,p.image,p.expiry_date FROM products p "
               "JOIN categories c ON p.category_id=c.category_id WHERE p.name LIKE %s")
        args = [f"%{self.q.get()}%"]
        if self.active_cat.get() != "All":
            sql += " AND c.name=%s"
            args.append(self.active_cat.get())
        CARD_W, CARD_H = 180, 272
        for i, (pid, n, pr, st, un, im, exp) in enumerate(db.run(sql + " ORDER BY p.name", args, True)):
            cv, inner = make_card(self.grid_f, CARD_W, CARD_H, r=16)
            cv.grid(row=i // 5, column=i % 5, padx=7, pady=7)
            tk.Label(inner, image=load_img(im, (92, 92), n), bg=CARD).pack(pady=(10, 4))
            tk.Label(inner, text=n, font=("Segoe UI", 10, "bold"), bg=CARD, wraplength=150).pack()
            tk.Label(inner, text=un, fg=MUTED, bg=CARD, font=("Segoe UI", 8)).pack()
            row = tk.Frame(inner, bg=CARD)
            row.pack(fill="x", pady=(4, 2), padx=10)
            tk.Label(row, text=f"Rs {pr}", font=("Segoe UI", 11, "bold"), fg=GREEN, bg=CARD).pack(side="left")
            if st > 0:
                circle_btn(row, d=28, command=lambda a=(pid, n, float(pr)): self.add(*a)).pack(side="right")
            stock_txt = "Out of stock" if st == 0 else (f"{st} left" if st < 10 else f"{st} in stock")
            tk.Label(inner, text=stock_txt, fg=RED if 0 < st < 10 else MUTED, bg=CARD, font=("Segoe UI", 8)).pack()
            tk.Label(inner, text=self.expiry_text(exp), fg=self.expiry_color(exp), bg=CARD,
                     font=("Segoe UI", 8, "bold" if self.expiry_color(exp) == RED else "normal")).pack()
        n_prod, n_low, sales = db.run(
            "SELECT (SELECT COUNT(*) FROM products),(SELECT COUNT(*) FROM products WHERE stock<10),"
            "(SELECT IFNULL(SUM(total),0) FROM bills WHERE DATE(bill_date)=CURDATE())", fetch=True)[0]
        self.stats.config(text=f"{self.t('products')}: {n_prod}   {self.t('low_stock')}: {n_low}   {self.t('today_sales')}: Rs {sales}")

    def add(self, pid, n, p):
        st = db.run("SELECT stock FROM products WHERE product_id=%s", (pid,), True)[0][0]
        q = self.cart.get(pid, (n, p, 0))[2] + 1
        if q > st:
            return messagebox.showwarning("Stock", f"Only {st} in stock")
        self.cart[pid] = (n, p, q)
        self.refresh_cart()

    def refresh_cart(self):
        for w in self.cart_items_frame.winfo_children():
            w.destroy()
        if not self.cart:
            tk.Label(self.cart_items_frame, text="No items yet.\nClick + on a product to add it.",
                     bg=CARD, fg=MUTED, justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=20)
        for pid, (n, p, q) in self.cart.items():
            row = tk.Frame(self.cart_items_frame, bg=CARD, pady=6)
            row.pack(fill="x")
            info = tk.Frame(row, bg=CARD)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=n, font=("Segoe UI", 9, "bold"), bg=CARD, anchor="w").pack(anchor="w")
            tk.Label(info, text=f"Rs {p} x {q} = Rs {p*q:.0f}", font=("Segoe UI", 8), fg=MUTED, bg=CARD, anchor="w").pack(anchor="w")
            ctr = tk.Frame(row, bg=CARD)
            ctr.pack(side="right")
            tk.Button(ctr, text="−", width=2, bd=0, command=lambda i=pid: self.cart_minus(i)).pack(side="left")
            tk.Label(ctr, text=str(q), width=2, bg=CARD).pack(side="left")
            tk.Button(ctr, text="+", width=2, bd=0, command=lambda i=pid: self.cart_plus(i)).pack(side="left")
            tk.Frame(self.cart_items_frame, bg="#ebebef", height=1).pack(fill="x", pady=2)
        self.total_lbl.config(text=f"Total: Rs {sum(p * q for _, p, q in self.cart.values()):.2f}")

    def cart_plus(self, pid):
        n, p, _ = self.cart[pid]
        self.add(pid, n, p)

    def cart_minus(self, pid):
        n, p, q = self.cart[pid]
        self.cart[pid] = (n, p, q - 1)
        if q - 1 <= 0:
            del self.cart[pid]
        self.refresh_cart()

    def cart_clear(self):
        self.cart.clear()
        self.refresh_cart()

    # ---------------------------------------------------------- PAYMENT
    def open_payment(self):
        if not self.cart:
            return messagebox.showerror("Billing", "Add at least one item first")
        name, phone = self.c_name.get().strip(), self.c_phone.get().strip()
        if not name or not phone.isdigit():
            return messagebox.showerror("Billing", "Enter customer name and a numeric phone number")
        total = sum(p * q for _, p, q in self.cart.values())

        win = tk.Toplevel(self)
        win.title(self.t("pay_title"))
        win.geometry("360x480")
        tk.Label(win, text=self.t("pay_title"), font=("Segoe UI", 13, "bold")).pack(pady=10)
        tk.Label(win, text=f"Amount: Rs {total:.2f}", font=("Segoe UI", 12, "bold"), fg=GREEN).pack()

        qr_frame = tk.Frame(win)
        qr_frame.pack(pady=8)
        mode_var = tk.StringVar(value="")

        def pick(mode):
            mode_var.set(mode)
            for w in qr_frame.winfo_children():
                w.destroy()
            if mode in ("gpay", "phonepe", "paytm"):
                self.show_qr(qr_frame, total)
            confirm_btn.config(state="normal")

        modes = [("gpay", "📲 GPay"), ("phonepe", "📲 PhonePe"), ("paytm", "📲 Paytm"),
                 ("card", "💳 Card"), ("cash", "💵 Cash"), ("khata", self.t("khata_mode"))]
        grid = tk.Frame(win)
        grid.pack(pady=6)
        for i, (m, lbl) in enumerate(modes):
            tk.Button(grid, text=lbl, width=16, command=lambda m=m: pick(m)).grid(row=i // 2, column=i % 2, padx=4, pady=4)

        confirm_btn = tk.Button(win, text=self.t("confirm_pay"), state="disabled", bg=GREEN, fg="white",
                                 font=("Segoe UI", 11, "bold"),
                                 command=lambda: self.finish_checkout(win, name, phone, mode_var.get()))
        confirm_btn.pack(fill="x", padx=16, pady=16)

    def show_qr(self, parent, amount):
        try:
            import qrcode
        except ImportError:
            tk.Label(parent, text="(install the 'qrcode' package to show a real QR:\npip install qrcode[pil])",
                     fg=RED, justify="left").pack()
            return
        upi = f"upi://pay?pa=freshbasket@okaxis&pn=FreshBasket&am={amount:.2f}&cu=INR"
        img = qrcode.make(upi).resize((160, 160))
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(parent, image=photo)
        lbl.image = photo
        lbl.pack()
        tk.Label(parent, text="Customer scans to pay", fg="gray", font=("Segoe UI", 9)).pack()

    def finish_checkout(self, win, name, phone, mode):
        try:
            bid, total = db.checkout(name, phone, self.cart, mode)
        except Exception as e:
            return messagebox.showerror("Checkout failed", str(e))
        win.destroy()
        self.cart.clear()
        self.c_name.set("")
        self.c_phone.set("")
        self.refresh_cart()
        self.refresh_all()
        self.show_receipt(bid, name, phone, mode)

    # ---------------------------------------------------------- RECEIPT
    def build_receipt_text(self, bid):
        h = db.query("SELECT c.name,c.phone,b.bill_date,b.total,b.mode FROM bills b "
                     "JOIN customers c ON b.customer_id=c.customer_id WHERE b.bill_id=%s", (bid,))[1][0]
        items = db.query("SELECT name,qty,price,qty*price FROM bill_items WHERE bill_id=%s", (bid,))[1]
        bn = db.bill_number(bid)
        lines = [f"FRESHBASKET", f"Bill No: {bn}", f"Date: {h[2]}", f"Customer: {h[0]} ({h[1]})",
                 f"Payment: {h[4]}", "-" * 40]
        for n, q, p, a in items:
            lines.append(f"{n[:16]:<16}{q:>3} x {p:>7} = {a:>8}")
        lines += ["-" * 40, f"TOTAL: Rs {h[3]}", "", self.t("thank_you")]
        return "\n".join(lines), h, bn

    def show_receipt(self, bid, name, phone, mode):
        text, h, bn = self.build_receipt_text(bid)
        w = tk.Toplevel(self)
        w.title(f"Bill {bn}")
        tk.Label(w, text=text, font=("Consolas", 10), justify="left").pack(padx=15, pady=15)
        btns = tk.Frame(w)
        btns.pack(pady=(0, 12))
        tk.Button(btns, text=self.t("print_bill"), command=lambda: self.print_bill(bid, text)).pack(side="left", padx=5)
        tk.Button(btns, text=self.t("send_ebill"), command=lambda: self.send_ebill(phone, text)).pack(side="left", padx=5)
        tk.Button(btns, text=self.t("new_bill"), bg=GREEN, fg="white", command=w.destroy).pack(side="left", padx=5)

    def print_bill(self, bid, text):
        path = os.path.join(RECEIPT_DIR, f"bill_{bid}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        try:
            os.startfile(path, "print")  # Windows only
            messagebox.showinfo("Print", "Sent to your default printer.")
        except Exception:
            messagebox.showinfo("Print", f"Saved the receipt to:\n{path}\n(Open it and print manually on non-Windows systems.)")

    def send_ebill(self, phone, text):
        digits = "".join(ch for ch in phone if ch.isdigit())
        if len(digits) == 10:
            digits = "91" + digits  # assume India country code
        url = f"https://wa.me/{digits}?text={webbrowser.urllib.parse.quote(text)}" if digits else \
              f"https://wa.me/?text={webbrowser.urllib.parse.quote(text)}"
        webbrowser.open(url)

    # ============================================================ INVENTORY PAGE
    def build_inv(self, parent):
        form = tk.LabelFrame(parent, text="Product details", padx=8, pady=8, bg=BG)
        form.pack(fill="x", padx=16, pady=12)
        self.f_name, self.f_price, self.f_stock, self.f_unit, self.f_img = (tk.StringVar() for _ in range(5))
        self.f_cat = ttk.Combobox(form, state="readonly", width=20)
        fields = (("Name", tk.Entry(form, textvariable=self.f_name)), ("Category", self.f_cat),
                  ("Price", tk.Entry(form, textvariable=self.f_price)), ("Stock", tk.Entry(form, textvariable=self.f_stock)),
                  ("Unit", tk.Entry(form, textvariable=self.f_unit)), ("Image file", tk.Entry(form, textvariable=self.f_img)))
        for i, (lbl, w) in enumerate(fields):
            tk.Label(form, text=lbl, bg=BG).grid(row=i // 3 * 2, column=i % 3, sticky="w", padx=6)
            w.grid(row=i // 3 * 2 + 1, column=i % 3, padx=6, pady=2, sticky="we")
        tk.Label(form, text="Expiry Date (YYYY-MM-DD) -- leave blank for non-perishables", bg=BG).grid(
            row=4, column=0, columnspan=3, sticky="w", padx=6, pady=(8, 0))
        self.f_expiry = tk.StringVar()
        tk.Entry(form, textvariable=self.f_expiry).grid(row=5, column=0, columnspan=3, padx=6, pady=2, sticky="we")
        btns = tk.Frame(form, bg=BG)
        btns.grid(row=0, column=3, rowspan=4, padx=15)
        for t_, c in (("Add", self.inv_add), ("Update", self.inv_update), ("Delete", self.inv_delete),
                     ("Browse image", self.browse), ("New category", self.new_cat), ("Clear", self.inv_clear)):
            tk.Button(btns, text=t_, width=13, command=c).pack(pady=1)
        self.preview = tk.Label(form, bg=BG)
        self.preview.grid(row=0, column=4, rowspan=4, padx=10)

        sr = tk.Frame(parent, bg=BG)
        sr.pack(fill="x", padx=16)
        tk.Label(sr, text="Search product:", bg=BG).pack(side="left")
        self.iq = tk.StringVar()
        e = tk.Entry(sr, textvariable=self.iq)
        e.pack(side="left", padx=6)
        e.bind("<KeyRelease>", lambda ev: self.refresh_inv())
        self.it = ttk.Treeview(parent)
        self.it.pack(fill="both", expand=True, padx=16, pady=10)
        self.it.bind("<<TreeviewSelect>>", self.inv_select)

    def refresh_inv(self):
        h, rows = db.query("SELECT p.product_id AS id,p.name,c.name AS category,p.price,p.stock,p.unit,p.image,"
                           "p.expiry_date AS expiry FROM products p JOIN categories c ON p.category_id=c.category_id "
                           "WHERE p.name LIKE %s ORDER BY p.product_id", (f"%{self.iq.get()}%",))
        fill(self.it, h, rows)

    def inv_select(self, _=None):
        s = self.it.selection()
        if not s:
            return
        v = self.it.item(s[0])["values"]
        self.sel_id = v[0]
        for var, val in zip((self.f_name, self.f_price, self.f_stock, self.f_unit, self.f_img), (v[1], v[3], v[4], v[5], v[6])):
            var.set(val)
        self.f_cat.set(v[2])
        self.f_expiry.set(v[7] if len(v) > 7 and v[7] else "")
        self.preview.config(image=load_img(str(v[6]), (80, 80), str(v[1])))

    def inv_vals(self):
        try:
            n = self.f_name.get().strip()
            if not n:
                raise ValueError
            exp_str = self.f_expiry.get().strip()
            exp_val = None
            if exp_str:
                datetime.strptime(exp_str, "%Y-%m-%d")  # raises ValueError if the format is wrong
                exp_val = exp_str
            return (n, self.cat_ids[self.f_cat.get()], float(self.f_price.get()), int(self.f_stock.get()),
                    self.f_unit.get().strip(), self.f_img.get().strip(), exp_val)
        except (ValueError, KeyError):
            messagebox.showerror("Error", "Fill all fields correctly (price = number, stock = whole number, "
                                           "expiry date = YYYY-MM-DD or blank)")

    def inv_add(self):
        v = self.inv_vals()
        if v:
            db.run("INSERT INTO products(name,category_id,price,stock,unit,image,expiry_date) VALUES(%s,%s,%s,%s,%s,%s,%s)", v)
            self.refresh_all()
            self.inv_clear()

    def inv_update(self):
        v = self.inv_vals()
        if v and self.sel_id:
            db.run("UPDATE products SET name=%s,category_id=%s,price=%s,stock=%s,unit=%s,image=%s,expiry_date=%s "
                   "WHERE product_id=%s", v + (self.sel_id,))
            self.refresh_all()
        elif not self.sel_id:
            messagebox.showinfo("Update", "Select a product in the table first")

    def inv_delete(self):
        if not self.sel_id:
            return messagebox.showinfo("Delete", "Select a product first")
        if messagebox.askyesno("Confirm", "Delete this product? (Past bills will still show it correctly.)"):
            db.delete_product(self.sel_id)
            self.refresh_all()
            self.inv_clear()

    def inv_clear(self):
        self.sel_id = None
        for v in (self.f_name, self.f_price, self.f_stock, self.f_unit, self.f_img, self.f_expiry):
            v.set("")
        self.f_cat.set("")
        self.preview.config(image="")

    def browse(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if p:
            os.makedirs(IMG_DIR, exist_ok=True)
            dest = os.path.join(IMG_DIR, os.path.basename(p))
            if os.path.abspath(p) != os.path.abspath(dest):
                shutil.copy(p, IMG_DIR)
            self.f_img.set(os.path.basename(p))
            self.preview.config(image=load_img(os.path.basename(p), (80, 80)))

    def new_cat(self):
        n = simpledialog.askstring("New category", "Category name:")
        if n and n.strip():
            try:
                db.run("INSERT INTO categories(name) VALUES(%s)", (n.strip(),))
            except Exception:
                messagebox.showerror("Error", "Category already exists")
            self.load_categories()

    # ============================================================ SALES LOG PAGE
    def build_bills(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", pady=12, padx=16)
        tk.Label(top, text="Search (customer / phone / bill no):", bg=BG).pack(side="left")
        self.bq = tk.StringVar()
        e = tk.Entry(top, textvariable=self.bq)
        e.pack(side="left", padx=6)
        e.bind("<KeyRelease>", lambda ev: self.refresh_bills())
        tk.Button(top, text="View bill", command=self.view_bill).pack(side="left", padx=4)
        tk.Button(top, text=self.t("return_btn"), command=self.open_return_dialog).pack(side="left", padx=4)
        tk.Button(top, text="🗑 Delete Bill", fg=RED, command=self.delete_bill).pack(side="left", padx=4)
        self.bt = ttk.Treeview(parent)
        self.bt.pack(fill="both", expand=True, padx=16, pady=6)

    def refresh_bills(self):
        q = f"%{self.bq.get()}%"
        h, rows = db.query("SELECT b.bill_id,c.name,c.phone,b.bill_date,b.total,b.mode,b.status FROM bills b "
                           "JOIN customers c ON b.customer_id=c.customer_id WHERE c.name LIKE %s OR c.phone LIKE %s "
                           "OR b.bill_id LIKE %s ORDER BY b.bill_id DESC", (q, q, q))
        fill(self.bt, h, rows)

    def sel_bill_id(self):
        s = self.bt.selection()
        return self.bt.item(s[0])["values"][0] if s else None

    def view_bill(self):
        b = self.sel_bill_id()
        if b:
            text, h, bn = self.build_receipt_text(b)
            w = tk.Toplevel(self)
            w.title(f"Bill {bn}")
            tk.Label(w, text=text, font=("Consolas", 10), justify="left").pack(padx=15, pady=15)

    def delete_bill(self):
        b = self.sel_bill_id()
        if not b:
            return messagebox.showinfo("Delete Bill", "Select a bill first")

        kh = db.get_khata_for_bill(b)
        remove_khata = False
        if kh:
            khata_id, amount, paid = kh
            status = "already paid" if paid else "still pending"
            if not messagebox.askyesno(
                "Bill linked to Credit Ledger",
                f"Bill #{b} is in the Credit Ledger (Khata) for Rs {amount:.2f} ({status}).\n\n"
                "Do you want to delete this bill AND its Credit Ledger entry together?\n\n"
                "Click No to cancel -- the bill will be kept."):
                return
            remove_khata = True
        else:
            if not messagebox.askyesno("Confirm",
                                        f"Delete bill #{b} permanently?\n\n"
                                        "Stock will NOT be restored. Any related "
                                        "Returns entries will be kept."):
                return

        try:
            db.delete_bill(b, remove_khata=remove_khata)
        except Exception as e:
            return messagebox.showerror("Delete failed", str(e))

        self.refresh_all()
        messagebox.showinfo("Delete Bill", f"Bill #{b} deleted"
                             + (" along with its Credit Ledger entry." if remove_khata else "."))

    def open_return_dialog(self):
        b = self.sel_bill_id()
        if not b:
            return messagebox.showinfo("Return", "Select a bill first")
        items = db.query("SELECT product_id,name,qty,price FROM bill_items WHERE bill_id=%s", (b,))[1]
        win = tk.Toplevel(self)
        win.title(f"Return item(s) — Bill #{b}")
        win.geometry("360x400")
        tk.Label(win, text=f"Bill #{b}", font=("Segoe UI", 12, "bold")).pack(pady=8)
        vars_ = []
        for pid, name, qty, price in items:
            v = tk.IntVar(value=0)
            row = tk.Frame(win)
            row.pack(fill="x", padx=12, pady=3)
            tk.Checkbutton(row, variable=v).pack(side="left")
            tk.Label(row, text=f"{name} (bought {qty}) @ Rs {price}").pack(side="left")
            vars_.append((pid, name, qty, v))
        tk.Label(win, text="Reason:").pack(anchor="w", padx=12, pady=(10, 0))
        reason = tk.StringVar()
        tk.Entry(win, textvariable=reason).pack(fill="x", padx=12)

        def submit():
            chosen = [(pid, name, qty) for pid, name, qty, v in vars_ if v.get()]
            if not chosen:
                return messagebox.showwarning("Return", "Select at least one item")
            for pid, name, qty in chosen:
                db.create_return(b, pid, name, qty, reason.get() or "Not specified")
            win.destroy()
            self.refresh_all()
            messagebox.showinfo("Return", "Return processed and stock restored.")

        tk.Button(win, text="Submit Return", bg=GREEN, fg="white", command=submit).pack(fill="x", padx=12, pady=14)

    # ============================================================ RETURNS LOG PAGE
    def build_returns(self, parent):
        tk.Label(parent, text="Returns Log", font=("Segoe UI", 13, "bold"), bg=BG).pack(anchor="w", padx=16, pady=12)
        self.rt_tree = ttk.Treeview(parent)
        self.rt_tree.pack(fill="both", expand=True, padx=16, pady=6)

    def refresh_returns(self):
        h, rows = db.query("SELECT return_id,bill_id,name,qty,reason,return_date FROM returns ORDER BY return_id DESC")
        fill(self.rt_tree, h, rows)

    # ============================================================ CREDIT LEDGER PAGE (was "Khata")
    def build_khata(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", padx=16, pady=12)
        self.khata_title_lbl = tk.Label(top, font=("Segoe UI", 13, "bold"), bg=BG)
        self.khata_title_lbl.pack(side="left")
        tk.Button(top, text=self.t("mark_paid"), command=self.khata_mark_paid).pack(side="right")
        self.kh_tree = ttk.Treeview(parent)
        self.kh_tree.pack(fill="both", expand=True, padx=16, pady=6)

    def refresh_khata(self):
        h, rows = db.query("SELECT khata_id,name,phone,amount,created_at,"
                           "CASE WHEN paid THEN 'Paid' ELSE 'Pending' END AS status FROM khata ORDER BY khata_id DESC")
        fill(self.kh_tree, h, rows)

    def khata_mark_paid(self):
        s = self.kh_tree.selection()
        if not s:
            return messagebox.showinfo("Credit Ledger", "Select an entry first")
        kid = self.kh_tree.item(s[0])["values"][0]
        db.mark_khata_paid(kid)
        self.refresh_khata()

    # ============================================================ REPORTS PAGE
    def build_reports(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill="x", padx=16, pady=12)
        for name, sql in REPORTS.items():
            tk.Button(top, text=name, command=lambda s=sql: self.run_report(s)).pack(side="left", padx=3)
        self.sql_lbl = tk.Label(parent, text="Click a report to run its SQL query", fg="gray", bg=BG,
                                wraplength=1200, justify="left")
        self.sql_lbl.pack(anchor="w", padx=16)
        self.rt = ttk.Treeview(parent)
        self.rt.pack(fill="both", expand=True, padx=16, pady=10)

    def run_report(self, sql):
        self.sql_lbl.config(text=sql)
        h, rows = db.query(sql)
        fill(self.rt, h, rows)


if __name__ == "__main__":
    db.setup()
    App().mainloop()
