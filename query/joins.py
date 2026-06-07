"""
Gestion des jointures et enrichissement.
"""
from db.demo import _get_db


def get_available_joins(schema: dict, base_table: str, current_joins: list) -> list:
    """
    Retourne les tables joignables (non encore utilisées) avec leur condition
    ON auto-détectée à partir des clés étrangères du schéma.
    """
    already_used = {base_table} | {j["table"] for j in current_joins}
    result, seen = [], set()
    for candidate, info in schema.items():
        if candidate in already_used or candidate in seen:
            continue
        for existing in already_used:
            for fk in schema[existing].get("fk", []):
                if fk["ref"] == candidate:
                    result.append({
                        "table":    candidate,
                        "on":       f"{existing}.{fk['col']} = {candidate}.{fk['ref_col']}",
                        "relation": f"{existing}.{fk['col']}  →  {candidate}.{fk['ref_col']}",
                    })
                    seen.add(candidate)
                    break
            if candidate in seen:
                break
            for fk in info.get("fk", []):
                if fk["ref"] == existing:
                    result.append({
                        "table":    candidate,
                        "on":       f"{candidate}.{fk['col']} = {existing}.{fk['ref_col']}",
                        "relation": f"{candidate}.{fk['col']}  →  {existing}.{fk['ref_col']}",
                    })
                    seen.add(candidate)
                    break
            if candidate in seen:
                break
    return result


def get_all_columns(schema: dict, base_table: str, joins: list) -> list:
    """Colonnes qualifiées (table.col) de la table de base + toutes les jointures."""
    cols = [f"{base_table}.{c}" for c in schema[base_table]["columns"]]
    for j in joins:
        cols += [f"{j['table']}.{c}" for c in schema[j["table"]]["columns"]]
    return cols


def get_column_labels(schema: dict, base_table: str, joins: list) -> dict:
    """
    Retourne {col_key: label_affiché} pour le sélecteur de conditions.
    Sans jointure : col_key = "nom"         → label = "Nom"
    Avec jointure : col_key = "clients.nom" → label = "Nom  (clients)"
    """
    has_joins = bool(joins)
    result: dict = {}

    for col in schema[base_table]["columns"]:
        raw = schema[base_table].get("labels", {}).get(col, col)
        key = f"{base_table}.{col}" if has_joins else col
        result[key] = f"{raw}  ({base_table})" if has_joins else raw

    for j in joins:
        t = j["table"]
        for col in schema[t]["columns"]:
            raw = schema[t].get("labels", {}).get(col, col)
            result[f"{t}.{col}"] = f"{raw}  ({t})"

    return result


def compute_enrich_count(table, where_clause, params, enrich):
    sql = enrich[table]["count_sql"].format(where=where_clause)
    try:
        res = _get_db().read_sql(sql, params)
        return int(res["total"].iloc[0])
    except Exception:
        return None


def run_enrich_query(table, where_clause, params, enrich):
    sql = enrich[table]["select_sql"].format(where=where_clause)
    return _get_db().read_sql(sql, params)
