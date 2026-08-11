-- Produit + catégorie dénormalisée (jointure raw.product x raw.category).
select
    p.id            as product_key,
    p.sku,
    p.name          as product_name,
    c.name          as category,
    p.price,
    p.is_active
from {{ source('raw', 'product') }} p
join {{ source('raw', 'category') }} c on c.id = p.category_id
