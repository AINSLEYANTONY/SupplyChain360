-- One row per table for the latest pipeline run.
-- Question answered: did every raw row end up somewhere?
--   raw rows = duplicates removed + rows in Silver + rows in quarantine
-- Silver and quarantine counts come from the real tables, not from Spark's own claims.
with latest_run as (
    select *
    from {{ source('quality', 'run_stats') }}
    where run_date = (select max(run_date) from {{ source('quality', 'run_stats') }})
),

in_silver as (
    select 'suppliers' as source_table, count(*) as rows_in_silver from {{ source('silver', 'suppliers') }}
    union all select 'products',    count(*) from {{ source('silver', 'products') }}
    union all select 'customers',   count(*) from {{ source('silver', 'customers') }}
    union all select 'warehouses',  count(*) from {{ source('silver', 'warehouses') }}
    union all select 'inventory',   count(*) from {{ source('silver', 'inventory') }}
    union all select 'orders',      count(*) from {{ source('silver', 'orders') }}
    union all select 'order_items', count(*) from {{ source('silver', 'order_items') }}
    union all select 'shipments',   count(*) from {{ source('silver', 'shipments') }}
),

in_quarantine as (
    select source_table, count(*) as rows_in_quarantine
    from {{ source('quarantine', 'rejected_records') }}
    group by source_table
)

select
    r.run_date,
    r.source_table,
    r.raw_rows,
    r.duplicates_removed,
    s.rows_in_silver,
    coalesce(q.rows_in_quarantine, 0) as rows_in_quarantine,
    round(100.0 * s.rows_in_silver / nullif(r.raw_rows - r.duplicates_removed, 0), 2) as valid_pct,
    r.raw_rows = r.duplicates_removed + s.rows_in_silver + coalesce(q.rows_in_quarantine, 0) as reconciles
from latest_run r
join in_silver s on s.source_table = r.source_table
left join in_quarantine q on q.source_table = r.source_table