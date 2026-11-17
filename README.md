# Olist E-Commerce ETL Pipeline

![CI](https://github.com/thehaseebi/olist-ecommerce-etl-pipeline/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

A batch ETL pipeline that turns **~100k real Brazilian e-commerce orders** ([Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce))
from 5 raw CSV files into a **PostgreSQL star schema** and **Parquet** files, guarded by **data-quality checks**, covered by **unit tests**, and verified by **CI** on every push.

## Architecture

```mermaid
flowchart LR
    A[Raw CSVs<br/>5 Olist files] --> B[Extract<br/>pandas]
    B --> C[Transform<br/>star schema]
    C --> D{Quality gate}
    D -->|pass| E[(Parquet<br/>data/staging)]
    D -->|pass| F[(PostgreSQL 16<br/>Docker)]
    F --> G[SQL analytics]
    D -.->|fail| X[Pipeline stops<br/>nothing loaded]
```

## Data model

Star schema at the grain of **one row per order item** `(order_id, order_item_id)`.

```mermaid
erDiagram
    fact_sales }o--|| dim_customer : customer_id
    fact_sales }o--|| dim_product  : product_id
    fact_sales }o--|| dim_date     : date_key
    fact_sales {
        text order_id PK
        int order_item_id PK
        text customer_id FK
        text product_id FK
        int date_key FK
        text seller_id
        text order_status
        numeric price
        numeric freight_value
        numeric total_amount
    }
    dim_customer {
        text customer_id PK
        text customer_unique_id
        text city
        char state
    }
    dim_product {
        text product_id PK
        text category
        numeric product_weight_g
    }
    dim_date {
        int date_key PK
        date full_date
        smallint year
        smallint quarter
        smallint month
        smallint day
        smallint day_of_week
        boolean is_weekend
    }
```

| Table | Rows |
|---|---:|
| `fact_sales` | 112,650 |
| `dim_customer` | 99,441 |
| `dim_product` | 32,951 |
| `dim_date` | 774 (every day 2016-09-04 → 2018-10-17) |

## Key engineering decisions

- **Idempotent, atomic load.** `TRUNCATE` + `COPY` run inside a single transaction: re-running the pipeline never duplicates data, and a failure mid-load rolls back to the previous good state.
- **Bulk `COPY` instead of row-by-row `INSERT`.** DataFrames are streamed to PostgreSQL through an in-memory CSV buffer.
- **Quality gate before load.** The pipeline refuses to load if the fact grain has duplicates, prices are negative, or any fact row references a missing dimension key (referential integrity).
- **Defence in depth.** The database enforces the same rules again with primary keys, foreign keys and a `CHECK (price >= 0)` constraint.
- **Complete date dimension.** Generated for every calendar day, not just days with sales, so reports show zero-sales days.
- **Parquet staging layer.** Typed, columnar output readable by Spark / DuckDB / Athena; **2.6x smaller** than the source CSVs (42.4 MB → 16.4 MB).
- **Pure, testable transforms.** Each table is built by a small DataFrame-in / DataFrame-out function, unit-tested without a database.

## Insights

From delivered orders (`sql/analytics.sql`), revenue in BRL:

| Question | Answer |
|---|---|
| Peak month | **Nov 2017**: R$ 1.15M, **+53.6%** month-over-month (Black Friday) |
| Top category | **health_beauty**: R$ 1.41M, followed by watches_gifts and bed_bath_table |
| Repeat-customer rate | only **3.05%** of customers ordered more than once, so retention is a clear growth opportunity |

> **Data gotcha:** Olist issues a new `customer_id` for every order. Counting repeat buyers on `customer_id` gives ~0%; the real person is `customer_unique_id`, which is why both are kept in `dim_customer`.

## Project structure

```
├── etl/
│   ├── config.py        # paths + connection string from .env
│   ├── extract.py       # read raw CSVs, log row counts
│   ├── transform.py     # build dimensions + fact table
│   ├── quality.py       # data-quality gate
│   ├── load.py          # atomic bulk load with COPY
│   └── pipeline.py      # entry point
├── sql/
│   ├── schema.sql       # DDL: tables, keys, constraints, indexes
│   └── analytics.sql    # business questions (CTEs, window functions)
├── tests/test_pipeline.py
├── .github/workflows/ci.yml
├── docker-compose.yml
└── requirements.txt
```

## Run it locally

**Prerequisites:** Python 3.10+, Docker Desktop.

```bash
# 1. Start PostgreSQL (exposed on port 5433)
docker compose up -d

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure the connection string
cp .env.example .env               # then set user/password to match docker-compose.yml

# 4. Download the Olist dataset from Kaggle and put these files in data/raw/:
#    olist_orders_dataset.csv, olist_order_items_dataset.csv, olist_customers_dataset.csv,
#    olist_products_dataset.csv, product_category_name_translation.csv

# 5. Run the pipeline and the tests
python -m etl.pipeline
python -m pytest -q
```

Explore the results:

```bash
docker exec -i ecommerce_pg psql -U ecom_pg_admin -d ecommerce < sql/analytics.sql
```

## What I would do next

- **Incremental loads** using a watermark on `order_purchase_timestamp` and `INSERT ... ON CONFLICT` upserts
- **Orchestration** with Airflow or Prefect for scheduled runs
- **dbt models** for the transformation layer, with built-in tests and lineage
- **Partitioned Parquet on S3** and Spark for scale beyond a single machine
