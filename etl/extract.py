import logging 
import pandas as pd
from .config import RAW_DIR

log = logging.getLogger(__name__)

FILES = {
    "orders": "olist_orders_dataset.csv",
    "items": "olist_order_items_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "categories": "product_category_name_translation.csv"
}

def extract():
    frames = {}
    for name, file in FILES.items():
        path = RAW_DIR / file
        if not path.exists():
            raise FileNotFoundError(f"{path} not found - download the Olist dataset first")
        frames[name] = pd.read_csv(path, encoding="utf-8-sig")
        log.info("extracted %-10s %8d rows", name, len(frames[name]))
    return frames