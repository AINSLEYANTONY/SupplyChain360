select
    'low_stock'                                                   as alert_type,
    severity,
    'inventory'                                                   as entity_type,
    warehouse_name || ' / ' || product_name                       as entity,
    'Stock ' || stock_quantity || ' is below reorder level ' || reorder_level as message,
    cast(stock_quantity as numeric)                               as metric_value,
    cast(reorder_level as numeric)                                as threshold,
    current_timestamp                                             as generated_at
from {{ ref('alert_low_stock') }}

union all

select
    'shipment_delay',
    severity,
    'shipment',
    'Shipment ' || shipment_id || ' (' || carrier_name || ')',
    'Delivered ' || days_late || ' day(s) late',
    cast(days_late as numeric),
    cast({{ var('shipment_delay_min_days') }} as numeric),
    current_timestamp
from {{ ref('alert_shipment_delays') }}

union all

select
    'supplier_rating',
    severity,
    'supplier',
    supplier_name,
    'Rating ' || rating || ' is below ' || threshold,
    cast(rating as numeric),
    cast(threshold as numeric),
    current_timestamp
from {{ ref('alert_supplier_performance') }}