select
    {{ surrogate_key(['customer_id']) }} as customer_key,
    customer_id, customer_name, city, state, country, customer_segment, registration_date
from {{ ref('stg_customers') }}
