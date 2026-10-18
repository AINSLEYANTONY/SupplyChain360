select
    order_id,
    product_id,
    quantity,
    unit_price,
    discount,
    total_price,
    gross_revenue
from {{ source('silver', 'order_items') }}
