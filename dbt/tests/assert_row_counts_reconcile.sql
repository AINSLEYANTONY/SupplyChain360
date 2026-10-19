-- Every row must be accounted for. If rows vanish between Bronze and
-- Silver/quarantine, this returns them and the build FAILS (no warning).
select source_table, raw_rows, duplicates_removed, rows_in_silver, rows_in_quarantine
from {{ ref('dq_scorecard') }}
where not reconciles