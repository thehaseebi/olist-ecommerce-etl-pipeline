import pandas as pd
import pytest

from etl.quality import check
from etl.transform import build_dim_product, transform


def raw_sample():
    return {
        "orders": pd.DataFrame({
            "order_id": ["o1", "o2"],
            "customer_id": ["c1", "c2"],
            "order_status": ["delivered", "shipped"],
            "order_purchase_timestamp": ["2018-01-05 10:00:00", "2018-01-07 18:30:00"],
        }),
        "items": pd.DataFrame({
            "order_id": ["o1", "o1", "o2"],
            "order_item_id": [1, 2, 1],
            "product_id": ["p1", "p2", "p1"],
            "seller_id": ["s1", "s1", "s2"],
            "price": [10.0, 20.0, 5.5],
            "freight_value": [2.5, 0.0, 1.25],
        }),
        "customers": pd.DataFrame({
            "customer_id": ["c1", "c2"],
            "customer_unique_id": ["u1", "u1"],
            "customer_city": ["sao paulo", "rio de janeiro"],
            "customer_state": ["SP", "RJ"],
        }),
        "products": pd.DataFrame({
            "product_id": ["p1", "p2"],
            "product_category_name": ["beleza_saude", None],
            "product_weight_g": [500, 1200],
        }),
        "categories": pd.DataFrame({
            "product_category_name": ["beleza_saude"],
            "product_category_name_english": ["health_beauty"],
        }),
    }


def test_fact_has_correct_amounts_and_date_keys():
    fact = transform(raw_sample())["fact_sales"]
    assert len(fact) == 3
    assert fact["total_amount"].tolist() == [12.5, 20.0, 6.75]
    assert fact["date_key"].tolist() == [20180105, 20180105, 20180107]


def test_missing_category_becomes_unknown():
    raw = raw_sample()
    dim = build_dim_product(raw["products"], raw["categories"]).set_index("product_id")
    assert dim.loc["p1", "category"] == "health_beauty"
    assert dim.loc["p2", "category"] == "unknown"


def test_dim_date_covers_every_day_and_flags_weekends():
    dim = transform(raw_sample())["dim_date"].set_index("date_key")
    assert list(dim.index) == [20180105, 20180106, 20180107]
    assert dim.loc[20180106, "is_weekend"]          # Saturday
    assert not dim.loc[20180105, "is_weekend"]      # Friday


def test_clean_data_passes_quality_checks():
    check(transform(raw_sample()))


def test_quality_check_catches_orphan_product():
    tables = transform(raw_sample())
    tables["dim_product"] = tables["dim_product"].iloc[:1]   # drop p2
    with pytest.raises(ValueError, match="unknown product_id"):
        check(tables)
