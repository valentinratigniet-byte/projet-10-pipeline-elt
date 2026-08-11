"""
Extraction + Chargement (le "EL" de ELT) vers la couche `raw`.

- Dimensions (customer, category, product) : rechargées en entier (petites tables).
- Faits (orders, order_item) : chargement INCRÉMENTAL par watermark
  (on ne charge que les commandes dont l'id dépasse le max déjà en raw).

Source et entrepôt sont ici le même PostgreSQL (schémas public -> raw) pour rester
reproductible ; en production la source serait un système distinct (d'où l'étape Python).
"""
import os
import psycopg2

DSN = os.environ.get("DATABASE_URL",
                     "postgresql://portfolio:portfolio@127.0.0.1:5433/ecommerce")

RAW_DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.customer   (id bigint PRIMARY KEY, email text, first_name text, last_name text, country text, created_at timestamptz);
CREATE TABLE IF NOT EXISTS raw.category   (id int PRIMARY KEY, name text, parent_id int);
CREATE TABLE IF NOT EXISTS raw.product    (id bigint PRIMARY KEY, sku text, name text, category_id int, price numeric(10,2), is_active boolean, created_at timestamptz);
CREATE TABLE IF NOT EXISTS raw.orders     (id bigint PRIMARY KEY, customer_id bigint, order_date timestamptz, status text);
CREATE TABLE IF NOT EXISTS raw.order_item (order_id bigint, product_id bigint, quantity int, unit_price numeric(10,2), PRIMARY KEY (order_id, product_id));
"""

DIMS = {
    "customer": "id, email, first_name, last_name, country, created_at",
    "category": "id, name, parent_id",
    "product":  "id, sku, name, category_id, price, is_active, created_at",
}


def main() -> None:
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute(RAW_DDL)

    # --- Dimensions : reload complet (petit volume) -----------------------
    for table, cols in DIMS.items():
        cur.execute(f"TRUNCATE raw.{table};")
        cur.execute(f"INSERT INTO raw.{table} ({cols}) SELECT {cols} FROM public.{table};")

    # --- Faits : incrémental par watermark --------------------------------
    cur.execute("SELECT coalesce(max(id), 0) FROM raw.orders;")
    watermark = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO raw.orders (id, customer_id, order_date, status) "
        "SELECT id, customer_id, order_date, status FROM public.orders WHERE id > %s;",
        (watermark,),
    )
    n_orders = cur.rowcount

    cur.execute(
        "INSERT INTO raw.order_item (order_id, product_id, quantity, unit_price) "
        "SELECT oi.order_id, oi.product_id, oi.quantity, oi.unit_price "
        "FROM public.order_item oi JOIN public.orders o ON o.id = oi.order_id "
        "WHERE o.id > %s "
        "ON CONFLICT (order_id, product_id) DO NOTHING;",
        (watermark,),
    )
    n_items = cur.rowcount

    conn.commit()
    print(f"EL OK - watermark={watermark} | +{n_orders} commandes, +{n_items} lignes chargées dans raw")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
