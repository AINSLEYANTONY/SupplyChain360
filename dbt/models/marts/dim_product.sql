select
    {{ surrogate_key(['product_id']) }} as product_key,
    product_id, product_name, category, sub_category,
    {{ surrogate_key(['supplier_id']) }} as supplier_key,
    unit_cost, selling_price, unit_margin, weight
from {{ ref('stg_products') }}
