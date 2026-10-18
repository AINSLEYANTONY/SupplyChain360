select
    shipment_id,
    order_id,
    warehouse_id,
    carrier,
    shipping_date,
    expected_delivery as expected_delivery_date,
    actual_delivery as actual_delivery_date,
    shipping_cost,
    shipment_status,
    delivery_days,
    expected_days,
    is_delayed
from {{ source('silver', 'shipments') }}
