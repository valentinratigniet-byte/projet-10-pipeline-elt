"""
Simule une source qui évolue : ajoute de nouvelles commandes datées maintenant
dans la base opérationnelle (public), pour donner de la matière au chargement
incrémental. À rejouer avant le pipeline pour voir l'incrément fonctionner.

Usage : python elt/generate_new_orders.py [nb_commandes=200]
"""
import os
import random
import sys

import psycopg2

DSN = os.environ.get("DATABASE_URL",
                     "postgresql://portfolio:portfolio@127.0.0.1:5433/ecommerce")
STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]


def main(n: int = 200) -> None:
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    cur.execute("SELECT array_agg(id) FROM customer;")
    customer_ids = cur.fetchone()[0]
    cur.execute("SELECT id, price FROM product;")
    rows = cur.fetchall()
    product_ids = [r[0] for r in rows]
    price = {r[0]: r[1] for r in rows}

    created, lines = 0, 0
    for _ in range(n):
        cid = random.choice(customer_ids)
        status = random.choices(STATUSES, weights=[1, 3, 3, 6, 1])[0]
        cur.execute(
            "INSERT INTO orders (customer_id, order_date, status) "
            "VALUES (%s, now(), %s) RETURNING id;",
            (cid, status),
        )
        oid = cur.fetchone()[0]
        created += 1
        for pid in random.sample(product_ids, k=random.randint(1, 5)):
            cur.execute(
                "INSERT INTO order_item (order_id, product_id, quantity, unit_price) "
                "VALUES (%s, %s, %s, %s);",
                (oid, pid, random.randint(1, 4), price[pid]),
            )
            lines += 1

    conn.commit()
    print(f"Source simulée - +{created} commandes, +{lines} lignes ajoutées à public")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200)
