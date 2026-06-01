"""
Tests de non-régression — SQL Query Builder
Couvre :
  - Structure DB (3 tables voyage + VIEW voyages)
  - Intégrité des données via le VIEW
  - Logique métier (build_where, build_query, revalidate_joins, get_available_joins)
  - Requêtes du module carte
  - Requêtes enrich (config.yaml)
  - Chargement de la config

Lancer : pytest test_non_regression.py -v
"""

import sys, os, re
import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Imports du module applicatif -----------------------------------
from sql_query_builderV2 import (
    get_connection,
    build_where,
    build_query,
    build_query_display,
    revalidate_joins,
    get_available_joins,
    get_all_columns,
    get_column_labels,
    load_config,
    DBAdapter,
)


# ====================================================================
# Fixtures
# ====================================================================

@pytest.fixture(scope="session")
def raw_conn():
    """Connexion SQLite brute (pour tester les requêtes directement)."""
    return get_connection()


@pytest.fixture(scope="session")
def db(raw_conn):
    return DBAdapter("sqlite", raw_conn, "test")


@pytest.fixture(scope="session")
def schema():
    return load_config()["schema"]


@pytest.fixture(scope="session")
def enrich():
    return load_config().get("enrich", {})


# ====================================================================
# Structure de la base de données
# ====================================================================

class TestDatabaseStructure:
    def test_voyage_group_exists(self, raw_conn):
        names = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table'", raw_conn
        )["name"].tolist()
        assert "voyage_group" in names

    def test_voyage_place_exists(self, raw_conn):
        names = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table'", raw_conn
        )["name"].tolist()
        assert "voyage_place" in names

    def test_voyage_members_exists(self, raw_conn):
        names = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table'", raw_conn
        )["name"].tolist()
        assert "voyage_members" in names

    def test_voyages_is_a_view(self, raw_conn):
        views = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='view'", raw_conn
        )["name"].tolist()
        assert "voyages" in views

    def test_voyages_not_a_table(self, raw_conn):
        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table'", raw_conn
        )["name"].tolist()
        assert "voyages" not in tables

    def test_voyage_group_columns(self, raw_conn):
        df = pd.read_sql("PRAGMA table_info(voyage_group)", raw_conn)
        cols = set(df["name"].tolist())
        assert {"id", "date_depart", "date_retour", "duree_jours",
                "type_voyage", "transport", "statut", "groupe_voyage_id"} == cols

    def test_voyage_place_columns(self, raw_conn):
        df = pd.read_sql("PRAGMA table_info(voyage_place)", raw_conn)
        cols = set(df["name"].tolist())
        assert {"voyage_id", "destination", "pays_destination",
                "continent", "hotel"} == cols

    def test_voyage_members_columns(self, raw_conn):
        df = pd.read_sql("PRAGMA table_info(voyage_members)", raw_conn)
        cols = set(df["name"].tolist())
        assert {"voyage_id", "client_id", "budget", "note"} == cols


# ====================================================================
# Intégrité du VIEW voyages
# ====================================================================

