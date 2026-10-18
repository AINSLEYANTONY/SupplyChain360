select
    {{ surrogate_key(['supplier_id']) }} as supplier_key,
    supplier_id, supplier_name, supplier_location, supplier_category,
    rating, lead_time, contract_start_date
from {{ ref('stg_suppliers') }}
