-- Grain: one row per shipment
select
    shipment_id,
    order_id,
    {{ surrogate_key(['customer_id']) }}                              as customer_key,
    {{ surrogate_key(['warehouse_id']) }}                             as warehouse_key,
    {{ surrogate_key(['carrier']) }}                                  as carrier_key,
    cast(to_char(shipping_date, 'YYYYMMDD') as integer)               as shipping_date_key,
    cast(to_char(expected_delivery_date, 'YYYYMMDD') as integer)      as expected_delivery_date_key,
    cast(to_char(actual_delivery_date, 'YYYYMMDD') as integer)        as actual_delivery_date_key,
    shipping_cost,
    delivery_days,
    expected_days,
    is_delayed,
    shipment_status
from {{ ref('int_shipments_valid') }}