"""
config.py keeps paths and the connection string in one place. The connection string comes from the
environment (.env)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
STAGING_DIR = ROOT / "data" / "staging"
PG_DSN = os.getenv("PG_DSN", "postgresql://ecom_pg_admin:ecom_pg_admin@localhost:5433/ecommerce")

