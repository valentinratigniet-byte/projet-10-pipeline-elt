{{
  config(
    materialized = 'incremental',
    unique_key = ['order_id', 'product_key'],
    incremental_strategy = 'delete+insert'
  )
}}

-- Table de faits (grain : une ligne de commande).
-- INCRÉMENTAL : à chaque exécution, on ne traite que les commandes plus récentes
-- que le max déjà présent -> pas de recalcul complet, pas de doublons.
select
    oi.order_id,
    o.customer_key,
    oi.product_key,
    to_char(o.order_date, 'YYYYMMDD')::int as date_key,
    o.status,
    oi.quantity,
    oi.unit_price,
    oi.line_amount
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_orders') }} o on o.order_id = oi.order_id

{% if is_incremental() %}
where o.order_id > (select coalesce(max(order_id), 0) from {{ this }})
{% endif %}
