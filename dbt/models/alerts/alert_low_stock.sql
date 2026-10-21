-- Rule: stock_quantity < reorder_level
select
    w.warehouse_name,
    p.product_id,
    p.product_name,
    p.category,
    f.stock_quantity,
    f.reorder_level,
    f.stock_gap,
    case
        when f.stock_quantity = 0 then 'critical'                      -- stockout
        when f.stock_quantity < 0.5 * f.reorder_level then 'high'
        else 'warning'
    end as severity
from {{ ref('fact_inventory') }} f
join {{ ref('dim_warehouse') }} w on w.warehouse_key = f.warehouse_key
join {{ ref('dim_product') }} p   on p.product_key   = f.product_key
where f.stock_quantity < f.reorder_level