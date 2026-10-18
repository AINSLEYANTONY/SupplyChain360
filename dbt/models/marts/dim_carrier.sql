select distinct
    {{ surrogate_key(['carrier']) }} as carrier_key,
    carrier as carrier_name
from {{ ref('stg_shipments') }}
where carrier is not null
