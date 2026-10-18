select
    supplier_id,
    supplier_name,
    location as supplier_location,
    category as supplier_category,
    rating,
    lead_time,
    contract_start_date
from {{ source('silver', 'suppliers') }}