class TestVoyagesView:
    EXPECTED_COLS = {"id", "client_id", "destination", "pays_destination",
                     "continent", "date_depart", "date_retour", "duree_jours",
                     "type_voyage", "transport", "hotel", "budget",
                     "statut", "note", "groupe_voyage_id"}

    def test_view_has_all_original_columns(self, raw_conn):
        df = pd.read_sql("SELECT * FROM voyages LIMIT 1", raw_conn)
        assert self.EXPECTED_COLS.issubset(set(df.columns))

    def test_view_row_count(self, raw_conn):
        n = pd.read_sql("SELECT COUNT(*) AS n FROM voyages", raw_conn)["n"].iloc[0]
        assert n == 28

    def test_voyage_group_row_count(self, raw_conn):
        n = pd.read_sql("SELECT COUNT(*) AS n FROM voyage_group", raw_conn)["n"].iloc[0]
        assert n == 28

    def test_voyage_place_row_count(self, raw_conn):
        n = pd.read_sql("SELECT COUNT(*) AS n FROM voyage_place", raw_conn)["n"].iloc[0]
        assert n == 28

    def test_voyage_members_row_count(self, raw_conn):
        n = pd.read_sql("SELECT COUNT(*) AS n FROM voyage_members", raw_conn)["n"].iloc[0]
        assert n == 28

    def test_tokyo_group_1001(self, raw_conn):
        df = pd.read_sql(
            "SELECT id, destination, groupe_voyage_id FROM voyages "
            "WHERE groupe_voyage_id=1001 ORDER BY id", raw_conn
        )
        assert len(df) == 2
        assert set(df["destination"].tolist()) == {"Tokyo"}
        assert set(df["id"].tolist()) == {1, 25}

    def test_budget_integrity(self, raw_conn):
        budget = pd.read_sql(
            "SELECT budget FROM voyages WHERE id=10", raw_conn
        )["budget"].iloc[0]
        assert abs(budget - 6200.0) < 0.01

    def test_null_note_for_future_trips(self, raw_conn):
        df = pd.read_sql(
            "SELECT note FROM voyages WHERE id IN (22,23,24)", raw_conn
        )
        assert df["note"].isna().all()

    def test_null_groupe_for_solo_trips(self, raw_conn):
        grp = pd.read_sql(
            "SELECT groupe_voyage_id FROM voyages WHERE id=2", raw_conn
        )["groupe_voyage_id"].iloc[0]
        assert grp is None or pd.isna(grp)

    def test_client_1_has_correct_voyages(self, raw_conn):
        df = pd.read_sql(
            "SELECT id FROM voyages WHERE client_id=1 ORDER BY id", raw_conn
        )
        assert list(df["id"]) == [1, 2, 22]

    def test_budget_total_sum(self, raw_conn):
        total = pd.read_sql(
            "SELECT SUM(budget) AS s FROM voyages", raw_conn
        )["s"].iloc[0]
        # Somme calculée manuellement depuis les données d'origine
        assert abs(total - 86_730.0) < 1.0

    def test_join_voyages_clients(self, raw_conn):
        df = pd.read_sql("""
            SELECT c.nom, v.destination
            FROM voyages v
            JOIN clients c ON v.client_id = c.id
            WHERE v.id = 1
        """, raw_conn)
        assert len(df) == 1
        assert df.iloc[0]["destination"] == "Tokyo"
        assert df.iloc[0]["nom"] == "Lemaire"

    def test_view_preserves_continent(self, raw_conn):
        continents = pd.read_sql(
            "SELECT DISTINCT continent FROM voyages ORDER BY continent", raw_conn
        )["continent"].tolist()
        assert "Asie" in continents
        assert "Europe" in continents
        assert "Amérique" in continents


# ====================================================================
# Logique métier : build_where / build_query
# ====================================================================

class TestBuildWhere:
    def test_empty_returns_always_true(self):
        where, params = build_where([])
        assert where == "1=1"
        assert params == []

    def test_single_egal(self):
        cond = [{"column": "statut", "operator": "Égal à", "value": "actif",
                 "join_op": "ET", "is_date": False, "is_bulk": False}]
        where, params = build_where(cond)
        assert "statut" in where
        assert "=" in where
        assert "actif" in params

    def test_like_contient(self):
        cond = [{"column": "nom", "operator": "Contient", "value": "mar",
                 "join_op": "ET", "is_date": False, "is_bulk": False}]
        where, params = build_where(cond)
        assert "LIKE" in where
        assert "%mar%" in params

    def test_two_conditions_et(self):
        conds = [
            {"column": "statut", "operator": "Égal à", "value": "actif",
             "join_op": "ET", "is_date": False, "is_bulk": False},
            {"column": "ville", "operator": "Égal à", "value": "Paris",
             "join_op": "ET", "is_date": False, "is_bulk": False},
        ]
        where, params = build_where(conds)
        assert "AND" in where
        assert len(params) == 2

    def test_two_conditions_ou(self):
        conds = [
            {"column": "ville", "operator": "Égal à", "value": "Paris",
             "join_op": "ET", "is_date": False, "is_bulk": False},
            {"column": "ville", "operator": "Égal à", "value": "Lyon",
             "join_op": "OU", "is_date": False, "is_bulk": False},
        ]
        where, params = build_where(conds)
        assert "OR" in where

    def test_bulk_condition(self):
        cond = [{"column": "ville", "operator": "Égal à",
                 "value": "Paris, Lyon", "values": ["Paris", "Lyon"],
                 "join_op": "ET", "is_date": False, "is_bulk": True}]
        where, params = build_where(cond)
        assert "OR" in where
        assert len(params) == 2


