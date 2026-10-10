import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)
OUT = Path("data/sample")
OUT.mkdir(parents=True, exist_ok=True)

def rand_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

CATS = ["Electronics", "Home", "Apparel", "Grocery", "Sports"]
CITIES = [("Mumbai", "Maharashtra"), ("Delhi", "Delhi"), ("Bengaluru", "Karnataka"),
          ("Chennai", "Tamil Nadu"), ("Kolkata", "West Bengal"), ("Pune", "Maharashtra")]

# --- Suppliers (20) ---
suppliers = pd.DataFrame({
    "supplier_id": range(1, 21),
    "supplier_name": [f"Supplier {i}" for i in range(1, 21)],
    "location": np.random.choice(["Mumbai", "Delhi", "Shenzhen", "Berlin", "Dallas"], 20),
    "category": np.random.choice(CATS, 20),
    "rating": np.round(np.random.uniform(2.5, 5.0, 20), 1),
    "lead_time": np.random.randint(3, 45, 20),
    "contract_start_date": [rand_date(date(2018, 1, 1), date(2023, 12, 31)) for _ in range(20)],
})

# --- Products (100) ---
cost = np.round(np.random.uniform(50, 2000, 100), 2)
products = pd.DataFrame({
    "product_id": range(1, 101),
    "product_name": [f"Product {i}" for i in range(1, 101)],
    "category": np.random.choice(CATS, 100),
    "sub_category": np.random.choice(["Basic", "Premium", "Bulk"], 100),
    "supplier_id": np.random.randint(1, 21, 100),
    "unit_cost": cost,
    "selling_price": np.round(cost * np.random.uniform(1.2, 1.8, 100), 2),
    "weight": np.round(np.random.uniform(0.1, 20, 100), 2),
})

# --- Customers (500) ---
loc = [random.choice(CITIES) for _ in range(500)]
customers = pd.DataFrame({
    "customer_id": range(1, 501),
    "customer_name": [f"Customer {i}" for i in range(1, 501)],
    "city": [c for c, _ in loc],
    "state": [s for _, s in loc],
    "country": "India",
    "customer_segment": np.random.choice(["Consumer", "Corporate", "Small Business"], 500, p=[.6, .25, .15]),
    "registration_date": [rand_date(date(2022, 1, 1), date(2024, 6, 30)) for _ in range(500)],
})

# --- Warehouses (6) ---
warehouses = pd.DataFrame({
    "warehouse_id": range(1, 7),
    "warehouse_name": [f"WH-{c}" for c, _ in CITIES],
    "city": [c for c, _ in CITIES],
    "state": [s for _, s in CITIES],
    "capacity": np.random.randint(5000, 20000, 6),
    "current_utilization": np.round(np.random.uniform(0.4, 1.05, 6), 2),
})

# --- Inventory ---
rows = []
for wid in warehouses.warehouse_id:
    for pid in random.sample(range(1, 101), 60):
        reorder = random.randint(20, 100)
        rows.append((wid, pid, random.randint(0, 300), reorder,
                     rand_date(date(2025, 9, 1), date(2025, 10, 9))))
inventory = pd.DataFrame(rows, columns=["warehouse_id", "product_id", "stock_quantity",
                                        "reorder_level", "last_updated"])

# --- Orders, Order Items, Shipments ---
orders, items, ships = [], [], []
carriers = ["BlueDart", "Delhivery", "DTDC", "FedEx"]
price = products.set_index("product_id").selling_price
for oid in range(1, 5001):
    odate = rand_date(date(2024, 1, 1), date(2025, 9, 30))
    status = random.choices(["Delivered", "Shipped", "Cancelled", "Processing"], [.75, .1, .08, .07])[0]
    total = 0
    for pid in random.sample(range(1, 101), random.randint(1, 4)):
        qty, disc = random.randint(1, 5), random.choice([0, 0, 0.05, 0.1])
        tp = round(qty * price[pid] * (1 - disc), 2)
        total += tp
        items.append((oid, pid, qty, price[pid], disc, tp))
    orders.append((oid, random.randint(1, 500), odate, status,
                   random.choice(["Card", "UPI", "COD", "NetBanking"]), round(total, 2), "Address"))
    if status in ("Delivered", "Shipped"):
        ship = odate + timedelta(days=random.randint(1, 3))
        exp = ship + timedelta(days=random.randint(3, 7))
        act = exp + timedelta(days=random.randint(-2, 5)) if status == "Delivered" else None
        ships.append((oid, random.randint(1, 6), random.choice(carriers), ship, exp, act,
                      round(random.uniform(40, 400), 2), status))

orders = pd.DataFrame(orders, columns=["order_id", "customer_id", "order_date", "order_status",
                                       "payment_method", "total_amount", "shipping_address"])
order_items = pd.DataFrame(items, columns=["order_id", "product_id", "quantity", "unit_price",
                                           "discount", "total_price"])
shipments = pd.DataFrame(ships, columns=["order_id", "warehouse_id", "carrier", "shipping_date",
                                         "expected_delivery", "actual_delivery", "shipping_cost",
                                         "shipment_status"])
shipments.insert(0, "shipment_id", range(1, len(shipments) + 1))

# --- Inject deliberate dirty data (for Stage 7 quality checks) ---
orders = pd.concat([orders, orders.sample(20, random_state=1)], ignore_index=True)  # 20 duplicate orders
orders.loc[orders.sample(15, random_state=2).index, "customer_id"] = None  # null customer IDs
bad = shipments[shipments.actual_delivery.notna()].sample(10, random_state=3).index
shipments.loc[bad, "actual_delivery"] = shipments.loc[bad, "shipping_date"] - timedelta(days=2)  # delivered before shipped
order_items.loc[order_items.sample(10, random_state=4).index, "quantity"] = -1  # negative qty

# --- Write files (mix of formats, like real life) ---
suppliers.to_csv(OUT / "suppliers.csv", index=False)
products.to_csv(OUT / "products.csv", index=False)
warehouses.to_csv(OUT / "warehouses.csv", index=False)
inventory.to_csv(OUT / "inventory.csv", index=False)
order_items.to_csv(OUT / "order_items.csv", index=False)
customers.to_json(OUT / "customers.json", orient="records", date_format="iso")
orders.to_json(OUT / "orders.json", orient="records", date_format="iso")
shipments.to_csv(OUT / "shipments.csv", index=False)
print("Done:", {f.name: f.stat().st_size // 1024 for f in OUT.iterdir()}, "KB")