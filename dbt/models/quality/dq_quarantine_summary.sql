-- What was rejected, and why
select
    source_table,
    dq_errors        as failed_rule,
    count(*)         as rejected_rows,
    max(ingest_date) as ingest_date
from {{ source('quarantine', 'rejected_records') }}
group by source_table, dq_errors
order by rejected_rows desc