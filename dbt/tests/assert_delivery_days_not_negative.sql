-- Business rule: nothing is delivered before it ships.
select shipment_id, delivery_days
from {{ ref('fact_shipments') }}
where delivery_days < 0