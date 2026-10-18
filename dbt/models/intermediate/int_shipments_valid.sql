-- Shipments joined to their order (to find the customer).
-- Shipments of quarantined orders are dropped by the inner join.
select
    s.shipment_id,
    s.order_id,
    o.customer_id,
    s.warehouse_id,
    s.carrier,
    s.shipping_date,
    s.expected_delivery_date,
    s.actual_delivery_date,
    s.shipping_cost,
    s.delivery_days,
    s.expected_days,
    s.is_delayed,
    s.shipment_status
from {{ ref('stg_shipments') }} s
join {{ ref('stg_orders') }} o on o.order_id = s.order_id