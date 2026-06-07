"""
Adaptateur de base de données — SQLite, PostgreSQL, MySQL.
"""
import os
import pandas as pd


class DBAdapter:
    """
    Abstraction légère autour d'une connexion DB.
    Gère l'adaptation des placeholders ? → %s (PostgreSQL / MySQL)
    et offre une interface read_sql unifiée.
    """
    PLACEHOLDER = {"sqlite": "?", "postgresql": "%s", "mysql": "%s"}

    def __init__(self, db_type: str, conn, label: str = ""):
        self.db_type = db_type
        self.conn    = conn
        self.label   = label or db_type

    def adapt_sql(self, sql: str) -> str:
        if self.db_type != "sqlite":
            return sql.replace("?", "%s")
        return sql

    def read_sql(self, sql: str, params=None) -> pd.DataFrame:
        return pd.read_sql_query(self.adapt_sql(sql), self.conn,
                                 params=params or [])

    def execute(self, sql: str, params=None):
        cur = self.conn.cursor()
        cur.execute(self.adapt_sql(sql), params or [])
        self.conn.commit()
        return cur


def connect_db(cfg: dict) -> DBAdapter:
    """
    Crée un DBAdapter depuis un dictionnaire de config.
    cfg["type"] : "sqlite" | "postgresql" | "mysql"
    """
    import sqlite3
    db_type = cfg.get("type", "sqlite").lower()

    if db_type == "sqlite":
        path  = cfg.get("path", ":memory:")
        conn  = sqlite3.connect(path, check_same_thread=False)
        label = f"SQLite · {os.path.basename(path)}"

    elif db_type == "postgresql":
        try:
            import psycopg2
        except ImportError:
            raise ImportError("pip install psycopg2-binary")
        conn = psycopg2.connect(
            host=cfg["host"], port=int(cfg.get("port", 5432)),
            dbname=cfg["database"], user=cfg["user"], password=cfg["password"],
        )
        conn.autocommit = True
        label = f"PostgreSQL · {cfg['host']}/{cfg['database']}"

    elif db_type == "mysql":
        try:
            import mysql.connector
        except ImportError:
            raise ImportError("pip install mysql-connector-python")
        conn = mysql.connector.connect(
            host=cfg["host"], port=int(cfg.get("port", 3306)),
            database=cfg["database"], user=cfg["user"], password=cfg["password"],
        )
        label = f"MySQL · {cfg['host']}/{cfg['database']}"

    else:
        raise ValueError(
            f"Type de DB non supporté : {db_type!r}. "
            "Valeurs acceptées : sqlite, postgresql, mysql"
        )

    return DBAdapter(db_type, conn, label)


def introspect_schema_from_db(adapter: DBAdapter,
                               table_filter: "list | None" = None) -> dict:
    """
    Découvre automatiquement les tables, colonnes, clés primaires et clés
    étrangères d'une base de données réelle.
    Retourne un dict compatible avec le format SCHEMA de config.yaml.
    """
    import pandas as pd
    db_type = adapter.db_type
    conn    = adapter.conn
    schema  = {}

    if db_type == "sqlite":
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
        )["name"].tolist()
        tables = [t for t in tables if not t.startswith("_")]
        if table_filter:
            tables = [t for t in tables if t in table_filter]

        for t in tables:
            info    = pd.read_sql_query(f"PRAGMA table_info(\"{t}\")", conn)
            pk_rows = info[info["pk"] == 1]["name"].tolist()
            pk      = pk_rows[0] if pk_rows else (info["name"].iloc[0] if len(info) else "id")
            fk_rows = pd.read_sql_query(f"PRAGMA foreign_key_list(\"{t}\")", conn)
            fks = [{"col": r["from"], "ref": r["table"], "ref_col": r["to"]}
                   for _, r in fk_rows.iterrows()]
            schema[t] = {"columns": info["name"].tolist(), "pk": pk, "fk": fks}

    elif db_type == "postgresql":
        schema_name = "public"
        cols = pd.read_sql_query(f"""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = '{schema_name}'
            ORDER BY table_name, ordinal_position
        """, conn)
        pks = pd.read_sql_query(f"""
            SELECT kcu.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema    = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema = '{schema_name}'
        """, conn)
        fks_raw = pd.read_sql_query(f"""
            SELECT kcu.table_name, kcu.column_name,
                   ccu.table_name AS ref_table, ccu.column_name AS ref_col
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema    = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema    = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = '{schema_name}'
        """, conn)
        pk_map = dict(zip(pks["table_name"], pks["column_name"]))
        fk_map: dict = {}
        for _, r in fks_raw.iterrows():
            fk_map.setdefault(r["table_name"], []).append(
                {"col": r["column_name"], "ref": r["ref_table"], "ref_col": r["ref_col"]})
        for tbl, grp in cols.groupby("table_name"):
            if table_filter and tbl not in table_filter:
                continue
            schema[tbl] = {
                "columns": grp["column_name"].tolist(),
                "pk":      pk_map.get(tbl, grp["column_name"].iloc[0]),
                "fk":      fk_map.get(tbl, []),
            }

    elif db_type == "mysql":
        db_name = conn.database
        cols = pd.read_sql_query(f"""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = '{db_name}'
            ORDER BY TABLE_NAME, ORDINAL_POSITION
        """, conn)
        pks = pd.read_sql_query(f"""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{db_name}'
              AND CONSTRAINT_NAME = 'PRIMARY'
        """, conn)
        fks_raw = pd.read_sql_query(f"""
            SELECT TABLE_NAME, COLUMN_NAME,
                   REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{db_name}'
              AND REFERENCED_TABLE_NAME IS NOT NULL
        """, conn)
        pk_map = dict(zip(pks["TABLE_NAME"], pks["COLUMN_NAME"]))
        fk_map: dict = {}
        for _, r in fks_raw.iterrows():
            fk_map.setdefault(r["TABLE_NAME"], []).append({
                "col":     r["COLUMN_NAME"],
                "ref":     r["REFERENCED_TABLE_NAME"],
                "ref_col": r["REFERENCED_COLUMN_NAME"],
            })
        for tbl, grp in cols.groupby("TABLE_NAME"):
            if table_filter and tbl not in table_filter:
                continue
            schema[tbl] = {
                "columns": grp["COLUMN_NAME"].tolist(),
                "pk":      pk_map.get(tbl, grp["COLUMN_NAME"].iloc[0]),
                "fk":      fk_map.get(tbl, []),
            }

    return schema
