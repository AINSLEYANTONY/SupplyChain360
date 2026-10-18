-- Grain: one row per order
with items as (
    select order_id, count(*) as item_count
    from {{ ref('stg_order_items') }}
    group by order_id
)
select
    o.order_id,
    {{ surrogate_key(['o.customer_id']) }}               as customer_key,
    cast(to_char(o.order_date, 'YYYYMMDD') as integer)   as order_date_key,
    o.order_status,
    o.payment_method,
    o.total_amount,
    coalesce(i.item_count, 0)                            as item_count
from {{ ref('stg_orders') }} o
left join items i on i.order_id = o.order_id