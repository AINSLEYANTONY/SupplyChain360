-- Rule: delivery_days > expected_days (minimum delay set in dbt_project.yml)
select
    s.shipment_id,
    s.order_id,
    c.carrier_name,
    w.warehouse_name,
    s.expected_days,
    s.delivery_days,
    s.delivery_days - s.expected_days as days_late,
    s.shipping_cost,
    case when s.delivery_days - s.expected_days >= 3 then 'high' else 'warning' end as severity
from {{ ref('fact_shipments') }} s
join {{ ref('dim_carrier') }} c   on c.carrier_key   = s.carrier_key
join {{ ref('dim_warehouse') }} w on w.warehouse_key = s.warehouse_key
where s.delivery_days - s.expected_days >= {{ var('shipment_delay_min_days') }}