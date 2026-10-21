-- Rule: supplier rating below the threshold set in dbt_project.yml
select
    supplier_id,
    supplier_name,
    supplier_location,
    supplier_category,
    rating,
    lead_time,
    {{ var('supplier_rating_threshold') }} as threshold,
    case when rating < 3.0 then 'high' else 'warning' end as severity
from {{ ref('dim_supplier') }}
where rating < {{ var('supplier_rating_threshold') }}