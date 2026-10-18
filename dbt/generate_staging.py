from pathlib import Path

OUT = Path("dbt/models/staging")
OUT.mkdir(parents=True, exist_ok=True)

TABLES = {
    "suppliers": ["supplier_id", "supplier_name", "location as supplier_location",
                  "category as supplier_category", "rating", "lead_time", "contract_start_date"],
    "products": ["product_id", "product_name", "category", "sub_category", "supplier_id",
                 "unit_cost", "selling_price", "unit_margin", "weight"],
    "customers": ["customer_id", "customer_name", "city", "state", "country",
                  "customer_segment", "registration_date"],
    "warehouses": ["warehouse_id", "warehouse_name", "city", "state", "capacity",
                   "current_utilization", "is_over_utilized"],
    "inventory": ["warehouse_id", "product_id", "stock_quantity", "reorder_level",
                  "last_updated as snapshot_date", "is_low_stock"],
    "orders": ["order_id", "customer_id", "order_date", "order_status",
               "payment_method", "total_amount"],
    "order_items": ["order_id", "product_id", "quantity", "unit_price", "discount",
                    "total_price", "gross_revenue"],
    "shipments": ["shipment_id", "order_id", "warehouse_id", "carrier", "shipping_date",
                  "expected_delivery as expected_delivery_date",
                  "actual_delivery as actual_delivery_date", "shipping_cost",
                  "shipment_status", "delivery_days", "expected_days", "is_delayed"],
}

for name, cols in TABLES.items():
    body = ",\n    ".join(cols)
    sql = f"select\n    {body}\nfrom {{{{ source('silver', '{name}') }}}}\n"
    (OUT / f"stg_{name}.sql").write_text(sql, encoding="utf-8")
    print("wrote", f"stg_{name}.sql")