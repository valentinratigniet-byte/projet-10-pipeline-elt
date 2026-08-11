select product_key, sku, product_name, category, price, is_active
from {{ ref('stg_products') }}
