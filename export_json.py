"""
Export du data warehouse SQLite vers un JSON portable pour Grafana.

Lit data/warehouse.db (schéma en étoile) et produit data/warehouse.json
avec une vue aplatie, une ligne par (ville, datetime) :

    fact_qualite_air JOIN dim_ville ON ville  JOIN dim_temps ON datetime

Champs produits :
    datetime, ville, aqi, pm10, pm2_5, co, no2,
    latitude, longitude, date, annee, mois, jour, heure

Ce fichier est ensuite servi par GitHub (URL raw) et interrogé par le
datasource Grafana "Infinity". Il est régénéré à chaque exécution du
workflow horaire, donc les dashboards restent à jour.

Usage :
    python export_json.py
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/warehouse.db")
OUT_PATH = Path("data/warehouse.json")

# Requête : jointure du schéma en étoile
QUERY = """
SELECT
    f.datetime,
    f.ville,
    f.aqi,
    f.pm10,
    f.pm2_5,
    f.co,
    f.no2,
    v.latitude,
    v.longitude,
    t.date,
    t.annee,
    t.mois,
    t.jour,
    t.heure
FROM fact_qualite_air f
JOIN dim_ville v ON v.ville = f.ville
JOIN dim_temps t ON t.datetime = f.datetime
ORDER BY f.datetime, f.ville
"""


def export_to_json(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> int:
    """Génère le JSON aplati. Retourne le nombre de lignes exportées."""
    if not db_path.is_file():
        raise FileNotFoundError(
            f"Base introuvable : {db_path}. "
            f"Exécutez d'abord load_warehouse.py."
        )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(QUERY)]

    if not rows:
        raise RuntimeError("Le warehouse est vide : aucun enregistrement à exporter.")

    # Normalise le datetime en ISO 8601 ("2026-05-01T00:00:00") pour Grafana
    for row in rows:
        row["datetime"] = row["datetime"].replace(" ", "T")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"✅ {len(rows)} lignes exportées vers {out_path} "
          f"({out_path.stat().st_size / 1024:.0f} Ko)")
    return len(rows)


if __name__ == "__main__":
    export_to_json()
