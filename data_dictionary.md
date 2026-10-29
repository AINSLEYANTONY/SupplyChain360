# Data dictionary

All business tables live in the `gold` schema of the `supplychain_dw` database. Keys named `*_key` are surrogate keys: the md5 hash of the business ID, so the same ID always produces the same key.

## Business definitions

| Term | Definition |
|---|---|
| Net revenue | `quantity × unit_price × (1 − discount)` per order line. Dashboard totals exclude cancelled orders. |
| Profit | Net revenue minus `quantity × unit_cost`. Shipping cost is not allocated to order lines. |
| Delivery days | Actual delivery date minus shipping date. |
| Delayed shipment | Actual delivery date is later than the expected delivery date. Not set until delivered. |
| Low stock | `stock_quantity < reorder_level`. A stockout is `stock_quantity = 0`. |
| Over-utilized warehouse | `current_utilization > 1.0` (above 100% of capacity). |

## Dimensions

**dim_customer** (one row per customer): `customer_key`, `customer_id`, `customer_name`, `city`, `state`, `country`, `customer_segment` (Consumer, Corporate or Small Business), `registration_date`.

**dim_product** (one row per product): `product_key`, `product_id`, `product_name`, `category`, `sub_category`, `supplier_key`, `unit_cost`, `selling_price`, `unit_margin` (price minus cost), `weight`.

**dim_supplier** (one row per supplier): `supplier_key`, `supplier_id`, `supplier_name`, `supplier_location`, `supplier_category`, `rating` (0 to 5), `lead_time` (days), `contract_start_date`.

**dim_warehouse** (one row per warehouse): `warehouse_key`, `warehouse_id`, `warehouse_name`, `city`, `state`, `capacity` (units), `current_utilization` (1.0 = full), `is_over_utilized`.

**dim_carrier** (one row per carrier): `carrier_key`, `carrier_name`.

**dim_date** (one row per day, 2023 to 2026): `date_key` (YYYYMMDD integer), `full_date`, `year`, `quarter`, `month`, `month_name`, `day`, `day_of_week` (1 = Monday), `day_name`, `is_weekend`.

## Facts

**fact_orders** (one row per order): `order_id`, `customer_key`, `order_date_key`, `order_status` (Delivered, Shipped, Processing or Cancelled), `payment_method`, `total_amount`, `item_count`.

**fact_sales** (one row per order line): `sales_key`, `order_id`, `order_date_key`, `customer_key`, `product_key`, `supplier_key`, `order_status`, `quantity`, `unit_price`, `discount`, `gross_revenue` (before discount), `net_revenue`, `product_cost`, `profit`.

**fact_shipments** (one row per shipment): `shipment_id`, `order_id`, `customer_key`, `warehouse_key`, `carrier_key`, `shipping_date_key`, `expected_delivery_date_key`, `actual_delivery_date_key` (empty until delivered), `shipping_cost`, `delivery_days`, `expected_days`, `is_delayed`, `shipment_status`.

**fact_inventory** (one row per warehouse and product): `inventory_key`, `warehouse_key`, `product_key`, `snapshot_date_key`, `stock_quantity`, `reorder_level`, `is_low_stock`, `stock_gap` (reorder level minus stock; positive means short).

## Alerts (schema `alerts`)

**alerts_all**: `alert_type` (low_stock, shipment_delay or supplier_rating), `severity` (critical, high or warning), `entity_type`, `entity`, `message`, `metric_value`, `threshold`, `generated_at`.
Detail tables: `alert_low_stock`, `alert_shipment_delays` and `alert_supplier_performance`. Thresholds are the `vars` in `dbt/dbt_project.yml`.

## Data quality (schemas `quality` and `quarantine`)

| Table | Contents |
|---|---|
| `quarantine.rejected_records` | Every rejected row: `source_table`, `dq_errors` (failed rules), `record_json` (original record), `batch_id`, `ingest_date`. |
| `quality.run_stats` | Per run and table: `raw_rows`, `duplicates_removed`, `silver_rows`, `quarantined_rows`. |
| `quality.dq_scorecard` | Latest run per table, with `valid_pct` and `reconciles` (true when raw = duplicates + silver + quarantine). |
| `quality.dq_quarantine_summary` | Rejected rows per table and failed rule. |
| `quality.pipeline_failures` | One row per Airflow task that failed after all retries. |

## Other layers

`silver.*` holds the cleaned, typed copies of the eight source tables. `staging.stg_*` are one-to-one dbt views over silver, with renames only. `intermediate.int_*` hold joins and the revenue, cost and profit logic.