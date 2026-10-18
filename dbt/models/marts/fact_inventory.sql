-- Grain: one row per warehouse + product (a stock snapshot)
select
    {{ surrogate_key(['warehouse_id', 'product_id']) }}               as inventory_key,
    {{ surrogate_key(['warehouse_id']) }}                             as warehouse_key,
    {{ surrogate_key(['product_id']) }}                               as product_key,
    cast(to_char(snapshot_date, 'YYYYMMDD') as integer)               as snapshot_date_key,
    stock_quantity,
    reorder_level,
    is_low_stock,
    reorder_level - stock_quantity                                    as stock_gap
from {{ ref('stg_inventory') }}