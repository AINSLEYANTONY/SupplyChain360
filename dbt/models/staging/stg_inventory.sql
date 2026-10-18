select
    warehouse_id,
    product_id,
    stock_quantity,
    reorder_level,
    last_updated as snapshot_date,
    is_low_stock
from {{ source('silver', 'inventory') }}
