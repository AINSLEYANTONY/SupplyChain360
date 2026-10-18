from pathlib import Path

OUT = Path("dbt/models/marts")
OUT.mkdir(parents=True, exist_ok=True)

DIMS = {
    "dim_customer": """select
    {{ surrogate_key(['customer_id']) }} as customer_key,
    customer_id, customer_name, city, state, country, customer_segment, registration_date
from {{ ref('stg_customers') }}
""",
    "dim_supplier": """select
    {{ surrogate_key(['supplier_id']) }} as supplier_key,
    supplier_id, supplier_name, supplier_location, supplier_category,
    rating, lead_time, contract_start_date
from {{ ref('stg_suppliers') }}
""",
    "dim_product": """select
    {{ surrogate_key(['product_id']) }} as product_key,
    product_id, product_name, category, sub_category,
    {{ surrogate_key(['supplier_id']) }} as supplier_key,
    unit_cost, selling_price, unit_margin, weight
from {{ ref('stg_products') }}
""",
    "dim_warehouse": """select
    {{ surrogate_key(['warehouse_id']) }} as warehouse_key,
    warehouse_id, warehouse_name, city, state, capacity,
    current_utilization, is_over_utilized
from {{ ref('stg_warehouses') }}
""",
    "dim_carrier": """select distinct
    {{ surrogate_key(['carrier']) }} as carrier_key,
    carrier as carrier_name
from {{ ref('stg_shipments') }}
where carrier is not null
""",
    "dim_date": """select
    cast(to_char(d, 'YYYYMMDD') as integer)  as date_key,
    cast(d as date)                          as full_date,
    extract(year from d)::int                as year,
    extract(quarter from d)::int             as quarter,
    extract(month from d)::int               as month,
    to_char(d, 'FMMonth')                    as month_name,
    extract(day from d)::int                 as day,
    extract(isodow from d)::int              as day_of_week,
    to_char(d, 'FMDay')                      as day_name,
    extract(isodow from d) in (6, 7)         as is_weekend
from generate_series('2023-01-01'::date, '2026-12-31'::date, interval '1 day') as g(d)
""",
}

for name, sql in DIMS.items():
    (OUT / f"{name}.sql").write_text(sql, encoding="utf-8")
    print("wrote", f"{name}.sql")