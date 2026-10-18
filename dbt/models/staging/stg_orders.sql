select
    order_id,
    customer_id,
    order_date,
    order_status,
    payment_method,
    total_amount
from {{ source('silver', 'orders') }}
