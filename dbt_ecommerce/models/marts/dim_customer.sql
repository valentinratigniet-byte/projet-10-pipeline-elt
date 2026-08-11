select customer_key, email, full_name, country
from {{ ref('stg_customers') }}
