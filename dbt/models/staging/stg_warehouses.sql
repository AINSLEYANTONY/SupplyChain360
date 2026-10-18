select
    warehouse_id,
    warehouse_name,
    city,
    state,
    capacity,
    current_utilization,
    is_over_utilized
from {{ source('silver', 'warehouses') }}