class TestBuildQuery:
    def test_select_all_voyages(self, raw_conn, schema):
        sql, params = build_query("voyages", [], schema=schema)
        df = pd.read_sql(sql, raw_conn, params=params)
        assert len(df) == 28

    def test_select_all_clients(self, raw_conn, schema):
        sql, params = build_query("clients", [], schema=schema)
        df = pd.read_sql(sql, raw_conn, params=params)
        assert len(df) == 12

    def test_query_with_condition(self, raw_conn, schema):
        conds = [{"column": "statut", "operator": "Égal à", "value": "actif",
                  "join_op": "ET", "is_date": False, "is_bulk": False}]
        sql, params = build_query("clients", conds, schema=schema)
        df = pd.read_sql(sql, raw_conn, params=params)
        assert len(df) == 10  # 10 clients actifs dans les données

    def test_query_with_join(self, raw_conn, schema):
        joins = [{"table": "clients", "type": "LEFT JOIN",
                  "on": "voyages.client_id = clients.id"}]
        sql, params = build_query("voyages", [], joins=joins, schema=schema)
        df = pd.read_sql(sql, raw_conn, params=params)
        assert len(df) == 28

    def test_no_self_join_in_query(self, raw_conn, schema):
        joins = [{"table": "voyages", "type": "LEFT JOIN",
                  "on": "voyages.client_id = voyages.client_id"}]
        sql, params = build_query("voyages", [], joins=joins, schema=schema)
        # La jointure self-join doit être ignorée silencieusement
        assert "JOIN voyages" not in sql

    def test_display_query_no_params(self, schema):
        conds = [{"column": "statut", "operator": "Égal à", "value": "actif",
                  "join_op": "ET", "is_date": False, "is_bulk": False}]
        sql = build_query_display("clients", conds, schema=schema)
        assert "'actif'" in sql
        assert "?" not in sql


# ====================================================================
# revalidate_joins — suppression en cascade
# ====================================================================

class TestRevalidateJoins:
    def test_orphan_removed_on_delete(self):
        """Supprimer clients doit retirer voyages qui en dépend."""
        remaining = [
            {"table": "voyages", "type": "LEFT JOIN",
             "on": "clients.id = voyages.client_id"},
        ]
        result = revalidate_joins("passeports", remaining)
        assert result == []

    def test_valid_join_kept(self):
        joins = [
            {"table": "clients", "type": "LEFT JOIN",
             "on": "voyages.client_id = clients.id"},
        ]
        result = revalidate_joins("voyages", joins)
        assert len(result) == 1

    def test_chain_cascade(self):
        """passeports → clients → voyages : retirer clients cascade sur voyages."""
        chain = [
            {"table": "clients", "type": "LEFT JOIN",
             "on": "passeports.client_id = clients.id"},
            {"table": "voyages", "type": "LEFT JOIN",
             "on": "clients.id = voyages.client_id"},
        ]
        # On simule la suppression de clients
        after_remove = [j for j in chain if j["table"] != "clients"]
        result = revalidate_joins("passeports", after_remove)
        assert result == []

    def test_independent_join_unaffected(self):
        """Supprimer employes ne doit pas toucher affectations si bien chaîné."""
        joins = [
            {"table": "affectations", "type": "LEFT JOIN",
             "on": "employes.id = affectations.employe_id"},
        ]
        result = revalidate_joins("employes", joins)
        assert len(result) == 1

    def test_empty_list_stays_empty(self):
        assert revalidate_joins("clients", []) == []

    def test_base_table_not_removed(self):
        joins = [
            {"table": "clients", "type": "LEFT JOIN",
             "on": "voyages.client_id = clients.id"},
        ]
        result = revalidate_joins("voyages", joins)
        tables = [j["table"] for j in result]
        assert "voyages" not in tables


