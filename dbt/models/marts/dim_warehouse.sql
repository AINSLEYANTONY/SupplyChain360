select
    {{ surrogate_key(['warehouse_id']) }} as warehouse_key,
    warehouse_id, warehouse_name, city, state, capacity,
    current_utilization, is_over_utilized
from {{ ref('stg_warehouses') }}
