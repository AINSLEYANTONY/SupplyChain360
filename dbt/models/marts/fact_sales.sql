-- Grain: one row per order line (one product within one order)
select
    {{ surrogate_key(['order_id', 'product_id']) }}      as sales_key,
    order_id,
    cast(to_char(order_date, 'YYYYMMDD') as integer)     as order_date_key,
    {{ surrogate_key(['customer_id']) }}                 as customer_key,
    {{ surrogate_key(['product_id']) }}                  as product_key,
    {{ surrogate_key(['supplier_id']) }}                 as supplier_key,
    order_status,
    quantity,
    unit_price,
    discount,
    gross_revenue,
    net_revenue,
    product_cost,
    profit
from {{ ref('int_sales_lines') }}