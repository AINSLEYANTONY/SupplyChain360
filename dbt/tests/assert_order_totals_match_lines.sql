{{ config(severity='warn') }}
-- Order totals should equal the sum of their lines.
-- Differences come from lines Spark quarantined (e.g. negative quantity).
select
    o.order_id,
    o.total_amount,
    sum(s.net_revenue) as lines_total
from {{ ref('stg_orders') }} o
join {{ ref('int_sales_lines') }} s on s.order_id = o.order_id
group by o.order_id, o.total_amount
having abs(o.total_amount - sum(s.net_revenue)) > 0.01