# ====================================================================
# get_available_joins
# ====================================================================

class TestGetAvailableJoins:
    def test_clients_can_join_voyages(self, schema):
        avail = get_available_joins(schema, "clients", [])
        tables = [j["table"] for j in avail]
        assert "voyages" in tables

    def test_voyages_can_join_clients(self, schema):
        avail = get_available_joins(schema, "voyages", [])
        tables = [j["table"] for j in avail]
        assert "clients" in tables

    def test_passeports_can_join_clients(self, schema):
        avail = get_available_joins(schema, "passeports", [])
        tables = [j["table"] for j in avail]
        assert "clients" in tables

    def test_employes_can_join_affectations(self, schema):
        avail = get_available_joins(schema, "employes", [])
        tables = [j["table"] for j in avail]
        assert "affectations" in tables

    def test_no_self_join(self, schema):
        for base in schema:
            avail = get_available_joins(schema, base, [])
            tables = [j["table"] for j in avail]
            assert base not in tables, f"{base} s'auto-joint"

    def test_already_joined_excluded(self, schema):
        current = [{"table": "clients", "type": "LEFT JOIN",
                    "on": "voyages.client_id = clients.id"}]
        avail = get_available_joins(schema, "voyages", current)
        tables = [j["table"] for j in avail]
        assert "clients" not in tables

    def test_on_condition_references_real_columns(self, schema):
        avail = get_available_joins(schema, "clients", [])
        for j in avail:
            assert "." in j["on"], f"ON sans table.col : {j['on']}"
            assert "=" in j["on"]


# ====================================================================
# Requêtes du module carte
# ====================================================================

class TestMapModuleQueries:
    def test_stats_par_pays(self, raw_conn):
        df = pd.read_sql("""
            SELECT pays_destination,
                   COUNT(*)                  AS nb_voyages,
                   COUNT(DISTINCT client_id) AS nb_clients,
                   ROUND(AVG(budget),  0)    AS budget_moyen,
                   ROUND(SUM(budget),  0)    AS total_budget
            FROM voyages
            GROUP BY pays_destination
            ORDER BY nb_voyages DESC
        """, raw_conn)
        assert len(df) > 0
        assert "nb_voyages" in df.columns
        assert df["nb_voyages"].sum() == 28

    def test_clients_par_pays(self, raw_conn):
        df = pd.read_sql("""
            SELECT c.id, c.nom, c.prenom,
                   COUNT(v.id)             AS nb_voyages,
                   ROUND(SUM(v.budget), 0) AS total_budget
            FROM clients c
            JOIN voyages v ON c.id = v.client_id
            WHERE v.pays_destination = 'Japon'
            GROUP BY c.id
        """, raw_conn)
        assert len(df) > 0
        assert all(col in df.columns for col in ["nom", "nb_voyages", "total_budget"])

    def test_voyages_client_id(self, raw_conn):
        df = pd.read_sql("""
            SELECT v.pays_destination, v.destination, v.continent,
                   v.date_depart, v.date_retour, v.duree_jours,
                   v.budget, v.note, v.type_voyage, v.statut
            FROM voyages v
            WHERE v.client_id = 1
            ORDER BY v.date_depart DESC
        """, raw_conn)
        assert len(df) == 3
        assert "Tokyo" in df["destination"].tolist()


# ====================================================================
# Requêtes enrich (issues de config.yaml)
# ====================================================================

