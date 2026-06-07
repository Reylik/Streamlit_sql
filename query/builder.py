"""
Construction de l'arbre binaire et génération du SQL WHERE / requête complète.
"""
from utils import OPERATORS


# ── Arbre binaire ─────────────────────────────────────────────────────────────

def build_tree(conditions):
    """
    Arbre binaire. Chaque condition (sauf la 1re) précise :
      join_op   : "ET" | "OU"
      or_target : "leaf"   → combine avec la DERNIÈRE feuille  (groupe local)
                  "branch" → enveloppe TOUT l'arbre            (nouvelle branche)

    Ex : [A, B(ET,leaf), C(OU,leaf), D(OU,branch)]
         → (A AND (B OR C)) OR D
    """
    if not conditions:
        return None
    tree = {"type": "leaf", "idx": 0}
    last_leaf = tree
    for i in range(1, len(conditions)):
        op        = conditions[i]["join_op"]
        placement = conditions[i].get("or_target", "branch")
        new_leaf  = {"type": "leaf", "idx": i}
        if placement == "leaf":
            old = dict(last_leaf)
            last_leaf.clear()
            last_leaf.update({"type": "branch", "op": op,
                              "left": old, "right": new_leaf})
            last_leaf = new_leaf
        else:
            tree = {"type": "branch", "op": op, "left": tree, "right": new_leaf}
            last_leaf = new_leaf
        
    return tree


def build_preview_tree(conditions, pending):
    """
    Arbre committé + DEUX nœuds fantômes cliquables pour choisir le placement.
    """
    op = pending["join_op"]
    if not conditions:
        return None

    base = {"type": "leaf", "idx": 0}
    last_leaf = base
    for i in range(1, len(conditions)):
        cop       = conditions[i]["join_op"]
        placement = conditions[i].get("or_target", "branch")
        nl        = {"type": "leaf", "idx": i}
        if placement == "leaf":
            old = dict(last_leaf)
            last_leaf.clear()
            last_leaf.update({"type": "branch", "op": cop, "left": old, "right": nl})
            last_leaf = nl
        else:
            base = {"type": "branch", "op": cop, "left": base, "right": nl}
            last_leaf = nl

    ghost_leaf = {"type": "ghost", "target": "leaf", "pending": pending}
    old = dict(last_leaf)
    last_leaf.clear()
    last_leaf.update({"type": "branch", "ghost": True, "op": op,
                      "left": old, "right": ghost_leaf})

    ghost_branch = {"type": "ghost", "target": "branch", "pending": pending}
    return {"type": "branch", "ghost": True, "op": op,
            "left": base, "right": ghost_branch}


# ── Génération SQL ────────────────────────────────────────────────────────────

def _sql_from_tree(node, conditions, params, display):
    if node["type"] == "leaf":
        c = conditions[node["idx"]]

        if c.get("is_pair"):
            col1, col2 = c["columns"]
            pairs      = c.get("pairs", [])
            if not pairs:
                return "1=0"
            sub_clauses = []
            for v1, v2 in pairs:
                if display:
                    v1d = str(v1).replace("'", "''")
                    v2d = str(v2).replace("'", "''")
                    sub_clauses.append(f"({col1} = '{v1d}' AND {col2} = '{v2d}')")
                else:
                    sub_clauses.append(f"({col1} = ? AND {col2} = ?)")
                    params.extend([v1, v2])
            return "(" + " OR ".join(sub_clauses) + ")"

        if c.get("is_bulk"):
            sym, fn = OPERATORS[c["operator"]]
            if display:
                clauses = [f"{c['column']} {sym} '{fn(v)}'" for v in c["values"]]
            else:
                clauses = []
                for v in c["values"]:
                    clauses.append(f"{c['column']} {sym} ?")
                    params.append(fn(v))
            return "(" + " OR ".join(clauses) + ")"

        elif isinstance(c["value"], (tuple, list)) and len(c["value"]) == 2:
            date1, date2 = c["value"]
            if display:
                return f"{c['column']} BETWEEN '{date1}' AND '{date2}'"
            else:
                params.extend([date1, date2])
                return f"{c['column']} BETWEEN ? AND ?"

        sym, fn = OPERATORS[c["operator"]]
        val = fn(c["value"])
        if display:
            return f"{c['column']} {sym} '{val}'"
        params.append(val)
        return f"{c['column']} {sym} ?"

    if node["type"] == "or_group":
        parts = [_sql_from_tree(child, conditions, params, display)
                 for child in node["children"]]
        return "(" + " OR ".join(parts) + ")"

    sql_op = "AND" if node["op"] == "ET" else "OR"
    L = _sql_from_tree(node["left"],  conditions, params, display)
    R = _sql_from_tree(node["right"], conditions, params, display)
    return f"({L} {sql_op} {R})"


def build_where(conditions, display=False):
    if not conditions:
        return "1=1", []
    params = []
    where = _sql_from_tree(build_tree(conditions), conditions, params, display)
    return where, params


def build_query(table, conditions, joins=None, schema=None):
    where, params = build_where(conditions)
    safe_joins = [j for j in (joins or []) if j["table"] != table]

    if safe_joins and schema:
        col_count: dict = {}
        for t in [table] + [j["table"] for j in safe_joins]:
            for c in schema.get(t, {}).get("columns", []):
                col_count[c] = col_count.get(c, 0) + 1

        parts = []
        for t in [table] + [j["table"] for j in safe_joins]:
            for c in schema.get(t, {}).get("columns", []):
                parts.append(f"{t}.{c} AS {t}_{c}" if col_count[c] > 1 else f"{t}.{c}")
        sql = "SELECT " + ", ".join(parts) + f"\nFROM {table}"
    else:
        sql = f"SELECT *\nFROM {table}"

    for j in safe_joins:
        sql += f"\n{j['type']} {j['table']} ON {j['on']}"
    if where != "1=1":
        sql += f"\nWHERE {where}"
    return sql, params


def build_query_display(table, conditions, joins=None, schema=None):
    where, _ = build_where(conditions, display=True)
    safe_joins = [j for j in (joins or []) if j["table"] != table]

    if safe_joins and schema:
        col_count: dict = {}
        for t in [table] + [j["table"] for j in safe_joins]:
            for c in schema.get(t, {}).get("columns", []):
                col_count[c] = col_count.get(c, 0) + 1
        parts = []
        for t in [table] + [j["table"] for j in safe_joins]:
            for c in schema.get(t, {}).get("columns", []):
                parts.append(f"{t}.{c} AS {t}_{c}" if col_count[c] > 1 else f"{t}.{c}")
        sql = "SELECT " + ", ".join(parts) + f"\nFROM {table}"
    else:
        sql = f"SELECT *\nFROM {table}"

    for j in safe_joins:
        sql += f"\n{j['type']} {j['table']} ON {j['on']}"
    if where != "1=1":
        sql += f"\nWHERE {where}"
    return sql
