CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    city TEXT,
    state CHAR(2)
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    product_weight_g NUMERIC
);

CREATE TABLE IF not EXISTS dim_date (
    date_key int primary key,
    full_date date not null,
    year smallint not null,
    quarter smallint not null,
    month smallint not null,
    day smallint not null,
    day_of_week smallint not null,
    is_weekend boolean not null
);

CREATE TABLE IF NOT EXISTS fact_sales (
    order_id TEXT NOT NULL,
    order_item_id INT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES dim_customer,
    product_id TEXT NOT NULL REFERENCES dim_product,
    seller_id TEXT NOT NULL,
    date_key INT NOT NULL REFERENCES dim_date,
    order_status TEXT NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE INDEX IF NOT EXISTS ix_fact_sales_date on fact_sales (date_key);
CREATE INDEX IF NOT EXISTS ix_fact_sales_product on fact_sales (product_id);
CREATE INDEX IF NOT EXISTS ix_fact_sales_customer on fact_sales (customer_id);