class TestEnrichQueries:
    def test_voyages_enrich_count(self, raw_conn):
        df = pd.read_sql(
            "SELECT COUNT(*) AS total FROM clients "
            "WHERE id IN (SELECT client_id FROM voyages WHERE 1=1)",
            raw_conn,
        )
        assert df.iloc[0]["total"] > 0

    def test_clients_enrich_count(self, raw_conn):
        df = pd.read_sql(
            "SELECT COUNT(*) AS total FROM voyages WHERE client_id IN (1, 2)",
            raw_conn,
        )
        assert df.iloc[0]["total"] > 0

    def test_clients_enrich_select(self, raw_conn):
        df = pd.read_sql("""
            SELECT c.*,
                   v.id AS voyage_id, v.destination, v.pays_destination,
                   v.continent, v.date_depart, v.date_retour, v.duree_jours,
                   v.type_voyage, v.budget, v.statut, v.note
            FROM clients c
            JOIN voyages v ON c.id = v.client_id
            WHERE c.id IN (1, 2)
            ORDER BY v.date_depart DESC
        """, raw_conn)
        assert len(df) > 0
        assert "destination" in df.columns

    def test_voyages_enrich_select(self, raw_conn):
        df = pd.read_sql("""
            SELECT c.*, v.destination, v.pays_destination,
                   v.date_depart, v.date_retour, v.budget
            FROM voyages v
            JOIN clients c ON v.client_id = c.id
            WHERE v.id IN (1, 2, 3)
            ORDER BY v.date_depart DESC
        """, raw_conn)
        assert len(df) == 3

    def test_passeports_enrich(self, raw_conn):
        df = pd.read_sql("""
            SELECT c.*, p.num_passeport, p.nationalite,
                   p.date_emission, p.date_expiration
            FROM passeports p
            JOIN clients c ON p.client_id = c.id
            WHERE p.id IN (1, 2)
            ORDER BY p.date_expiration DESC
        """, raw_conn)
        assert len(df) == 2
        assert "num_passeport" in df.columns

    def test_employes_enrich(self, raw_conn):
        df = pd.read_sql("""
            SELECT e.*, a.agence, a.ville AS ville_affectation,
                   a.pays AS pays_affectation, a.continent,
                   a.date_debut, a.date_fin
            FROM employes e
            JOIN affectations a ON e.id = a.employe_id
            WHERE e.id IN (1)
            ORDER BY a.date_debut DESC
        """, raw_conn)
        assert len(df) > 0
        assert "agence" in df.columns


# ====================================================================
# Chargement de la configuration
# ====================================================================

class TestConfigLoading:
    def test_schema_loads(self, schema):
        assert isinstance(schema, dict)
        assert len(schema) > 0

    def test_voyages_in_schema(self, schema):
        assert "voyages" in schema

    def test_voyages_schema_columns(self, schema):
        cols = schema["voyages"]["columns"]
        expected = {"id", "client_id", "destination", "pays_destination",
                    "continent", "date_depart", "date_retour", "duree_jours",
                    "type_voyage", "transport", "hotel", "budget",
                    "statut", "note", "groupe_voyage_id"}
        assert expected.issubset(set(cols))

    def test_voyages_fk_to_clients(self, schema):
        fks = schema["voyages"].get("fk", [])
        refs = [fk["ref"] for fk in fks]
        assert "clients" in refs

    def test_all_fk_refs_exist(self, schema):
        for table, info in schema.items():
            for fk in info.get("fk", []):
                assert fk["ref"] in schema, (
                    f"{table}.fk ref '{fk['ref']}' introuvable dans le schéma"
                )

    def test_pk_in_columns(self, schema):
        for table, info in schema.items():
            assert info["pk"] in info["columns"], (
                f"{table}: pk '{info['pk']}' absent de columns"
            )

    def test_sub_voyage_tables_not_in_schema(self, schema):
        """Les 3 sous-tables ne doivent PAS apparaître dans l'UI (config)."""
        assert "voyage_group" not in schema
        assert "voyage_place" not in schema
        assert "voyage_members" not in schema
