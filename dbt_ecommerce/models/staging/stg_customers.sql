-- Nettoyage/renommage : 1 modèle staging = 1 source.
select
    id                              as customer_key,
    lower(email)                    as email,
    first_name || ' ' || last_name  as full_name,
    country
from {{ source('raw', 'customer') }}
