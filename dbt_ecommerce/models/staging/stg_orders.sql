select
    id           as order_id,
    customer_id  as customer_key,
    order_date,
    status
from {{ source('raw', 'orders') }}
