import io
import pandas as pd
import logging
import psycopg2
from contextlib import closing
from .config import PG_DSN, ROOT

log = logging.getLogger(__name__)

LOAD_ORDER = ["dim_customer", "dim_product", "dim_date", "fact_sales"]

def copy_df(cur, table: str, df: pd.DataFrame):
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)
    cur.copy_expert(f"COPY {table} ({','.join(df.columns)}) FROM STDIN WITH (FORMAT csv)", buf)
    log.info("loaded %-12s %8d rows", table, len(df))

def load(tables: dict[str, pd.DataFrame]):
    # `conn` as a context manager commits on success / rolls back on error (one atomic load)
    with closing(psycopg2.connect(PG_DSN)) as conn, conn, conn.cursor() as cur:
        cur.execute((ROOT / "sql" / "schema.sql").read_text())
        cur.execute("TRUNCATE fact_sales, dim_customer, dim_product, dim_date")
        for name in LOAD_ORDER:
            copy_df(cur, name, tables[name])