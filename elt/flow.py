"""
Orchestration du pipeline ELT avec Prefect.

  extract_load  ->  dbt run  ->  dbt test

- Retries sur chaque étape (résilience aux erreurs transitoires).
- Logs structurés via le logger Prefect.
- Toute étape en échec fait échouer le flow (sortie non nulle) -> l'ordonnanceur
  le voit et peut alerter. Voir README pour la planification.

Lancer :  python elt/flow.py
"""
import os
import subprocess
import sys
from pathlib import Path

from prefect import flow, task, get_run_logger

ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = ROOT / "dbt_ecommerce"
# dbt lit son profil dans ce dossier (pas dans ~/.dbt).
DBT_ENV = {**os.environ, "DBT_PROFILES_DIR": str(DBT_DIR)}


def _run(cmd, cwd=None, env=None):
    """Exécute une commande, relaie la sortie, lève si code de retour non nul."""
    log = get_run_logger()
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if result.stdout:
        log.info(result.stdout.strip()[-3000:])
    if result.returncode != 0:
        log.error((result.stderr or result.stdout).strip()[-3000:])
        raise RuntimeError(f"Échec : {' '.join(cmd)}")


@task(retries=2, retry_delay_seconds=10)
def extract_load():
    _run([sys.executable, str(ROOT / "elt" / "extract_load.py")])


@task(retries=1, retry_delay_seconds=10)
def dbt_run():
    _run([sys.executable, "-m", "dbt.cli.main", "run"], cwd=str(DBT_DIR), env=DBT_ENV)


@task(retries=1, retry_delay_seconds=10)
def dbt_test():
    _run([sys.executable, "-m", "dbt.cli.main", "test"], cwd=str(DBT_DIR), env=DBT_ENV)


@flow(name="elt-ecommerce")
def elt_pipeline():
    extract_load()
    dbt_run()
    dbt_test()


if __name__ == "__main__":
    elt_pipeline()
