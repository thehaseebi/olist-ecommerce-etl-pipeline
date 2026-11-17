import logging 
import time

from .config import STAGING_DIR
from .extract import extract
from .load import load
from .quality import check
from .transform import transform

log = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5s %(name)s | %(message)s")
    start = time.perf_counter()

    tables = transform(extract())
    check(tables)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(STAGING_DIR / f"{name}.parquet", index=False)

    log.info("wrote Parquet files to %s", STAGING_DIR)
    load(tables)
    log.info("pipeline finished in %.1fs", time.perf_counter() - start)



if __name__ == "__main__":
    main()
