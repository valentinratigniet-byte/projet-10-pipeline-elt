# Projet 10 — Pipeline ELT automatisé PostgreSQL → Power BI

> **Un dashboard n'a de valeur que si ses données sont fraîches, sans intervention
> manuelle.** Ce pipeline ingère une source qui évolue, la transforme en modèle en
> étoile avec **dbt**, en **chargement incrémental**, orchestré par **Prefect** et
> testé automatiquement — la version industrialisée de la chaîne construite à la main
> aux [Projets 07→09](https://github.com/valentinratigniet-byte).

## 🧱 Architecture (ELT medallion)

```
public (OLTP)  ──EL incrémental──▶  raw  ──dbt──▶  staging  ──dbt──▶  marts  ──▶  Power BI
   source                          brut          vues stg_*        étoile fct_/dim_
```

Détail et diagramme : **[docs/pipeline.md](docs/pipeline.md)**.

| Couche | Rôle | Écrit par |
|---|---|---|
| `raw` | copie brute (jamais transformée) | `elt/extract_load.py` |
| `staging` | nettoyage/renommage, 1 vue par source | dbt (`stg_*`) |
| `marts` | modèle en étoile consommé par Power BI | dbt (`fct_sales`, `dim_*`) |

## ✨ Ce que le projet démontre

- **Pattern ELT** : on charge le brut, puis on transforme **dans** l'entrepôt (SQL/dbt).
- **Chargement incrémental** : watermark côté EL + modèle dbt incrémental → pas de
  doublon, pas de recalcul complet.
- **Tests de données** (dbt) : unicité des clés, `not_null`, intégrité référentielle.
- **Orchestration** (Prefect) : retries, logs, échec propre → alertable.

## 🚀 Rejouer le pipeline

Prérequis : la base du **Projet 07** lancée (Docker, port 5433) + **Python ≥ 3.11**
(environnement virtuel recommandé).

```bash
python -m venv .venv && .venv/Scripts/activate    # Windows (Linux/macOS : source .venv/bin/activate)
pip install -r requirements.txt

# 1. (optionnel) simuler des ventes fraîches dans la source
python elt/generate_new_orders.py 300

# 2. lancer tout le pipeline orchestré : EL -> dbt run -> dbt test
python elt/flow.py
```

Ou étape par étape :

```bash
python elt/extract_load.py                       # public -> raw (incrémental)
cd dbt_ecommerce
set DBT_PROFILES_DIR=%CD%                         # Windows (bash : export DBT_PROFILES_DIR=$PWD)
python -m dbt.cli.main run                        # raw -> staging -> marts
python -m dbt.cli.main test                       # tests de qualité
```

**Voir l'incrément fonctionner** : relancer l'étape 1 puis l'étape 2 → seules les
nouvelles commandes traversent le pipeline (le log affiche `+N commandes`).

## ✅ Validation (pipeline exécuté en vrai)

Flow Prefect complet exécuté de bout en bout (`python elt/flow.py`) :

```
✅ extract_load  → EL OK (watermark, charge uniquement le nouveau)
✅ dbt run       → 4 vues staging + 3 dimensions + fct_sales · PASS=8
✅ dbt test      → 24 tests de qualité · PASS=24  ERROR=0
   Flow 'elt-ecommerce' — Completed
```

- **Modèle en étoile** : `fct_sales` 121 017 lignes, `dim_customer` 5 000,
  `dim_product` 2 000, `dim_date` 733 — construits par dbt.
- **Tests dbt** (24) : unicité des clés, `not_null`, intégrité référentielle → tous verts.
- **Incrémental via dbt** : après +100 ventes, `dbt run` affiche
  `incremental model marts.fct_sales … INSERT 0 314` et la table passe de
  121 017 à **121 331** (= +314) — dbt **ajoute** seulement le nouveau, sans rebuild.

> Testé avec dbt-core 1.12 (dbt-postgres) sur Python 3.12 dans un venv.

## 🔌 Brancher Power BI

Le rapport (Projet 09) pointe sur le schéma **`marts`** au lieu des CSV :
connecteur PostgreSQL → `localhost:5433`, base `ecommerce`, tables
`marts.fct_sales`, `marts.dim_customer`, `marts.dim_product`, `marts.dim_date`.
Un rafraîchissement Power BI relit les marts fraîchement reconstruits.

## 🗂️ Structure

```
projet-10-pipeline-elt/
├── README.md
├── requirements.txt
├── elt/
│   ├── generate_new_orders.py   ← simule une source qui évolue
│   ├── extract_load.py          ← EL incrémental (public -> raw, watermark)
│   └── flow.py                  ← orchestration Prefect (EL -> dbt run -> dbt test)
├── dbt_ecommerce/               ← projet dbt (transformations + tests)
│   ├── dbt_project.yml · profiles.yml
│   ├── macros/generate_schema_name.sql
│   └── models/
│       ├── staging/  (stg_* + sources + tests)
│       └── marts/    (fct_sales incrémental, dim_*, tests)
└── docs/pipeline.md             ← schéma & explication du pipeline
```

---

*Projet 10 du [Portfolio Data](../). Industrialise la chaîne 07→09. Brique suivante :
Projet 11 — gouvernance & qualité (dictionnaire + lignage de l'entrepôt).*
