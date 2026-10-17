-- SupplyChain360 star schema (hand-built). Safe to rerun: it rebuilds from scratch.
DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

-- ========== DIMENSIONS ==========

CREATE TABLE dw.dim_customer (
    customer_key      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id       BIGINT NOT NULL UNIQUE,
    customer_name     TEXT,
    city              TEXT,
    state             TEXT,
    country           TEXT,
    customer_segment  TEXT,
    registration_date DATE
);
INSERT INTO dw.dim_customer (customer_id, customer_name, city, state, country, customer_segment, registration_date)
SELECT customer_id, customer_name, city, state, country, customer_segment, registration_date
FROM silver.customers;

CREATE TABLE dw.dim_supplier (
    supplier_key        INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_id         BIGINT NOT NULL UNIQUE,
    supplier_name       TEXT,
    location            TEXT,
    category            TEXT,
    rating              NUMERIC(3,1),
    lead_time           INT,
    contract_start_date DATE
);
INSERT INTO dw.dim_supplier (supplier_id, supplier_name, location, category, rating, lead_time, contract_start_date)
SELECT supplier_id, supplier_name, location, category, rating, lead_time, contract_start_date
FROM silver.suppliers;

CREATE TABLE dw.dim_product (
    product_key   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id    BIGINT NOT NULL UNIQUE,
    product_name  TEXT,
    category      TEXT,
    sub_category  TEXT,
    supplier_key  INT NOT NULL REFERENCES dw.dim_supplier (supplier_key),
    unit_cost     NUMERIC(12,2),
    selling_price NUMERIC(12,2),
    unit_margin   NUMERIC(12,2),
    weight        NUMERIC(8,2)
);
INSERT INTO dw.dim_product (product_id, product_name, category, sub_category, supplier_key,
                            unit_cost, selling_price, unit_margin, weight)
SELECT p.product_id, p.product_name, p.category, p.sub_category, s.supplier_key,
       p.unit_cost, p.selling_price, p.unit_margin, p.weight
FROM silver.products p
JOIN dw.dim_supplier s ON s.supplier_id = p.supplier_id;

CREATE TABLE dw.dim_warehouse (
    warehouse_key       INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warehouse_id        BIGINT NOT NULL UNIQUE,
    warehouse_name      TEXT,
    city                TEXT,
    state               TEXT,
    capacity            INT,
    current_utilization NUMERIC(4,2),
    is_over_utilized    BOOLEAN
);
INSERT INTO dw.dim_warehouse (warehouse_id, warehouse_name, city, state, capacity, current_utilization, is_over_utilized)
SELECT warehouse_id, warehouse_name, city, state, capacity, current_utilization, is_over_utilized
FROM silver.warehouses;

CREATE TABLE dw.dim_carrier (
    carrier_key  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    carrier_name TEXT NOT NULL UNIQUE
);
INSERT INTO dw.dim_carrier (carrier_name)
SELECT DISTINCT carrier FROM silver.shipments WHERE carrier IS NOT NULL ORDER BY carrier;

CREATE TABLE dw.dim_date (
    date_key    INT PRIMARY KEY,          -- e.g. 20250131
    full_date   DATE NOT NULL UNIQUE,
    year        INT,
    quarter     INT,
    month       INT,
    month_name  TEXT,
    day         INT,
    day_of_week INT,                      -- 1 = Monday ... 7 = Sunday
    day_name    TEXT,
    is_weekend  BOOLEAN
);
INSERT INTO dw.dim_date (date_key, full_date, year, quarter, month, month_name, day, day_of_week, day_name, is_weekend)
SELECT to_char(d, 'YYYYMMDD')::int, d::date,
       extract(year FROM d)::int, extract(quarter FROM d)::int, extract(month FROM d)::int,
       to_char(d, 'FMMonth'), extract(day FROM d)::int,
       extract(isodow FROM d)::int, to_char(d, 'FMDay'),
       extract(isodow FROM d) IN (6, 7)
FROM generate_series('2023-01-01'::date, '2026-12-31'::date, interval '1 day') AS g(d);

-- ========== FACTS ==========

-- Grain: one row per order
CREATE TABLE dw.fact_orders (
    order_id       BIGINT PRIMARY KEY,    -- "degenerate dimension": the ID itself is useful
    customer_key   INT NOT NULL REFERENCES dw.dim_customer (customer_key),
    order_date_key INT NOT NULL REFERENCES dw.dim_date (date_key),
    order_status   TEXT,
    payment_method TEXT,
    total_amount   NUMERIC(14,2),
    item_count     INT
);
INSERT INTO dw.fact_orders (order_id, customer_key, order_date_key, order_status, payment_method, total_amount, item_count)
SELECT o.order_id, c.customer_key, to_char(o.order_date, 'YYYYMMDD')::int,
       o.order_status, o.payment_method, o.total_amount, COALESCE(i.item_count, 0)
FROM silver.orders o
JOIN dw.dim_customer c ON c.customer_id = o.customer_id
LEFT JOIN (SELECT order_id, count(*) AS item_count
           FROM silver.order_items GROUP BY order_id) i ON i.order_id = o.order_id;

