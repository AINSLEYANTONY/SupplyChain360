select
    product_id,
    product_name,
    category,
    sub_category,
    supplier_id,
    unit_cost,
    selling_price,
    unit_margin,
    weight
from {{ source('silver', 'products') }}
