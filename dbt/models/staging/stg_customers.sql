select
    customer_id,
    customer_name,
    city,
    state,
    country,
    customer_segment,
    registration_date
from {{ source('silver', 'customers') }}
