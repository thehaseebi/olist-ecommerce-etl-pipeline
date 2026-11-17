import pandas as pd

def check(table: dict[str, pd.DataFrame]):
    fact = table["fact_sales"]
    errors = []

    if fact.empty:
        errors.append("fact_sales is empty")
    if fact.duplicated(["order_id", "order_item_id"]).any():
        errors.append("duplicate rows at fact grain (order_id, order_item_id)")
    if (fact["price"] < 0).any():
        errors.append("negative prices")
    for dim, key in [("dim_customer", "customer_id"), ("dim_product", "product_id"), ("dim_date", "date_key")]:
        orphans = int((~fact[key].isin(table[dim][key])).sum())
        if orphans:
            errors.append(f"{orphans} fact rows reference unknown {key}")

    if errors:
        raise ValueError("Data quality checks failed: " + "; ".join(errors))

    