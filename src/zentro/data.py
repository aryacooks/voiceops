from functools import lru_cache
import pandas as pd
from .config import DATASET_DIR
@lru_cache(maxsize=12)
def table(name):
    return pd.read_csv(DATASET_DIR / 'data' / f'{name}.csv', dtype=str, keep_default_na=False)
def catalog_lookup(sku):
    rows = table('products')
    return rows[rows.sku.str.upper() == sku.upper()].to_dict('records')
def is_pincode_serviceable(pincode):
    rows = table('pincodes')
    found = rows[rows.pincode == str(pincode)].to_dict('records')
    return found[0] if found else {'found': False, 'pincode': str(pincode)}