-- Grain: one row per order line (one product within one order)
CREATE TABLE dw.fact_sales (
    sales_key      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id       BIGINT NOT NULL,
    order_date_key INT NOT NULL REFERENCES dw.dim_date (date_key),
    customer_key   INT NOT NULL REFERENCES dw.dim_customer (customer_key),
    product_key    INT NOT NULL REFERENCES dw.dim_product (product_key),
    supplier_key   INT NOT NULL REFERENCES dw.dim_supplier (supplier_key),
    order_status   TEXT,
    quantity       INT,
    unit_price     NUMERIC(12,2),
    discount       NUMERIC(4,2),
    gross_revenue  NUMERIC(14,2),         -- quantity x unit_price
    net_revenue    NUMERIC(14,2),         -- after discount
    product_cost   NUMERIC(14,2),         -- quantity x unit_cost
    profit         NUMERIC(14,2)          -- net_revenue - product_cost
);
INSERT INTO dw.fact_sales (order_id, order_date_key, customer_key, product_key, supplier_key, order_status,
                           quantity, unit_price, discount, gross_revenue, net_revenue, product_cost, profit)
SELECT oi.order_id, to_char(o.order_date, 'YYYYMMDD')::int, c.customer_key, p.product_key, p.supplier_key,
       o.order_status, oi.quantity, oi.unit_price, oi.discount, oi.gross_revenue, oi.total_price,
       round((oi.quantity * p.unit_cost)::numeric, 2),
       round((oi.total_price - oi.quantity * p.unit_cost)::numeric, 2)
FROM silver.order_items oi
JOIN silver.orders o      ON o.order_id = oi.order_id
JOIN dw.dim_customer c    ON c.customer_id = o.customer_id
JOIN dw.dim_product p     ON p.product_id = oi.product_id;

-- Grain: one row per shipment
CREATE TABLE dw.fact_shipments (
    shipment_id                BIGINT PRIMARY KEY,
    order_id                   BIGINT NOT NULL,
    customer_key               INT NOT NULL REFERENCES dw.dim_customer (customer_key),
    warehouse_key              INT NOT NULL REFERENCES dw.dim_warehouse (warehouse_key),
    carrier_key                INT NOT NULL REFERENCES dw.dim_carrier (carrier_key),
    shipping_date_key          INT NOT NULL REFERENCES dw.dim_date (date_key),
    expected_delivery_date_key INT REFERENCES dw.dim_date (date_key),
    actual_delivery_date_key   INT REFERENCES dw.dim_date (date_key),  -- empty until delivered
    shipping_cost              NUMERIC(12,2),
    delivery_days              INT,
    expected_days              INT,
    is_delayed                 BOOLEAN,
    shipment_status            TEXT
);
INSERT INTO dw.fact_shipments (shipment_id, order_id, customer_key, warehouse_key, carrier_key,
                               shipping_date_key, expected_delivery_date_key, actual_delivery_date_key,
                               shipping_cost, delivery_days, expected_days, is_delayed, shipment_status)
SELECT s.shipment_id, s.order_id, c.customer_key, w.warehouse_key, ca.carrier_key,
       to_char(s.shipping_date, 'YYYYMMDD')::int,
       to_char(s.expected_delivery, 'YYYYMMDD')::int,
       to_char(s.actual_delivery, 'YYYYMMDD')::int,
       s.shipping_cost, s.delivery_days, s.expected_days, s.is_delayed, s.shipment_status
FROM silver.shipments s
JOIN silver.orders o       ON o.order_id = s.order_id
JOIN dw.dim_customer c     ON c.customer_id = o.customer_id
JOIN dw.dim_warehouse w    ON w.warehouse_id = s.warehouse_id
JOIN dw.dim_carrier ca     ON ca.carrier_name = s.carrier;

-- Grain: one row per warehouse + product (a stock snapshot)
CREATE TABLE dw.fact_inventory (
    inventory_key     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    warehouse_key     INT NOT NULL REFERENCES dw.dim_warehouse (warehouse_key),
    product_key       INT NOT NULL REFERENCES dw.dim_product (product_key),
    snapshot_date_key INT NOT NULL REFERENCES dw.dim_date (date_key),
    stock_quantity    INT,
    reorder_level     INT,
    is_low_stock      BOOLEAN,
    stock_gap         INT                 -- reorder_level - stock_quantity (positive = short)
);
INSERT INTO dw.fact_inventory (warehouse_key, product_key, snapshot_date_key,
                               stock_quantity, reorder_level, is_low_stock, stock_gap)
SELECT w.warehouse_key, p.product_key, to_char(i.last_updated, 'YYYYMMDD')::int,
       i.stock_quantity, i.reorder_level, i.is_low_stock, i.reorder_level - i.stock_quantity
FROM silver.inventory i
JOIN dw.dim_warehouse w ON w.warehouse_id = i.warehouse_id
JOIN dw.dim_product p   ON p.product_id = i.product_id;

-- ========== ROW COUNTS ==========
SELECT 'dim_customer' AS table_name, count(*) AS rows FROM dw.dim_customer
UNION ALL SELECT 'dim_product',    count(*) FROM dw.dim_product
UNION ALL SELECT 'dim_supplier',   count(*) FROM dw.dim_supplier
UNION ALL SELECT 'dim_warehouse',  count(*) FROM dw.dim_warehouse
UNION ALL SELECT 'dim_carrier',    count(*) FROM dw.dim_carrier
UNION ALL SELECT 'dim_date',       count(*) FROM dw.dim_date
UNION ALL SELECT 'fact_orders',    count(*) FROM dw.fact_orders
UNION ALL SELECT 'fact_sales',     count(*) FROM dw.fact_sales
UNION ALL SELECT 'fact_shipments', count(*) FROM dw.fact_shipments
UNION ALL SELECT 'fact_inventory', count(*) FROM dw.fact_inventory;