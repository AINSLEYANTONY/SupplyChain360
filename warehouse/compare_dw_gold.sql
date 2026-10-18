select 'dim_customer' as model, (select count(*) from dw.dim_customer) as hand_built, (select count(*) from gold.dim_customer) as dbt
union all select 'dim_product',    (select count(*) from dw.dim_product),    (select count(*) from gold.dim_product)
union all select 'dim_supplier',   (select count(*) from dw.dim_supplier),   (select count(*) from gold.dim_supplier)
union all select 'dim_warehouse',  (select count(*) from dw.dim_warehouse),  (select count(*) from gold.dim_warehouse)
union all select 'dim_carrier',    (select count(*) from dw.dim_carrier),    (select count(*) from gold.dim_carrier)
union all select 'dim_date',       (select count(*) from dw.dim_date),       (select count(*) from gold.dim_date)
union all select 'fact_orders',    (select count(*) from dw.fact_orders),    (select count(*) from gold.fact_orders)
union all select 'fact_sales',     (select count(*) from dw.fact_sales),     (select count(*) from gold.fact_sales)
union all select 'fact_shipments', (select count(*) from dw.fact_shipments), (select count(*) from gold.fact_shipments)
union all select 'fact_inventory', (select count(*) from dw.fact_inventory), (select count(*) from gold.fact_inventory)
union all select 'sum net_revenue',  (select round(sum(net_revenue)::numeric, 0) from dw.fact_sales),    (select round(sum(net_revenue)::numeric, 0) from gold.fact_sales)
union all select 'sum profit',       (select round(sum(profit)::numeric, 0) from dw.fact_sales),         (select round(sum(profit)::numeric, 0) from gold.fact_sales)
union all select 'sum shipping_cost',(select round(sum(shipping_cost)::numeric, 0) from dw.fact_shipments),(select round(sum(shipping_cost)::numeric, 0) from gold.fact_shipments);