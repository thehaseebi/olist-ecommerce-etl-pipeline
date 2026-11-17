import logging 
import pandas as pd
log = logging.getLogger(__name__)

def build_dim_customer(customer: pd.DataFrame):
    log.info("Building dimension table for customers")
    return(
        customer[["customer_id", "customer_unique_id", "customer_city", "customer_state"]]
        .drop_duplicates(subset=["customer_id"])
        .rename(columns={"customer_city": "city", "customer_state": "state"})
    )

def build_dim_product(products: pd.DataFrame, categories: pd.DataFrame):
    log.info("Building dimension table for products")
    df = products.merge(categories, how="left", on="product_category_name")
    df['category'] = df['product_category_name_english'].fillna("unknown")
    return df [["product_id", "category", "product_weight_g"]].drop_duplicates('product_id')

def build_dim_date(timestamps: pd.Series):
    log.info("Building dimension table for date")
    days = pd.date_range(timestamps.min().normalize(), timestamps.max().normalize(), freq="D")
    return pd.DataFrame({
        "date_key": days.strftime("%Y%m%d").astype(int),
        "full_date": days.date,
        "year": days.year,
        "quarter": days.quarter,
        "month": days.month,
        "day": days.day,
        "day_of_week": days.dayofweek + 1, # 1 = Monday
        "is_weekend": days.dayofweek.isin([5, 6]).astype(int)
    })

def build_fact_sales(orders: pd.DataFrame, items: pd.DataFrame):
    log.info("Building fact table for sales")
    orders = orders[["order_id", "customer_id", "order_status", "order_purchase_timestamp"]].copy()
    orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])

    df = items.merge(orders, on="order_id", how="inner")
    df = df.drop_duplicates(["order_id", "order_item_id"])
    df = df[df["price"] >= 0].copy()
    df["date_key"] = df["order_purchase_timestamp"].dt.strftime("%Y%m%d").astype(int)
    df["total_amount"] = (df["price"] + df["freight_value"]).round(2)
    return df[[
        "order_id", "order_item_id", "customer_id", "product_id", "seller_id",
        "date_key", "order_status", "price", "freight_value", "total_amount"
    ]].reset_index(drop=True)

def transform(raw: dict[str, pd.DataFrame]):
    log.info("Transforming raw data into dimension and fact tables")
    tables = {
        "dim_customer": build_dim_customer(raw["customers"]),
        "dim_product": build_dim_product(raw["products"], raw["categories"]),
        "dim_date": build_dim_date(pd.to_datetime(raw["orders"]["order_purchase_timestamp"])),
        "fact_sales":build_fact_sales(raw["orders"], raw["items"])
    }

    for name, df in tables.items():
        log.info("transformed %-12s %8d rows", name, len(df))

    return tables


