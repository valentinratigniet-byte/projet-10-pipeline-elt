-- Calendrier généré sur l'amplitude des commandes (une ligne par jour).
with bornes as (
    select min(order_date)::date as d0, max(order_date)::date as d1
    from {{ ref('stg_orders') }}
),
jours as (
    select generate_series(d0, d1, interval '1 day')::date as d from bornes
)
select
    to_char(d, 'YYYYMMDD')::int      as date_key,
    d                                as date,
    extract(year    from d)::int     as annee,
    extract(quarter from d)::int     as trimestre,
    extract(month   from d)::int     as mois_num,
    to_char(d, 'YYYY-MM')            as annee_mois
from jours
