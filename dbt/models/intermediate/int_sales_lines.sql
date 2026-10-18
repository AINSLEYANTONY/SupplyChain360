-- One row per order line, enriched with order and product details.
-- Revenue, cost and profit logic lives here, once.
-- Lines whose parent order was quarantined are dropped by the inner join.
select
    oi.order_id,
    oi.product_id,
    o.customer_id,
    o.order_date,
    o.order_status,
    p.supplier_id,
    oi.quantity,
    oi.unit_price,
    oi.discount,
    oi.gross_revenue,
    oi.total_price                                                    as net_revenue,
    round((oi.quantity * p.unit_cost)::numeric, 2)                    as product_cost,
    round((oi.total_price - oi.quantity * p.unit_cost)::numeric, 2)   as profit
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_orders') }} o   on o.order_id = oi.order_id
join {{ ref('stg_products') }} p on p.product_id = oi.product_id