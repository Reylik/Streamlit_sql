import streamlit as st
import pandas as pd
import sqlite3
import re
import copy
import uuid
import json
import os
from datetime import datetime

st.set_page_config(page_title="SQL Query Builder", page_icon="🔍",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',system-ui,-apple-system,sans-serif;}
.stApp{background:#0d0f14;color:#e8eaf0;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;font-size:2.2rem!important;
   background:linear-gradient(135deg,#64b5f6,#a78bfa,#f472b6);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px;}
h2,h3{font-family:'Syne',sans-serif!important;font-weight:700!important;color:#c8cad6!important;}
.stButton>button{font-family:'Syne',sans-serif!important;font-weight:600!important;
   background:linear-gradient(135deg,#3b82f6,#7c3aed)!important;color:white!important;
   border:none!important;border-radius:8px!important;transition:all .2s!important;}
.stButton>button:hover{transform:translateY(-1px)!important;
   box-shadow:0 6px 20px rgba(99,102,241,.4)!important;}
.stSelectbox>div>div,.stTextInput>div>div>input,
.stNumberInput>div>div>input{
   background:#1a1d27!important;border:1px solid #2a2d3e!important;
   border-radius:8px!important;color:#e8eaf0!important;font-family:'Syne',sans-serif!important;}
.stSelectbox>div>div:hover,.stTextInput>div>div>input:focus,
.stNumberInput>div>div>input:focus{border-color:#6366f1!important;
   box-shadow:0 0 0 2px rgba(99,102,241,.2)!important;}
.sql-display{background:#0a0c12;border:1px solid #1e2130;border-left:3px solid #6366f1;
   border-radius:10px;padding:18px 22px;font-family:'JetBrains Mono',monospace;
   font-size:.85rem;color:#a5f3fc;line-height:1.8;white-space:pre-wrap;margin:8px 0;}
.tree-wrap{background:#0f111a;border:1px solid #1e2130;border-radius:12px;
   padding:18px 18px 12px;margin:10px 0;}
.t-root{display:inline-block;background:linear-gradient(135deg,#312e81,#4c1d95);color:#c4b5fd;
   padding:6px 16px;border-radius:6px;font-family:'JetBrains Mono',monospace;
   font-weight:600;font-size:.85rem;}
.t-leaf{background:#1e293b;border:1px solid #334155;border-radius:6px;
   padding:4px 12px;font-family:'JetBrains Mono',monospace;font-size:.8rem;
   display:inline-block;line-height:1.8;}
[data-testid="stMetric"]{background:#13151d;border:1px solid #1e2130;
   border-radius:10px;padding:14px 18px;}
[data-testid="stMetricValue"]{color:#6366f1!important;
   font-family:'JetBrains Mono',monospace!important;font-weight:700!important;}
[data-testid="stDataFrame"]{border:1px solid #1e2130;border-radius:10px;overflow:hidden;}
[data-testid="stExpander"]{background:#13151d!important;border:1px solid #1e2130!important;
   border-radius:10px!important;}
hr{border-color:#1e2130!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#0d0f14;}
::-webkit-scrollbar-thumb{background:#2a2d3e;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#6366f1;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DB
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,nom TEXT,prenom TEXT,
      email TEXT,telephone TEXT,ville TEXT,pays TEXT,date_inscription TEXT,statut TEXT,
      num_carte_identite TEXT,date_expiration_ci TEXT,
      profession TEXT,employeur TEXT,situation_pro TEXT);
    INSERT INTO clients VALUES
    (1,'Lemaire','Sophie','sophie.lemaire@mail.fr','0612345678','Paris','France','2020-01-15','actif','9901234567890','2025-08-20','Ingénieure informatique','TechCorp SA','CDI'),
    (2,'Garnier','Thomas','t.garnier@mail.fr','0623456789','Lyon','France','2019-06-22','actif','9912345678901','2024-11-30','Consultant','McKinsey France','CDI'),
    (3,'Faure','Julie','julie.faure@mail.fr','0634567890','Marseille','France','2021-03-10','actif','9923456789012','2026-04-15','Médecin','CHU Marseille','Titulaire'),
    (4,'Chevalier','Marc','marc.chev@mail.fr','0645678901','Bordeaux','France','2018-11-05','inactif','9934567890123','2023-12-01','Directeur commercial','AutoParts SAS','CDI'),
    (5,'Morin','Lucie','lucie.morin@mail.fr','0656789012','Nantes','France','2022-07-30','actif','9945678901234','2027-06-20','Graphiste','Freelance','Indépendante'),
    (6,'Perrin','Antoine','a.perrin@mail.fr','0667890123','Toulouse','France','2020-09-14','actif','9956789012345','2025-03-10','Avocat','Cabinet Perrin & Associés','Libéral'),
    (7,'Blanc','Camille','c.blanc@mail.fr','0678901234','Strasbourg','France','2023-02-01','actif','9967890123456','2028-01-25','Architecte','Studio 42','CDI'),
    (8,'Renard','Nicolas','n.renard@mail.fr','0689012345','Lille','France','2017-05-18','inactif',NULL,NULL,'Retraité',NULL,'Retraité'),
    (9,'Vidal','Inès','ines.vidal@mail.fr','0690123456','Nice','France','2021-12-25','actif','9989012345678','2026-09-30','Chef de projet','BNP Paribas','CDI'),
    (10,'Roy','Kevin','kevin.roy@mail.fr','0601234567','Rennes','France','2022-04-03','actif','9990123456789','2027-04-03','Développeur full-stack','StartupXYZ','CDI'),
    (11,'Caron','Éléonore','e.caron@mail.fr','0611223344','Paris','France','2019-08-19','actif','9901122334455','2025-11-15','Professeure','Lycée Victor Hugo','Titulaire'),
    (12,'Picard','Bastien','b.picard@mail.fr','0622334455','Montpellier','France','2023-10-11','actif','9912233445566','2028-10-11','Étudiant','Université Paris-Dauphine','Alternance');

    CREATE TABLE IF NOT EXISTS passeports(
      id INTEGER PRIMARY KEY, client_id INTEGER,
      num_passeport TEXT, nationalite TEXT,
      date_emission TEXT, date_expiration TEXT,
      FOREIGN KEY(client_id) REFERENCES clients(id));
    INSERT INTO passeports VALUES
    (1,1,'FP100001','Française','2013-06-15','2018-06-15'),
    (2,1,'FP100002','Française','2023-07-01','2033-07-01'),
    (3,2,'FP200001','Française','2014-03-22','2019-03-22'),
    (4,2,'FP200002','Française','2024-04-01','2034-04-01'),
    (5,3,'FP300001','Française','2021-01-10','2031-01-10'),
    (6,4,'FP400001','Française','2010-09-05','2015-09-05'),
    (7,6,'FP600001','Française','2016-12-14','2021-12-14'),
    (8,6,'FP600002','Française','2026-01-01','2036-01-01'),
    (9,7,'FP700001','Française','2023-02-01','2033-02-01'),
    (10,8,'FP800001','Française','2009-05-18','2014-05-18'),
    (11,9,'FP900001','Française','2018-12-25','2028-12-25'),
    (12,11,'FP110001','Française','2017-08-19','2027-08-19');

    CREATE TABLE IF NOT EXISTS voyages(id INTEGER PRIMARY KEY,client_id INTEGER,
      destination TEXT,pays_destination TEXT,continent TEXT,
      date_depart TEXT,date_retour TEXT,duree_jours INTEGER,
      type_voyage TEXT,transport TEXT,hotel TEXT,
      budget REAL,statut TEXT,note INTEGER,groupe_voyage_id INTEGER,
      FOREIGN KEY(client_id) REFERENCES clients(id));
    INSERT INTO voyages VALUES
    (1,1,'Tokyo','Japon','Asie','2023-04-10','2023-04-24',14,'Tourisme','Avion','Grand Hyatt Tokyo',3200.00,'terminé',5,1001),
    (2,1,'Barcelone','Espagne','Europe','2022-07-15','2022-07-22',7,'Tourisme','Train','Hotel Arts',1100.00,'terminé',4,NULL),
    (3,2,'New York','États-Unis','Amérique','2023-08-01','2023-08-10',9,'Affaires','Avion','Marriott Times Square',2800.00,'terminé',4,NULL),
    (4,2,'Rome','Italie','Europe','2022-12-20','2022-12-27',7,'Tourisme','Avion','Hotel Eden',1350.00,'terminé',5,NULL),
    (5,3,'Bali','Indonésie','Asie','2023-06-01','2023-06-15',14,'Détente','Avion','Four Seasons Bali',2900.00,'terminé',5,1002),
    (6,3,'Lisbonne','Portugal','Europe','2024-03-10','2024-03-14',4,'City Break','Avion','Bairro Alto Hotel',750.00,'terminé',4,NULL),
    (7,4,'Dubai','Émirats Arabes Unis','Asie','2023-01-05','2023-01-12',7,'Luxe','Avion','Burj Al Arab',5500.00,'terminé',5,NULL),
    (8,5,'Marrakech','Maroc','Afrique','2023-10-20','2023-10-27',7,'Culturel','Avion','La Mamounia',1800.00,'terminé',5,NULL),
    (9,5,'Amsterdam','Pays-Bas','Europe','2024-05-01','2024-05-04',3,'City Break','Train','Hotel V Nesplein',620.00,'terminé',3,NULL),
    (10,6,'Maldives','Maldives','Asie','2023-02-14','2023-02-21',7,'Lune de miel','Avion','Conrad Maldives',6200.00,'terminé',5,1003),
    (11,6,'Prague','Tchéquie','Europe','2022-11-03','2022-11-06',3,'City Break','Avion','Augustine Hotel',580.00,'terminé',4,NULL),
    (12,7,'Sydney','Australie','Océanie','2023-12-22','2024-01-05',14,'Tourisme','Avion','Park Hyatt Sydney',4100.00,'terminé',5,NULL),
    (13,7,'Athènes','Grèce','Europe','2023-09-08','2023-09-15',7,'Culturel','Avion','Hotel Grande Bretagne',1250.00,'terminé',4,NULL),
    (14,8,'Reykjavik','Islande','Europe','2023-03-15','2023-03-20',5,'Aventure','Avion','Ion Adventure Hotel',1700.00,'terminé',4,NULL),
    (15,9,'Kyoto','Japon','Asie','2024-04-01','2024-04-10',9,'Culturel','Avion','The Ritz-Carlton Kyoto',3600.00,'terminé',5,NULL),
    (16,9,'Séville','Espagne','Europe','2023-05-18','2023-05-22',4,'City Break','Avion','Hotel Alfonso XIII',890.00,'terminé',4,NULL),
    (17,10,'Cancún','Mexique','Amérique','2023-07-01','2023-07-14',13,'Plage','Avion','Nizuc Resort',3100.00,'terminé',5,1004),
    (18,10,'Berlin','Allemagne','Europe','2022-10-29','2022-10-31',2,'City Break','Train','Hotel de Rome',410.00,'terminé',3,NULL),
    (19,11,'Cape Town','Afrique du Sud','Afrique','2023-11-10','2023-11-24',14,'Safari','Avion','The Silo Hotel',4800.00,'terminé',5,NULL),
    (20,11,'Bruges','Belgique','Europe','2024-02-14','2024-02-16',2,'Romantique','Train','Hotel Dukes Palace',490.00,'terminé',4,NULL),
    (21,12,'Costa Rica','Costa Rica','Amérique','2024-01-15','2024-01-28',13,'Aventure','Avion','Nayara Springs',3900.00,'terminé',5,NULL),
    (22,1,'Singapour','Singapour','Asie','2024-06-20','2024-06-28',8,'Affaires','Avion','Marina Bay Sands',3400.00,'à venir',NULL,NULL),
    (23,3,'New York','États-Unis','Amérique','2024-09-01','2024-09-08',7,'Tourisme','Avion','The Plaza',2600.00,'à venir',NULL,NULL),
    (24,5,'Tenerife','Espagne','Europe','2024-08-10','2024-08-17',7,'Plage','Avion','Royal Hideaway',1500.00,'à venir',NULL,NULL),
    (25,2,'Tokyo','Japon','Asie','2023-04-10','2023-04-24',14,'Tourisme','Avion','Grand Hyatt Tokyo',3200.00,'terminé',5,1001),
    (26,11,'Bali','Indonésie','Asie','2023-06-01','2023-06-15',14,'Détente','Avion','Four Seasons Bali',2900.00,'terminé',4,1002),
    (27,7,'Maldives','Maldives','Asie','2023-02-14','2023-02-21',7,'Lune de miel','Avion','Conrad Maldives',6200.00,'terminé',5,1003),
    (28,9,'Cancún','Mexique','Amérique','2023-07-01','2023-07-14',13,'Plage','Avion','Nizuc Resort',3100.00,'terminé',4,1004);

    CREATE TABLE IF NOT EXISTS employes(
      id INTEGER PRIMARY KEY, nom TEXT, prenom TEXT, poste TEXT,
      email TEXT, telephone TEXT, statut TEXT, date_embauche TEXT
    );
    INSERT INTO employes VALUES
    (1,'Dupont','Marie','Directeur Régional','m.dupont@agency.fr','0601110001','actif','2015-03-01'),
    (2,'Martin','Pierre','Agent Commercial','p.martin@agency.fr','0601110002','actif','2018-06-15'),
    (3,'Leblanc','Sophie','Responsable Visa','s.leblanc@agency.fr','0601110003','actif','2017-09-01'),
    (4,'Bernard','Thomas','Agent Commercial','t.bernard@agency.fr','0601110004','actif','2019-01-15'),
    (5,'Petit','Claire','Directeur Régional','c.petit@agency.fr','0601110005','actif','2016-04-01'),
    (6,'Robert','Julien','Responsable Opérations','j.robert@agency.fr','0601110006','actif','2020-02-01'),
    (7,'Richard','Anaïs','Agent Commercial','a.richard@agency.fr','0601110007','actif','2018-11-01'),
    (8,'Moreau','Kevin','Responsable Visa','k.moreau@agency.fr','0601110008','inactif','2016-03-01'),
    (9,'Simon','Lucie','Agent Commercial','l.simon@agency.fr','0601110009','actif','2021-07-01'),
    (10,'Laurent','Antoine','Directeur Régional','a.laurent@agency.fr','0601110010','actif','2014-09-01'),
    (11,'Michel','Emma','Responsable Opérations','e.michel@agency.fr','0601110011','actif','2019-05-15'),
    (12,'Garcia','Lucas','Agent Commercial','l.garcia@agency.fr','0601110012','actif','2022-01-01'),
    (13,'David','Nina','Responsable Visa','n.david@agency.fr','0601110013','actif','2017-08-01'),
    (14,'Bertrand','Maxime','Agent Commercial','m.bertrand@agency.fr','0601110014','actif','2020-10-01'),
    (15,'Roux','Chloé','Directeur Régional','c.roux@agency.fr','0601110015','actif','2015-12-01');

    CREATE TABLE IF NOT EXISTS affectations(
      id INTEGER PRIMARY KEY, employe_id INTEGER,
      agence TEXT, ville TEXT, pays TEXT, continent TEXT,
      date_debut TEXT, date_fin TEXT,
      FOREIGN KEY(employe_id) REFERENCES employes(id)
    );
    INSERT INTO affectations VALUES
    (1,1,'Agence Paris Opéra','Paris','France','Europe','2015-03-01','2019-08-31'),
    (2,1,'Agence Tokyo Shinjuku','Tokyo','Japon','Asie','2019-09-01','2021-12-31'),
    (3,1,'Agence Dubai Centre','Dubai','Émirats Arabes Unis','Asie','2022-01-01','2023-06-30'),
    (4,1,'Agence Paris Opéra','Paris','France','Europe','2023-07-01',NULL),
    (5,2,'Agence Lyon Centre','Lyon','France','Europe','2018-06-15','2020-12-31'),
    (6,2,'Agence Barcelone','Barcelone','Espagne','Europe','2021-01-01','2022-09-30'),
    (7,2,'Agence Lyon Centre','Lyon','France','Europe','2022-10-01',NULL),
    (8,3,'Agence Marseille','Marseille','France','Europe','2017-09-01','2020-06-30'),
    (9,3,'Agence New York','New York','États-Unis','Amérique','2020-07-01','2022-12-31'),
    (10,3,'Agence Singapour','Singapour','Singapour','Asie','2023-01-01',NULL),
    (11,4,'Agence Paris Montparnasse','Paris','France','Europe','2019-01-15','2021-03-31'),
    (12,4,'Agence Marrakech','Marrakech','Maroc','Afrique','2021-04-01','2023-03-31'),
    (13,4,'Agence Casablanca','Casablanca','Maroc','Afrique','2023-04-01',NULL),
    (14,5,'Agence Bordeaux','Bordeaux','France','Europe','2016-04-01','2020-11-30'),
    (15,5,'Agence Sydney','Sydney','Australie','Océanie','2021-01-01','2022-06-30'),
    (16,5,'Agence Melbourne','Melbourne','Australie','Océanie','2022-07-01',NULL),
    (17,6,'Agence Toulouse','Toulouse','France','Europe','2020-02-01','2021-09-30'),
    (18,6,'Agence Tokyo Ginza','Tokyo','Japon','Asie','2021-10-01','2023-09-30'),
    (19,6,'Agence Séoul','Séoul','Corée du Sud','Asie','2023-10-01',NULL),
    (20,7,'Agence Nice','Nice','France','Europe','2018-11-01','2021-12-31'),
    (21,7,'Agence Lisbonne','Lisbonne','Portugal','Europe','2022-01-01','2023-12-31'),
    (22,7,'Agence Nice','Nice','France','Europe','2024-01-01',NULL),
    (23,8,'Agence Paris Opéra','Paris','France','Europe','2016-03-01','2020-09-30'),
    (24,8,'Agence Dubai Marina','Dubai','Émirats Arabes Unis','Asie','2020-10-01','2022-12-31'),
    (25,9,'Agence Nantes','Nantes','France','Europe','2021-07-01','2022-12-31'),
    (26,9,'Agence Buenos Aires','Buenos Aires','Argentine','Amérique','2023-01-01','2023-12-31'),
    (27,9,'Agence Nantes','Nantes','France','Europe','2024-01-01',NULL),
    (28,10,'Agence Paris Champs-Élysées','Paris','France','Europe','2014-09-01','2019-12-31'),
    (29,10,'Agence Amsterdam','Amsterdam','Pays-Bas','Europe','2020-01-01','2021-11-30'),
    (30,10,'Agence Bangkok','Bangkok','Thaïlande','Asie','2021-12-01',NULL),
    (31,11,'Agence Strasbourg','Strasbourg','France','Europe','2019-05-15','2021-04-30'),
    (32,11,'Agence Rome','Rome','Italie','Europe','2021-05-01','2023-04-30'),
    (33,11,'Agence Madrid','Madrid','Espagne','Europe','2023-05-01',NULL),
    (34,12,'Agence Lille','Lille','France','Europe','2022-01-01','2023-06-30'),
    (35,12,'Agence Miami','Miami','États-Unis','Amérique','2023-07-01',NULL),
    (36,13,'Agence Rennes','Rennes','France','Europe','2017-08-01','2020-07-31'),
    (37,13,'Agence Cape Town','Cape Town','Afrique du Sud','Afrique','2020-08-01','2022-07-31'),
    (38,13,'Agence Nairobi','Nairobi','Kenya','Afrique','2022-08-01',NULL),
    (39,14,'Agence Montpellier','Montpellier','France','Europe','2020-10-01','2022-04-30'),
    (40,14,'Agence Montréal','Montréal','Canada','Amérique','2022-05-01','2023-09-30'),
    (41,14,'Agence Vancouver','Vancouver','Canada','Amérique','2023-10-01',NULL),
    (42,15,'Agence Paris Grands Boulevards','Paris','France','Europe','2015-12-01','2020-05-31'),
    (43,15,'Agence Mexico City','Mexico','Mexique','Amérique','2020-06-01','2022-05-31'),
    (44,15,'Agence Lima','Lima','Pérou','Amérique','2022-06-01',NULL);
    """)
    conn.commit()
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# ADAPTATEUR DE BASE DE DONNÉES  (SQLite · PostgreSQL · MySQL)
# ══════════════════════════════════════════════════════════════════════════════

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

    def read_sql(self, sql: str, params=None) -> "pd.DataFrame":
        return pd.read_sql_query(self.adapt_sql(sql), self.conn,
                                 params=params or [])

    def execute(self, sql: str, params=None):
        cur = self.conn.cursor()
        cur.execute(self.adapt_sql(sql), params or [])
        self.conn.commit()
        return cur


@st.cache_data(ttl=300)
def get_table_summary(table_name: str, date_cols: tuple) -> dict:
    """
    Retourne un résumé de la table : nombre de lignes + dates min/max
    pour chaque colonne de type date. Tout est calculé en SQL.

    Paramètres
    ----------
    table_name : str
        Nom de la table SQL.
    date_cols : tuple
        Tuple des noms de colonnes de type date (tuple pour être hashable et cacheable).

    Retour
    ------
    dict avec :
      - "row_count" : int, nombre total de lignes
      - "date_info" : dict { col: {"min": str, "max": str} }
    """
    db = _get_db()
    summary = {"row_count": 0, "date_info": {}}

    # Nombre de lignes
    try:
        df_count = db.read_sql(f"SELECT COUNT(*) AS n FROM {table_name}")
        summary["row_count"] = int(df_count["n"].iloc[0])
    except Exception:
        return summary

    # Dates min/max pour chaque colonne date
    if date_cols:
        select_parts = []
        for col in date_cols:
            select_parts.append(f"MIN({col}) AS {col}__min")
            select_parts.append(f"MAX({col}) AS {col}__max")
        sql = f"SELECT {', '.join(select_parts)} FROM {table_name}"
        try:
            df_dates = db.read_sql(sql)
            row = df_dates.iloc[0]
            for col in date_cols:
                vmin = row[f"{col}__min"]
                vmax = row[f"{col}__max"]
                summary["date_info"][col] = {
                    "min": str(vmin) if pd.notna(vmin) else None,
                    "max": str(vmax) if pd.notna(vmax) else None,
                }
        except Exception:
            pass

    return summary


def _get_db() -> DBAdapter:
    """Retourne l'adaptateur SQLite de démonstration (toujours actif)."""
    return DBAdapter("sqlite", get_connection(), "Démo SQLite")


# ── Connexion depuis une config dict ──────────────────────────────────────────
def connect_db(cfg: dict) -> DBAdapter:
    """
    Crée un DBAdapter depuis un dictionnaire de config.
    cfg["type"] : "sqlite" | "postgresql" | "mysql"

    SQLite  : {"type": "sqlite", "path": "./ma_base.db"}
    PostgreSQL : {"type": "postgresql", "host": ..., "port": ...,
                  "database": ..., "user": ..., "password": ...}
    MySQL   : {"type": "mysql",      "host": ..., "port": ...,
                  "database": ..., "user": ..., "password": ...}
    """
    db_type = cfg.get("type", "sqlite").lower()

    if db_type == "sqlite":
        path = cfg.get("path", ":memory:")
        conn = sqlite3.connect(path, check_same_thread=False)
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
        raise ValueError(f"Type de DB non supporté : {db_type!r}. Valeurs acceptées : sqlite, postgresql, mysql")

    return DBAdapter(db_type, conn, label)


# ── Introspection automatique du schéma ───────────────────────────────────────
def introspect_schema_from_db(adapter: DBAdapter,
                               table_filter: "list | None" = None) -> dict:
    """
    Découvre automatiquement les tables, colonnes, clés primaires et clés
    étrangères d'une base de données réelle.
    Retourne un dict compatible avec le format SCHEMA de config.yaml.
    """
    db_type = adapter.db_type
    conn    = adapter.conn
    schema  = {}

    if db_type == "sqlite":
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
        )["name"].tolist()
        tables = [t for t in tables if not t.startswith("_")]  # ignore internes
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
                "col": r["COLUMN_NAME"],
                "ref": r["REFERENCED_TABLE_NAME"],
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


# ── Page de connexion ─────────────────────────────────────────────────────────
OPERATORS = {
    "Contient":     ("LIKE", lambda v: f"%{v}%"),
    "Commence par": ("LIKE", lambda v: f"{v}%"),
    "Finit par":    ("LIKE", lambda v: f"%{v}"),
    "Égal à":       ("=",    lambda v: v),
    "Différent de": ("!=",   lambda v: v),
    "Supérieur à":  (">",    lambda v: v),
    "Inférieur à":  ("<",    lambda v: v),
}
OP_LABELS = list(OPERATORS.keys())

MONTHS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin",
             "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]


def is_date_col(col: str) -> bool:
    return "date" in col.lower()


def build_date_value(year: int, month: int, day: int) -> str:
    if month == 0:   return f"{year:04d}"
    elif day == 0:   return f"{year:04d}-{month:02d}"
    else:            return f"{year:04d}-{month:02d}-{day:02d}"


# ══════════════════════════════════════════════════════════════════════════════
# ARBRE BINAIRE & SQL
# ══════════════════════════════════════════════════════════════════════════════
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
    last_leaf = tree                      # référence vivante vers la dernière feuille
    for i in range(1, len(conditions)):
        op        = conditions[i]["join_op"]
        placement = conditions[i].get("or_target", "branch")
        new_leaf  = {"type": "leaf", "idx": i}
        if placement == "leaf":
            # Remplacer la dernière feuille EN PLACE par (last_leaf op new_leaf)
            old = dict(last_leaf)
            last_leaf.clear()
            last_leaf.update({"type": "branch", "op": op,
                              "left": old, "right": new_leaf})
            last_leaf = new_leaf
        else:                              # branch : envelopper tout l'arbre
            tree = {"type": "branch", "op": op, "left": tree, "right": new_leaf}
            last_leaf = new_leaf
    return tree


def build_preview_tree(conditions, pending):
    """
    Arbre committé + DEUX nœuds fantômes :
      • une feuille fantôme greffée sur la dernière feuille  (or_target=leaf)
      • une branche fantôme au sommet                         (or_target=branch)
    Les fantômes sont cliquables et valident le placement.
    """
    op = pending["join_op"]
    if not conditions:
        return None

    # Reconstruire l'arbre committé en gardant la référence de la dernière feuille
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

    # Feuille fantôme : greffée en place sur la dernière feuille
    ghost_leaf = {"type": "ghost", "target": "leaf", "pending": pending}
    old = dict(last_leaf)
    last_leaf.clear()
    last_leaf.update({"type": "branch", "ghost": True, "op": op,
                      "left": old, "right": ghost_leaf})

    # Branche fantôme : enveloppe tout l'arbre au sommet
    ghost_branch = {"type": "ghost", "target": "branch", "pending": pending}
    return {"type": "branch", "ghost": True, "op": op,
            "left": base, "right": ghost_branch}


def _sql_from_tree(node, conditions, params, display):
    if node["type"] == "leaf":
        c = conditions[node["idx"]]
        # ── Recherche par couples (col1=v1a AND col2=v1b) OR (col1=v2a AND col2=v2b) ──
        if c.get("is_pair"):
            col1, col2 = c["columns"]
            pairs      = c.get("pairs", [])
            if not pairs:
                return "1=0"  # liste vide : aucune ligne
            sub_clauses = []
            for v1, v2 in pairs:
                if display:
                    # Échappement basique des apostrophes pour l'affichage
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
        elif isinstance(c["value"], (tuple, list)) and len(c["value"]) == 2:  # Plage de dates
            date1, date2 = c["value"]
            if display:
                return f"{c['column']} BETWEEN '{date1}' AND '{date2}'" 
            else:
                params.extend([date1, date2])
                return f"{c['column']} BETWEEN ? AND ?"
        
        sym, fn = OPERATORS[c["operator"]]
        val = fn(c["value"])
        if display: return f"{c['column']} {sym} '{val}'"
        params.append(val)
        return f"{c['column']} {sym} ?"
    if node["type"] == "or_group":
        # Groupe OR local : (A OR B OR C)
        parts = [_sql_from_tree(child, conditions, params, display)
                 for child in node["children"]]
        return "(" + " OR ".join(parts) + ")"
    # branch (ET dans le nouvel arbre)
    sql_op = "AND" if node["op"] == "ET" else "OR"
    L = _sql_from_tree(node["left"],  conditions, params, display)
    R = _sql_from_tree(node["right"], conditions, params, display)
    return f"({L} {sql_op} {R})"


def build_where(conditions, display=False):
    if not conditions: return "1=1", []
    params = []
    where = _sql_from_tree(build_tree(conditions), conditions, params, display)
    return where, params


def build_query(table, conditions, joins=None, schema=None):
    where, params = build_where(conditions)
    safe_joins = [j for j in (joins or []) if j["table"] != table]
    # Filtrer les auto-jointures (table == base) qui causent des doublons
    safe_joins = [j for j in (joins or []) if j["table"] != table]

    if safe_joins and schema:
        # Compter les occurrences de chaque nom de colonne
        col_count: dict = {}
        for t in [table] + [j["table"] for j in safe_joins]:
            for c in schema.get(t, {}).get("columns", []):
                col_count[c] = col_count.get(c, 0) + 1

        # SELECT explicite : alias table_col pour toute colonne ambiguë
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


# ══════════════════════════════════════════════════════════════════════════════
# JOINTURES  —  détection automatique via les clés étrangères
# ══════════════════════════════════════════════════════════════════════════════
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
            # FK d'une table existante → candidate
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
            # FK du candidate → une table existante
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

    • Sans jointure : col_key = "nom"          → label = "Nom"
    • Avec jointure : col_key = "clients.nom"  → label = "Nom  (clients)"

    Les labels sont lus depuis schema[table]["labels"] si présents,
    sinon le nom technique de la colonne est utilisé tel quel.
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


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DE LA CONFIGURATION EXTERNE (YAML ou TOML)
# ══════════════════════════════════════════════════════════════════════════════

# Chemin par défaut : config.yaml dans le même répertoire que ce fichier.
# Changez en "config.toml" pour utiliser le format TOML.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


# ══════════════════════════════════════════════════════════════════════════════
# MODULE CARTE  —  visualisation géographique des voyages
# ══════════════════════════════════════════════════════════════════════════════

CONT_COLORS: dict[str, str] = {
    "Asie": "#f59e0b", "Europe": "#3b82f6", "Amérique": "#10b981",
    "Afrique": "#ef4444", "Océanie": "#8b5cf6",
}
TYPE_COLORS: dict[str, str] = {
    "Tourisme": "#3b82f6", "Affaires": "#8b5cf6", "Détente": "#10b981",
    "Lune de miel": "#f472b6", "Safari": "#f59e0b", "Aventure": "#ef4444",
    "Luxe": "#fbbf24", "City Break": "#06b6d4", "Culturel": "#a78bfa",
    "Plage": "#22d3ee", "Romantique": "#fb7185",
}

COUNTRY_ISO_MAP: dict[str, str] = {
    "Afghanistan": "AFG", "Afrique du Sud": "ZAF", "Albanie": "ALB",
    "Algérie": "DZA", "Allemagne": "DEU", "Andorre": "AND",
    "Angola": "AGO", "Arabie Saoudite": "SAU", "Argentine": "ARG",
    "Arménie": "ARM", "Australie": "AUS", "Autriche": "AUT",
    "Azerbaïdjan": "AZE", "Bahamas": "BHS", "Bahreïn": "BHR",
    "Bangladesh": "BGD", "Belgique": "BEL", "Bénin": "BEN",
    "Birmanie": "MMR", "Bolivie": "BOL", "Bosnie": "BIH",
    "Brésil": "BRA", "Bulgarie": "BGR", "Cambodge": "KHM",
    "Cameroun": "CMR", "Canada": "CAN", "Chili": "CHL",
    "Chine": "CHN", "Chypre": "CYP", "Colombie": "COL",
    "Congo": "COD", "Corée du Nord": "PRK", "Corée du Sud": "KOR",
    "Costa Rica": "CRI", "Côte d'Ivoire": "CIV", "Croatie": "HRV",
    "Cuba": "CUB", "Danemark": "DNK", "Égypte": "EGY",
    "Émirats Arabes Unis": "ARE", "Équateur": "ECU", "Espagne": "ESP",
    "Estonie": "EST", "États-Unis": "USA", "Éthiopie": "ETH",
    "Finlande": "FIN", "France": "FRA", "Géorgie": "GEO",
    "Ghana": "GHA", "Grèce": "GRC", "Guatemala": "GTM",
    "Honduras": "HND", "Hongrie": "HUN", "Inde": "IND",
    "Indonésie": "IDN", "Irak": "IRQ", "Iran": "IRN",
    "Irlande": "IRL", "Islande": "ISL", "Israël": "ISR",
    "Italie": "ITA", "Jamaïque": "JAM", "Japon": "JPN",
    "Jordanie": "JOR", "Kazakhstan": "KAZ", "Kenya": "KEN",
    "Koweït": "KWT", "Liban": "LBN", "Libye": "LBY",
    "Lituanie": "LTU", "Luxembourg": "LUX", "Maldives": "MDV",
    "Mali": "MLI", "Malaisie": "MYS", "Malte": "MLT",
    "Maroc": "MAR", "Mexique": "MEX", "Monaco": "MCO",
    "Mongolie": "MNG", "Monténégro": "MNE", "Mozambique": "MOZ",
    "Népal": "NPL", "Nicaragua": "NIC", "Niger": "NER",
    "Nigéria": "NGA", "Norvège": "NOR", "Nouvelle-Zélande": "NZL",
    "Oman": "OMN", "Ouganda": "UGA", "Ouzbékistan": "UZB",
    "Pakistan": "PAK", "Panama": "PAN", "Paraguay": "PRY",
    "Pays-Bas": "NLD", "Pérou": "PER", "Philippines": "PHL",
    "Pologne": "POL", "Portugal": "PRT", "Qatar": "QAT",
    "République dominicaine": "DOM", "République tchèque": "CZE",
    "Tchéquie": "CZE", "Roumanie": "ROU", "Royaume-Uni": "GBR",
    "Russie": "RUS", "Rwanda": "RWA", "Salvador": "SLV",
    "Sénégal": "SEN", "Serbie": "SRB", "Singapour": "SGP",
    "Slovaquie": "SVK", "Slovénie": "SVN", "Somalie": "SOM",
    "Soudan": "SDN", "Sri Lanka": "LKA", "Suède": "SWE",
    "Suisse": "CHE", "Syrie": "SYR", "Taïwan": "TWN",
    "Tanzanie": "TZA", "Thaïlande": "THA", "Tunisie": "TUN",
    "Turquie": "TUR", "Ukraine": "UKR", "Uruguay": "URY",
    "Venezuela": "VEN", "Vietnam": "VNM", "Yémen": "YEM",
    "Zambie": "ZMB", "Zimbabwe": "ZWE",
}

_MAP_BG   = "#0d0f14"
_MAP_LAND = "#13151d"
_MAP_SEA  = "#0a0c12"
_MAP_LINE = "#1e2130"


def _map_geo_layout(fig, height: int = 460) -> "go.Figure":
    """Applique le thème sombre aux figures Plotly geo."""
    fig.update_layout(
        paper_bgcolor=_MAP_BG, plot_bgcolor=_MAP_BG,
        font=dict(color="#e8eaf0"),
        margin=dict(l=0, r=0, t=0, b=0), height=height,
        coloraxis_showscale=False,
        geo=dict(
            bgcolor=_MAP_BG, showframe=False,
            showcoastlines=True, coastlinecolor="#2a2d3e",
            showland=True,    landcolor=_MAP_LAND,
            showocean=True,   oceancolor=_MAP_SEA,
            showlakes=True,   lakecolor=_MAP_SEA,
            showcountries=True, countrycolor=_MAP_LINE,
            projection_type="natural earth",
        ),
    )
    return fig


def _choropleth(df, color_col, hover_name, hover_data, color_scale,
                custom_data=None, highlight_iso=None, height=460):
    """Construit un choropleth Plotly avec thème sombre + pays surligné optionnel."""
    import plotly.express as px
    import plotly.graph_objects as go

    fig = px.choropleth(
        df, locations="iso_alpha", color=color_col,
        hover_name=hover_name, hover_data=hover_data,
        color_continuous_scale=color_scale,
        range_color=[0, max(df[color_col].max(), 1)],
        custom_data=custom_data or [],
    )
    if highlight_iso:
        fig.add_trace(go.Choropleth(
            locations=[highlight_iso], z=[1],
            colorscale=[[0, "#6366f1"], [1, "#6366f1"]],
            showscale=False, hoverinfo="skip",
            marker_line_color="#a78bfa", marker_line_width=2.5,
        ))
    return _map_geo_layout(fig, height)


def _read_map_click(event) -> "str | None":
    """Extrait le nom de pays cliqué depuis un event st.plotly_chart."""
    sel = getattr(event, "selection", None)
    pts = getattr(sel, "points", None) or (sel or {}).get("points", [])
    if not pts:
        return None
    raw = pts[0].get("customdata") or []
    return (raw[0] if isinstance(raw, (list, tuple)) and raw else raw) or None


def render_map_module() -> None:
    """
    Module carte principale.
    • Vue monde    : choropleth nb voyages par pays
    • Vue pays     : clients ayant visité ce pays (clic → vue client)
    • Vue client   : tous les pays visités par ce client
    """
    import plotly.express as px

    db  = _get_db()
    nav = st.session_state

    selected_country = nav.get("map_country")
    selected_cid     = nav.get("map_client_id")
    selected_cname   = nav.get("map_client_name", "")

    # ── Fil d'Ariane ──────────────────────────────────────────────────────────
    if selected_cid or selected_country:
        back_cols = st.columns([2, 10])
        with back_cols[0]:
            if selected_cid:
                label = f"← {selected_country}" if selected_country else "← Carte"
                if st.button(label, key="map_back", use_container_width=True):
                    nav.pop("map_client_id",   None)
                    nav.pop("map_client_name", None)
                    st.rerun()
            else:
                if st.button("← Carte mondiale", key="map_back", use_container_width=True):
                    nav.pop("map_country", None)
                    st.rerun()

    # ── Données globales ──────────────────────────────────────────────────────
    try:
        cdf = db.read_sql("""
            SELECT pays_destination,
                   COUNT(*)                    AS nb_voyages,
                   COUNT(DISTINCT client_id)   AS nb_clients,
                   ROUND(AVG(budget),  0)      AS budget_moyen,
                   ROUND(SUM(budget),  0)      AS total_budget
            FROM voyages
            GROUP BY pays_destination
            ORDER BY nb_voyages DESC
        """)
    except Exception:
        st.error("La table `voyages` est introuvable dans la base connectée.")
        return

    if cdf.empty:
        st.info("Aucune donnée de voyage disponible.")
        return

    cdf["iso_alpha"] = cdf["pays_destination"].map(COUNTRY_ISO_MAP)

    # ════════════════════════════════════════════════════════════════════════════
    # VUE CLIENT — carte personnelle
    # ════════════════════════════════════════════════════════════════════════════
    if selected_cid:
        try:
            trips = db.read_sql("""
                SELECT v.pays_destination, v.destination, v.continent,
                       v.date_depart, v.date_retour, v.duree_jours,
                       v.budget, v.note, v.type_voyage, v.statut
                FROM voyages v
                WHERE v.client_id = ?
                ORDER BY v.date_depart DESC
            """, [selected_cid])
        except Exception:
            st.error("Impossible de récupérer les voyages de ce client.")
            return

        if trips.empty:
            st.info("Aucun voyage pour ce client.")
            return

        pers = (trips.groupby("pays_destination")
                     .agg(nb_voyages=("pays_destination", "count"),
                          total_budget=("budget", "sum"))
                     .reset_index())
        pers["iso_alpha"] = pers["pays_destination"].map(COUNTRY_ISO_MAP)

        n_pays     = pers["pays_destination"].nunique()
        total_bgt  = int(trips["budget"].sum())
        n_trips    = len(trips)

        st.markdown(
            f"<h2 style='margin-bottom:.15rem;'>🧳 {selected_cname}</h2>"
            f"<p style='color:#64748b;margin-bottom:1rem;font-size:.88rem;'>"
            f"{n_trips} voyage(s) · {n_pays} pays · {total_bgt:,} €</p>",
            unsafe_allow_html=True)

        fig_c = _choropleth(
            pers, "total_budget", "pays_destination",
            {"iso_alpha": False, "nb_voyages": "Voyages",
             "total_budget": "Budget total (€)"},
            [[0, "#172554"], [0.4, "#7c3aed"], [1, "#a78bfa"]],
            custom_data=["pays_destination"], height=400,
        )
        st.plotly_chart(fig_c, use_container_width=True, key="client_map")

        # Destination list
        CONT = {"Asie": "#f59e0b", "Europe": "#3b82f6", "Amérique": "#10b981",
                "Afrique": "#ef4444", "Océanie": "#8b5cf6"}
        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        for _, r in trips.iterrows():
            note_v  = r.get("note")
            stars   = "⭐" * int(note_v) if note_v and pd.notna(note_v) else "—"
            sc      = "#4ade80" if r.get("statut") == "terminé" else "#fbbf24"
            cc      = CONT.get(r.get("continent", ""), "#6b7280")
            st.markdown(
                f"<div style='background:#13151d;border:1px solid #1e2130;"
                f"border-left:3px solid {cc};"
                f"border-radius:10px;padding:10px 16px;margin-bottom:7px;"
                f"display:flex;align-items:center;gap:12px;'>"
                f"<div style='flex:1;'>"
                f"<span style='font-weight:600;color:#e8eaf0;'>{r['destination']}</span>"
                f"<span style='color:#475569;font-size:.8rem;margin-left:8px;'>"
                f"{r['pays_destination']} · {str(r['date_depart'])[:10]}"
                f"{'  ·  ' + str(r['duree_jours']) + 'j' if r.get('duree_jours') else ''}"
                f"</span></div>"
                f"<span style='color:#4ade80;font-family:JetBrains Mono,monospace;"
                f"font-size:.82rem;'>{int(r['budget']):,}€</span>"
                f"<span style='color:{sc};font-size:.75rem;margin-left:10px;'>{r['statut']}</span>"
                f"<span style='font-size:.78rem;margin-left:8px;'>{stars}</span>"
                f"</div>",
                unsafe_allow_html=True)
        return

    # ════════════════════════════════════════════════════════════════════════════
    # VUE MONDE / VUE PAYS
    # ════════════════════════════════════════════════════════════════════════════

    # Métriques globales
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Pays visités",  int(cdf["pays_destination"].nunique()))
    mc2.metric("Total voyages", int(cdf["nb_voyages"].sum()))
    mc3.metric("Budget total",  f"{int(cdf['total_budget'].sum()):,}€")
    mc4.metric("Budget moyen",  f"{int(cdf['budget_moyen'].mean()):,}€")

    # Carte monde
    hi_iso = None
    if selected_country:
        row_hi = cdf[cdf["pays_destination"] == selected_country]
        if not row_hi.empty and pd.notna(row_hi.iloc[0].get("iso_alpha")):
            hi_iso = row_hi.iloc[0]["iso_alpha"]

    fig_w = _choropleth(
        cdf, "nb_voyages", "pays_destination",
        {"iso_alpha": False, "nb_voyages": "Voyages",
         "nb_clients": "Clients", "budget_moyen": "Budget moyen (€)"},
        [[0, "#172554"], [0.25, "#1d4ed8"], [0.6, "#3b82f6"], [1, "#93c5fd"]],
        custom_data=["pays_destination"], highlight_iso=hi_iso,
    )
    event_w = st.plotly_chart(fig_w, on_select="rerun",
                              key="world_map", use_container_width=True)

    # Lecture du clic carte
    clicked = _read_map_click(event_w)
    if clicked and clicked != selected_country:
        nav["map_country"] = clicked
        st.rerun()

    # Sélecteur texte (fallback + accessibilité)
    all_countries = [""] + sorted(cdf["pays_destination"].tolist())
    idx = all_countries.index(selected_country) if selected_country in all_countries else 0
    chosen = st.selectbox(
        "Ou sélectionnez un pays :", all_countries, index=idx,
        key="map_country_sel",
        format_func=lambda x: x or "— cliquer sur la carte ou choisir ici —",
    )
    if chosen != selected_country:
        nav["map_country"] = chosen or None
        st.rerun()

    if not selected_country:
        st.markdown(
            "<p style='color:#334155;font-style:italic;font-size:.85rem;"
            "text-align:center;margin-top:20px;padding-bottom:4rem;'>"
            "Cliquez sur un pays pour explorer ses statistiques.</p>",
            unsafe_allow_html=True)
        return

    # ── Statistiques du pays sélectionné ──────────────────────────────────────
    r = cdf[cdf["pays_destination"] == selected_country]
    if r.empty:
        return
    r = r.iloc[0]

    st.markdown(
        f"<h3 style='margin:20px 0 4px;'>📍 {selected_country}</h3>",
        unsafe_allow_html=True)
    ps1, ps2, ps3, ps4 = st.columns(4)
    ps1.metric("Voyages",      int(r["nb_voyages"]))
    ps2.metric("Clients",      int(r["nb_clients"]))
    ps3.metric("Budget moyen", f"{int(r['budget_moyen']):,}€")
    ps4.metric("Budget total", f"{int(r['total_budget']):,}€")

    # Clients ayant visité ce pays
    try:
        clients_c = db.read_sql("""
            SELECT c.id, c.nom, c.prenom, c.ville, c.statut,
                   COUNT(v.id)         AS nb_voyages,
                   ROUND(SUM(v.budget),0) AS total_budget
            FROM clients c
            JOIN voyages v ON c.id = v.client_id
            WHERE v.pays_destination = ?
            GROUP BY c.id
            ORDER BY nb_voyages DESC, total_budget DESC
        """, [selected_country])
    except Exception:
        return

    st.markdown(
        f"<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
        f"letter-spacing:1px;font-family:JetBrains Mono,monospace;margin:18px 0 10px;'>"
        f"Clients ayant visité {selected_country}</div>",
        unsafe_allow_html=True)

    for _, cl in clients_c.iterrows():
        sc     = "#4ade80" if cl.get("statut") == "actif" else "#f87171"
        ini    = (str(cl.get("nom","?"))[:1] + str(cl.get("prenom","?"))[:1]).upper()
        cc, cb = st.columns([8, 2])
        with cc:
            st.markdown(
                f"<div style='background:#13151d;border:1px solid #1e2130;"
                f"border-radius:10px;padding:10px 16px;"
                f"display:flex;align-items:center;gap:12px;'>"
                f"<div style='width:34px;height:34px;border-radius:50%;"
                f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                f"display:flex;align-items:center;justify-content:center;"
                f"font-weight:700;font-size:.82rem;color:white;flex-shrink:0;'>{ini}</div>"
                f"<div style='flex:1;'>"
                f"<span style='font-weight:600;color:#e8eaf0;'>"
                f"{cl.get('prenom','')} {cl.get('nom','')}</span>"
                f"<span style='color:#64748b;font-size:.78rem;margin-left:8px;'>"
                f"{cl.get('ville','')} · "
                f"<span style='color:{sc};'>{cl.get('statut','')}</span></span></div>"
                f"<span style='font-family:JetBrains Mono,monospace;font-size:.8rem;"
                f"color:#4ade80;'>{int(cl['total_budget']):,}€</span>"
                f"<span style='font-size:.72rem;color:#475569;margin-left:8px;'>"
                f"{int(cl['nb_voyages'])} voyage(s)</span>"
                f"</div>",
                unsafe_allow_html=True)
        with cb:
            if st.button("Voir ses voyages →",
                         key=f"map_client_{cl['id']}",
                         use_container_width=True):
                nav["map_client_id"]   = int(cl["id"])
                nav["map_client_name"] = f"{cl.get('prenom','')} {cl.get('nom','')}".strip()
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# MODULE RAPPORT  —  génération Word (.docx) et PDF après une recherche
# ══════════════════════════════════════════════════════════════════════════════

def _report_data(df, conditions, current_table, joins, last_where: str) -> dict:
    """Consolide les informations nécessaires au rapport."""
    from datetime import datetime as _dt
    cond_texts = []
    for c in conditions:
        op = OP_NATURAL.get(c.get("operator", ""), c.get("operator", ""))
        if c.get("is_bulk"):
            vals = ", ".join(c["values"][:5])
            sfx  = f" +{len(c['values'])-5} autres" if len(c["values"]) > 5 else ""
            cond_texts.append(f"{c['column']} {op} [{vals}{sfx}]")
        elif c.get("is_date"):
            cond_texts.append(f"{c['column']} en {_date_label(c['value'])}")
        else:
            cond_texts.append(f"{c['column']} {op} «{c['value']}»")

    join_texts = [f"{j['type']} {j['table']} ON {j['on']}" for j in (joins or [])]

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    stats: dict = {}
    for col in num_cols:
        s = df[col].dropna()
        if len(s):
            stats[col] = {"min": float(s.min()), "max": float(s.max()),
                          "mean": float(s.mean()), "sum": float(s.sum()),
                          "count": int(s.count())}
    return {
        "title":        "Rapport d'analyse — SQL Query Builder",
        "generated_at": _dt.now().strftime("%d/%m/%Y à %H:%M"),
        "table":        current_table,
        "joins":        join_texts,
        "conditions":   cond_texts,
        "df":           df,
        "n_rows":       len(df),
        "n_cols":       len(df.columns),
        "stats":        stats,
    }


def generate_report_pdf(rd: dict, max_rows: int = 500) -> bytes:
    """Retourne les bytes d'un rapport PDF (reportlab)."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib             import colors
    from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units       import cm
    from reportlab.platypus        import (SimpleDocTemplate, Paragraph, Spacer,
                                           Table, TableStyle, HRFlowable)

    buf = io.BytesIO()
    W, _H = A4
    margin  = 2.2 * cm
    doc     = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=margin, rightMargin=margin,
                                topMargin=2.5*cm, bottomMargin=2*cm)
    cw      = W - 2 * margin   # largeur utile

    styles  = getSampleStyleSheet()
    BLUE    = colors.HexColor("#1d4ed8")
    LBLUE   = colors.HexColor("#eff6ff")
    LGRAY   = colors.HexColor("#f8fafc")
    GRAY    = colors.HexColor("#e2e8f0")
    DARK    = colors.HexColor("#1e293b")
    MUTED   = colors.HexColor("#6b7280")

    S_TITLE  = ParagraphStyle("T",  parent=styles["Title"],    fontSize=17, spaceAfter=2,
                               textColor=colors.HexColor("#0f172a"))
    S_SUB    = ParagraphStyle("Su", parent=styles["Normal"],   fontSize=9,  spaceAfter=12,
                               textColor=MUTED)
    S_H1     = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=11, spaceBefore=14,
                               spaceAfter=5, textColor=colors.HexColor("#1e3a5f"))
    S_BODY   = ParagraphStyle("B",  parent=styles["Normal"],   fontSize=9,  leading=14,
                               spaceAfter=3, textColor=DARK)
    S_ITALIC = ParagraphStyle("I",  parent=S_BODY, textColor=MUTED)

    def _tbl(data, col_widths, header_bg=BLUE, alt=True):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        cmds = [
            ("FONTNAME",      (0,0), (-1,0),   "Helvetica-Bold"),
            ("FONTNAME",      (0,1), (-1,-1),  "Helvetica"),
            ("FONTSIZE",      (0,0), (-1,-1),  8),
            ("BACKGROUND",    (0,0), (-1,0),   header_bg),
            ("TEXTCOLOR",     (0,0), (-1,0),   colors.white),
            ("GRID",          (0,0), (-1,-1),  0.3, GRAY),
            ("TOPPADDING",    (0,0), (-1,-1),  4),
            ("BOTTOMPADDING", (0,0), (-1,-1),  4),
            ("LEFTPADDING",   (0,0), (-1,-1),  5),
            ("VALIGN",        (0,0), (-1,-1),  "MIDDLE"),
        ]
        if alt:
            for i in range(1, len(data)):
                bg = LGRAY if i % 2 == 0 else colors.white
                cmds.append(("BACKGROUND", (0,i), (-1,i), bg))
        t.setStyle(TableStyle(cmds))
        return t

    story = []
    story.append(Paragraph(rd["title"], S_TITLE))
    story.append(Paragraph(f"Généré le {rd['generated_at']}", S_SUB))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=12))

    # Paramètres
    story.append(Paragraph("Paramètres de la requête", S_H1))
    story.append(Paragraph(f"<b>Table source :</b>  {rd['table']}", S_BODY))
    for j in rd["joins"]:
        story.append(Paragraph(f"<b>Jointure :</b>  {j}", S_BODY))
    if rd["conditions"]:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Conditions :</b>", S_BODY))
        for i, c in enumerate(rd["conditions"], 1):
            story.append(Paragraph(f" {i}.  {c}", S_BODY))
    else:
        story.append(Paragraph("<i>Aucune condition — tous les enregistrements.</i>", S_ITALIC))

    # Résumé
    story.append(Paragraph("Résumé", S_H1))
    smry = [["Lignes retournées", str(rd["n_rows"])],
            ["Colonnes",          str(rd["n_cols"])],
            ["Table source",      rd["table"]],
            ["Généré le",         rd["generated_at"]]]
    story.append(_tbl([["Paramètre", "Valeur"]] + smry,
                      [cw * 0.4, cw * 0.6], header_bg=LBLUE))

    # Données
    df2    = rd["df"].head(max_rows)
    shown  = len(df2)
    sfx    = f" — {shown} affichées" if shown < rd["n_rows"] else ""
    story.append(Paragraph(f"Données  ({rd['n_rows']} lignes{sfx})", S_H1))
    cols   = list(df2.columns)
    n      = len(cols)
    cw_col = max(cw / n, 1.5*cm)
    rows   = [cols]
    for _, row in df2.iterrows():
        rows.append([("" if (v is None or str(v) == "nan") else str(v)) for v in row])
    story.append(_tbl(rows, [cw_col]*n))

    # Statistiques
    if rd["stats"]:
        story.append(Paragraph("Statistiques numériques", S_H1))
        hdr  = ["Colonne", "Min", "Max", "Moyenne", "Somme", "N"]
        srows = [hdr]
        for col, s in rd["stats"].items():
            srows.append([col, f"{s['min']:,.2f}", f"{s['max']:,.2f}",
                          f"{s['mean']:,.2f}", f"{s['sum']:,.2f}", str(s["count"])])
        story.append(_tbl(srows, [cw * 0.28] + [cw * 0.72 / 5] * 5,
                          header_bg=colors.HexColor("#0f172a")))

    # Fiches clients
    df_full    = rd["df"]
    has_nom    = "nom"         in df_full.columns
    has_prenom = "prenom"      in df_full.columns
    has_dest   = "destination" in df_full.columns
    _id_col    = _find_col(df_full, "id", "clients_id")
    _stat_col  = _find_col(df_full, "statut", "clients_statut")

    if has_nom and has_prenom:
        from reportlab.platypus import KeepTogether

        S_NAME = ParagraphStyle("Name", parent=styles["Normal"],
                                 fontSize=10, fontName="Helvetica-Bold",
                                 textColor=colors.HexColor("#0f172a"),
                                 spaceBefore=10, spaceAfter=2)
        S_META = ParagraphStyle("Meta", parent=styles["Normal"],
                                 fontSize=8.5, leading=13,
                                 textColor=colors.HexColor("#6b7280"), spaceAfter=2)
        S_VG   = ParagraphStyle("Vg", parent=styles["Normal"],
                                 fontSize=8.5, leading=14,
                                 textColor=colors.HexColor("#1e293b"),
                                 leftIndent=14, spaceAfter=1)
        S_SEP  = ParagraphStyle("Sep", parent=styles["Normal"],
                                 fontSize=1, spaceAfter=2)

        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1,
                                 color=colors.HexColor("#e2e8f0"), spaceAfter=4))
        story.append(Paragraph("Fiches clients", S_H1))

        CONT_C = {"Asie": "#b45309", "Europe": "#1d4ed8", "Amérique": "#16a34a",
                  "Afrique": "#dc2626", "Océanie": "#7c3aed"}

        if has_dest and _id_col:
            for cid, grp in df_full.groupby(_id_col, sort=False):
                r0      = grp.iloc[0]
                prenom  = r0.get("prenom", "")
                nom     = r0.get("nom", "")
                ville   = r0.get("ville", "")
                email   = r0.get("email", "")
                statut  = r0.get(_stat_col) if _stat_col else r0.get("statut", "")
                s_str   = "actif" if statut == "actif" else "inactif"
                s_col   = "#16a34a" if statut == "actif" else "#dc2626"
                n_v     = len(grp)

                block = []
                block.append(Paragraph(
                    f"<b>{prenom} {nom}</b>"
                    f"<font size='8' color='#6b7280'>  ·  {ville}"
                    f"{'  ·  ' + email if email else ''}</font>"
                    f"  <font size='8' color='{s_col}'>{s_str}</font>"
                    f"  <font size='8' color='#6366f1'>{n_v} voyage(s)</font>",
                    S_NAME))

                for _, vr in grp.iterrows():
                    dest   = vr.get("destination", "")
                    pays   = vr.get("pays_destination", "")
                    cont   = vr.get("continent", "")
                    d_dep  = str(vr.get("date_depart",  ""))[:10]
                    d_ret  = str(vr.get("date_retour", ""))[:10]
                    duree  = vr.get("duree_jours")
                    tv     = vr.get("type_voyage", "")
                    budget = vr.get("budget")
                    note   = vr.get("note")
                    v_stat = vr.get("statut_voyage", vr.get("statut", ""))
                    c_col  = CONT_C.get(cont, "#6b7280")
                    stars  = "\u2605" * int(note) if note and not pd.isna(note) else "\u2014"
                    bgt    = f"{int(budget):,}\u20ac" if budget and not pd.isna(budget) else "\u2014"
                    duree_s = f"  \u00b7  {int(duree)}j" if duree and not pd.isna(duree) else ""

                    block.append(Paragraph(
                        f"<font color='{c_col}'>\u25b8</font>  "
                        f"<b>{dest}</b>"
                        f"<font color='#94a3b8'>  {pays}{duree_s}  \u00b7  {d_dep} \u2192 {d_ret}"
                        f"  \u00b7  {tv}</font>"
                        f"  <font color='#16a34a'>{bgt}</font>"
                        f"  <font color='#b45309' size='8'>{stars}</font>",
                        S_VG))

                block.append(HRFlowable(width="100%", thickness=0.5,
                                         color=colors.HexColor("#f1f5f9"),
                                         spaceAfter=2))
                story.append(KeepTogether(block))

        else:
            # Clients seuls (sans voyages)
            for _, r in df_full.iterrows():
                prenom = r.get("prenom", "")
                nom    = r.get("nom", "")
                ville  = r.get("ville", "")
                email  = r.get("email", "")
                tel    = r.get("telephone", "")
                di     = r.get("date_inscription", "")
                statut = r.get(_stat_col) if _stat_col else r.get("statut", "")
                s_col  = "#16a34a" if statut == "actif" else "#dc2626"

                story.append(Paragraph(
                    f"<b>{prenom} {nom}</b>"
                    f"<font size='8' color='#6b7280'>  \u00b7  {ville}</font>"
                    f"  <font size='8' color='{s_col}'>{statut}</font>",
                    S_NAME))
                meta_parts = []
                if email: meta_parts.append(email)
                if tel:   meta_parts.append(tel)
                if di:    meta_parts.append(f"Membre depuis {str(di)[:10]}")
                if meta_parts:
                    story.append(Paragraph("  \u00b7  ".join(meta_parts), S_META))

    doc.build(story)
    return buf.getvalue()


def generate_report_docx(rd: dict, max_rows: int = 500) -> bytes:
    """Retourne les bytes d'un rapport Word (.docx) (python-docx)."""
    import io
    from docx             import Document
    from docx.shared      import Pt, RGBColor, Cm
    from docx.enum.table  import WD_TABLE_ALIGNMENT
    from docx.oxml.ns     import qn
    from docx.oxml        import OxmlElement

    doc = Document()
    sec = doc.sections[0]
    sec.page_width = sec.page_height = None   # set below
    from docx.shared import Cm as _Cm
    sec.page_width  = _Cm(21)
    sec.page_height = _Cm(29.7)
    sec.left_margin = sec.right_margin  = _Cm(2.5)
    sec.top_margin  = sec.bottom_margin = _Cm(2)

    content_cm = 21 - 5   # 16 cm
    # Clear default empty paragraph
    for p in doc.paragraphs:
        p._element.getparent().remove(p._element)

    def _rgb(hex6):
        return RGBColor(int(hex6[:2],16), int(hex6[2:4],16), int(hex6[4:],16))

    def _shd(cell, fill_hex):
        tc  = cell._tc
        tcPr= tc.get_or_add_tcPr()
        # Remove existing shd
        for old in tcPr.findall(qn("w:shd")):
            tcPr.remove(old)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"),   "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"),  fill_hex.upper())
        tcPr.append(shd)

    def _add_heading(text, level=1, color="0f172a"):
        p = doc.add_paragraph()
        r = p.add_run(text)
        r.bold = True
        r.font.size = Pt(14 if level == 1 else 11)
        r.font.color.rgb = _rgb(color)
        p.paragraph_format.space_before = Pt(14 if level == 1 else 8)
        p.paragraph_format.space_after  = Pt(5)
        return p

    def _add_kv(key, val):
        p = doc.add_paragraph()
        rk = p.add_run(f"{key} : "); rk.bold = True; rk.font.size = Pt(9)
        rv = p.add_run(str(val));    rv.font.size = Pt(9)
        p.paragraph_format.space_after = Pt(2)

    def _hr():
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(8)
        pPr  = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        btm  = OxmlElement("w:bottom")
        btm.set(qn("w:val"),  "single")
        btm.set(qn("w:sz"),   "12")
        btm.set(qn("w:space"),"1")
        btm.set(qn("w:color"),"1D4ED8")
        pBdr.append(btm)
        pPr.append(pBdr)

    def _tbl_docx(header_row, data_rows, col_widths_cm,
                  hdr_fill="1D4ED8", hdr_text="FFFFFF"):
        n   = len(header_row)
        t   = doc.add_table(rows=1, cols=n)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.LEFT
        hcells = t.rows[0].cells
        for i, h in enumerate(header_row):
            hcells[i].text = str(h)
            hcells[i].width = Cm(col_widths_cm[i] if i < len(col_widths_cm) else 2)
            r2 = hcells[i].paragraphs[0].runs[0]
            r2.bold = True; r2.font.size = Pt(8)
            r2.font.color.rgb = _rgb(hdr_text)
            _shd(hcells[i], hdr_fill)
        for ri, row in enumerate(data_rows):
            cells = t.add_row().cells
            fill  = "F8FAFC" if ri % 2 == 0 else "FFFFFF"
            for i, v in enumerate(row):
                cells[i].text  = str(v)
                cells[i].width = Cm(col_widths_cm[i] if i < len(col_widths_cm) else 2)
                for rx in cells[i].paragraphs[0].runs:
                    rx.font.size = Pt(8)
                _shd(cells[i], fill)
        return t

    # ── Titre ────────────────────────────────────────────────────────────────
    p = doc.add_paragraph()
    r = p.add_run(rd["title"])
    r.bold = True; r.font.size = Pt(17); r.font.color.rgb = _rgb("0f172a")
    p.paragraph_format.space_after = Pt(2)

    p2 = doc.add_paragraph(f"Généré le {rd['generated_at']}")
    p2.runs[0].font.size = Pt(9); p2.runs[0].font.color.rgb = _rgb("6b7280")
    p2.paragraph_format.space_after = Pt(4)
    _hr()

    # ── Paramètres ───────────────────────────────────────────────────────────
    _add_heading("Paramètres de la requête")
    _add_kv("Table source", rd["table"])
    for j in rd["joins"]:
        _add_kv("Jointure", j)
    if rd["conditions"]:
        p_h = doc.add_paragraph()
        rh  = p_h.add_run("Conditions :"); rh.bold = True; rh.font.size = Pt(9)
        p_h.paragraph_format.space_after = Pt(2)
        for i, c in enumerate(rd["conditions"], 1):
            pb = doc.add_paragraph(f"  {i}.  {c}", style="List Bullet")
            pb.paragraph_format.space_after = Pt(1)
            for rx in pb.runs: rx.font.size = Pt(9)
    else:
        p_nc = doc.add_paragraph("Aucune condition — tous les enregistrements.")
        p_nc.runs[0].italic = True; p_nc.runs[0].font.size = Pt(9)

    # ── Résumé ───────────────────────────────────────────────────────────────
    _add_heading("Résumé")
    smry = [["Lignes retournées", str(rd["n_rows"])],
            ["Colonnes",          str(rd["n_cols"])],
            ["Table source",      rd["table"]],
            ["Généré le",         rd["generated_at"]]]
    _tbl_docx(["Paramètre", "Valeur"], smry,
              [content_cm * 0.4, content_cm * 0.6],
              hdr_fill="DBEAFE", hdr_text="1E3A5F")

    # ── Données ──────────────────────────────────────────────────────────────
    df2   = rd["df"].head(max_rows)
    shown = len(df2)
    sfx   = f" — {shown} affichées" if shown < rd["n_rows"] else ""
    _add_heading(f"Données  ({rd['n_rows']} lignes{sfx})")
    cols  = list(df2.columns)
    n     = len(cols)
    cw    = max(content_cm / n, 1.5)
    rows  = [["" if (v is None or str(v) == "nan") else str(v) for v in row]
             for _, row in df2.iterrows()]
    _tbl_docx(cols, rows, [cw]*n)

    # ── Statistiques ─────────────────────────────────────────────────────────
    if rd["stats"]:
        _add_heading("Statistiques numériques")
        hdr   = ["Colonne", "Min", "Max", "Moyenne", "Somme", "N"]
        sdata = [[c, f"{s['min']:,.2f}", f"{s['max']:,.2f}",
                  f"{s['mean']:,.2f}", f"{s['sum']:,.2f}", str(s["count"])]
                 for c, s in rd["stats"].items()]
        wcols = [content_cm * 0.28] + [content_cm * 0.72 / 5] * 5
        _tbl_docx(hdr, sdata, wcols, hdr_fill="0F172A")

    # ── Fiches clients ────────────────────────────────────────────────────────
    df_full    = rd["df"]
    has_nom    = "nom"         in df_full.columns
    has_prenom = "prenom"      in df_full.columns
    has_dest   = "destination" in df_full.columns
    _id_col    = _find_col(df_full, "id", "clients_id")
    _stat_col  = _find_col(df_full, "statut", "clients_statut")

    if has_nom and has_prenom:
        # Séparateur
        p_hr = doc.add_paragraph()
        p_hr.paragraph_format.space_before = Pt(10)
        p_hr.paragraph_format.space_after  = Pt(4)
        pPr2 = p_hr._p.get_or_add_pPr()
        pBdr2= OxmlElement("w:pBdr")
        btm2 = OxmlElement("w:bottom")
        btm2.set(qn("w:val"),   "single")
        btm2.set(qn("w:sz"),    "4")
        btm2.set(qn("w:space"), "1")
        btm2.set(qn("w:color"), "E2E8F0")
        pBdr2.append(btm2)
        pPr2.append(pBdr2)
        _add_heading("Fiches clients")

        CONT_C = {"Asie": "B45309", "Europe": "1D4ED8", "Amérique": "16A34A",
                  "Afrique": "DC2626", "Océanie": "7C3AED"}

        def _run(para, text, size=9, bold=False, color="1e293b", italic=False):
            r = para.add_run(text)
            r.bold   = bold
            r.italic = italic
            r.font.size      = Pt(size)
            r.font.color.rgb = _rgb(color.lstrip("#"))
            return r

        if has_dest and _id_col:
            for cid, grp in df_full.groupby(_id_col, sort=False):
                r0     = grp.iloc[0]
                prenom = r0.get("prenom", "")
                nom    = r0.get("nom",    "")
                ville  = r0.get("ville",  "")
                email  = r0.get("email",  "")
                statut = r0.get(_stat_col) if _stat_col else r0.get("statut", "")
                s_col  = "16A34A" if statut == "actif" else "DC2626"
                n_v    = len(grp)

                # Entête client
                ph = doc.add_paragraph()
                ph.paragraph_format.space_before = Pt(10)
                ph.paragraph_format.space_after  = Pt(2)
                _run(ph, f"{prenom} {nom}", size=10, bold=True, color="0f172a")
                _run(ph, f"   {ville}", size=8.5, color="6b7280")
                if email:
                    _run(ph, f"  ·  {email}", size=8.5, color="6b7280")
                _run(ph, f"   {'actif' if statut == 'actif' else 'inactif'}",
                     size=8.5, color=s_col)
                _run(ph, f"  ·  {n_v} voyage(s)", size=8.5, color="6366f1")

                # Voyages
                for _, vr in grp.iterrows():
                    dest   = vr.get("destination", "")
                    pays   = vr.get("pays_destination", "")
                    cont   = vr.get("continent", "")
                    d_dep  = str(vr.get("date_depart",  ""))[:10]
                    d_ret  = str(vr.get("date_retour", ""))[:10]
                    duree  = vr.get("duree_jours")
                    tv     = vr.get("type_voyage", "")
                    budget = vr.get("budget")
                    note   = vr.get("note")
                    c_col  = CONT_C.get(cont, "6b7280")
                    stars  = "\u2605" * int(note) if note and not pd.isna(note) else "\u2014"
                    bgt    = f"{int(budget):,}\u20ac" if budget and not pd.isna(budget) else "\u2014"
                    duree_s = f"  ·  {int(duree)}j" if duree and not pd.isna(duree) else ""

                    pv = doc.add_paragraph()
                    pv.paragraph_format.space_after  = Pt(1)
                    pv.paragraph_format.left_indent  = Pt(14)
                    _run(pv, "\u25b8  ", size=9, color=c_col, bold=True)
                    _run(pv, dest, size=9, bold=True, color="1e3a5f")
                    _run(pv, f"   {pays}{duree_s}  ·  {d_dep} \u2192 {d_ret}  ·  {tv}",
                         size=8, color="94a3b8")
                    _run(pv, f"   {bgt}", size=9, color="16a34a")
                    _run(pv, f"  {stars}", size=8, color="b45309")

                # Filet
                p_sep = doc.add_paragraph()
                p_sep.paragraph_format.space_before = Pt(4)
                p_sep.paragraph_format.space_after  = Pt(0)
                pPr3  = p_sep._p.get_or_add_pPr()
                pBdr3 = OxmlElement("w:pBdr")
                b3    = OxmlElement("w:bottom")
                b3.set(qn("w:val"),   "single")
                b3.set(qn("w:sz"),    "2")
                b3.set(qn("w:space"), "1")
                b3.set(qn("w:color"), "F1F5F9")
                pBdr3.append(b3)
                pPr3.append(pBdr3)

        else:
            # Clients seuls
            for _, r in df_full.iterrows():
                prenom = r.get("prenom", "")
                nom    = r.get("nom",    "")
                ville  = r.get("ville",  "")
                email  = r.get("email",  "")
                tel    = r.get("telephone", "")
                di     = r.get("date_inscription", "")
                statut = r.get(_stat_col) if _stat_col else r.get("statut", "")
                s_col  = "16A34A" if statut == "actif" else "DC2626"

                pc = doc.add_paragraph()
                pc.paragraph_format.space_before = Pt(8)
                pc.paragraph_format.space_after  = Pt(2)
                _run(pc, f"{prenom} {nom}", size=10, bold=True, color="0f172a")
                _run(pc, f"  ·  {ville}", size=8.5, color="6b7280")
                _run(pc, f"  ·  {'actif' if statut == 'actif' else 'inactif'}",
                     size=8.5, color=s_col)
                meta = []
                if email: meta.append(email)
                if tel:   meta.append(tel)
                if di:    meta.append(f"Membre depuis {str(di)[:10]}")
                if meta:
                    pm = doc.add_paragraph("   ·   ".join(meta))
                    pm.runs[0].font.size = Pt(8.5)
                    pm.runs[0].font.color.rgb = _rgb("6b7280")
                    pm.paragraph_format.space_after = Pt(2)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@st.dialog("📄 Générer un rapport")
def _rapport_dialog(df, conditions, current_table, joins, last_where):
    """Boîte de dialogue de configuration et téléchargement du rapport."""
    st.markdown(
        f"<p style='color:#94a3b8;font-size:.85rem;'>"
        f"{len(df)} lignes · {len(df.columns)} colonnes · table <b>{current_table}</b></p>",
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    fmt     = c1.selectbox("Format", ["PDF", "Word (.docx)"], key="rpt_fmt")
    max_r   = c2.number_input(
        "Lignes max.", min_value=1, max_value=len(df),
        value=min(len(df), 500), step=max(1, min(50, len(df))), key="rpt_maxrows",
    )

    if st.button("⬇ Générer", type="primary", width="stretch", key="rpt_gen"):
        with st.spinner("Génération en cours…"):
            rd = _report_data(df, conditions, current_table, joins, last_where)
            try:
                if fmt == "PDF":
                    data  = generate_report_pdf(rd, max_rows=int(max_r))
                    fname = f"rapport_{current_table}.pdf"
                    mime  = "application/pdf"
                else:
                    data  = generate_report_docx(rd, max_rows=int(max_r))
                    fname = f"rapport_{current_table}.docx"
                    mime  = ("application/vnd.openxmlformats-officedocument"
                             ".wordprocessingml.document")
                st.download_button(
                    f"⬇  Télécharger  {fname}",
                    data=data, file_name=fname, mime=mime,
                    key="rpt_dl", use_container_width=True, type="primary",
                )
            except ImportError as e:
                st.error(
                    f"Bibliothèque manquante : `{e}`\n\n"
                    f"Ajoutez `{'reportlab' if fmt == 'PDF' else 'python-docx'}` "
                    f"à votre `requirements.txt` et redémarrez l'app.")
            except Exception as e:
                st.error(f"Erreur de génération : {e}")



# ══════════════════════════════════════════════════════════════════════════════
# MODULE PERSONNEL  —  affectations, mutations annuelles, rapport RH
# ══════════════════════════════════════════════════════════════════════════════

_CONT_COL_P = {
    "Europe": "#3b82f6", "Asie": "#f59e0b", "Amérique": "#10b981",
    "Afrique": "#ef4444", "Océanie": "#8b5cf6",
}


def _load_personnel_data(db: "DBAdapter") -> dict:
    """Charge toutes les données RH nécessaires aux vues et au rapport."""
    current = db.read_sql("""
        SELECT e.id, e.nom, e.prenom, e.poste, e.statut, e.date_embauche,
               a.agence, a.ville, a.pays, a.continent, a.date_debut
        FROM employes e
        JOIN affectations a ON e.id = a.employe_id
        WHERE a.date_fin IS NULL
        ORDER BY a.continent, a.pays, e.nom
    """)
    mutations = db.read_sql("""
        SELECT
            e.id AS employe_id, e.nom, e.prenom, e.poste,
            a_prev.pays       AS pays_depart,
            a_prev.continent  AS cont_depart,
            a_prev.agence     AS agence_depart,
            a_curr.pays       AS pays_arrivee,
            a_curr.continent  AS cont_arrivee,
            a_curr.agence     AS agence_arrivee,
            a_curr.ville      AS ville_arrivee,
            a_curr.date_debut AS date_mutation,
            CAST(strftime('%Y', a_curr.date_debut) AS INTEGER) AS annee
        FROM affectations a_curr
        JOIN affectations a_prev
          ON  a_prev.employe_id = a_curr.employe_id
          AND a_prev.date_fin   = (
                SELECT MAX(date_fin) FROM affectations
                WHERE employe_id = a_curr.employe_id
                  AND date_fin  < a_curr.date_debut
              )
        JOIN employes e ON e.id = a_curr.employe_id
        WHERE a_curr.date_debut >= '2019-01-01'
        ORDER BY a_curr.date_debut DESC
    """)
    all_aff = db.read_sql("""
        SELECT a.*, e.nom, e.prenom, e.poste, e.statut
        FROM affectations a
        JOIN employes e ON e.id = a.employe_id
        ORDER BY a.date_debut
    """)
    return {"current": current, "mutations": mutations, "all_aff": all_aff}


def generate_report_mutations_pdf(data: dict, year_from: int, year_to: int) -> bytes:
    """Rapport PDF annuel des mutations du personnel (reportlab)."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib             import colors
    from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units       import cm
    from reportlab.platypus        import (SimpleDocTemplate, Paragraph, Spacer,
                                            Table, TableStyle, HRFlowable, PageBreak)
    from datetime import datetime as _dt

    mut   = data["mutations"]
    cur   = data["current"]
    buf   = io.BytesIO()
    W, _H = A4
    M     = 2.2 * cm
    doc   = SimpleDocTemplate(buf, pagesize=A4,
                               leftMargin=M, rightMargin=M,
                               topMargin=2.5*cm, bottomMargin=2*cm)
    cw    = W - 2 * M

    styles = getSampleStyleSheet()
    BLUE   = colors.HexColor("#1d4ed8")
    LGRAY  = colors.HexColor("#f8fafc")
    GRAY   = colors.HexColor("#e2e8f0")
    DARK   = colors.HexColor("#0f172a")
    MUTED  = colors.HexColor("#6b7280")

    S_TITLE = ParagraphStyle("T",  parent=styles["Title"],   fontSize=17, spaceAfter=2,
                              textColor=DARK)
    S_SUB   = ParagraphStyle("Su", parent=styles["Normal"],  fontSize=9,  spaceAfter=12,
                              textColor=MUTED)
    S_H1    = ParagraphStyle("H1", parent=styles["Heading1"],fontSize=12, spaceBefore=14,
                              spaceAfter=6, textColor=colors.HexColor("#1e3a5f"))
    S_H2    = ParagraphStyle("H2", parent=styles["Heading2"],fontSize=10, spaceBefore=10,
                              spaceAfter=4, textColor=colors.HexColor("#334155"))
    S_BODY  = ParagraphStyle("B",  parent=styles["Normal"],  fontSize=9,  leading=14,
                              spaceAfter=3)

    def _tbl(data, cws, hbg=BLUE):
        t = Table(data, colWidths=cws, repeatRows=1)
        cmds = [
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,0), (-1,-1), 8),
            ("BACKGROUND",    (0,0), (-1,0),  hbg),
            ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
            ("GRID",          (0,0), (-1,-1), 0.3, GRAY),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ]
        for i in range(1, len(data)):
            cmds.append(("BACKGROUND", (0,i), (-1,i), LGRAY if i%2==0 else colors.white))
        t.setStyle(TableStyle(cmds))
        return t

    # Filtrer par période
    if not mut.empty and "annee" in mut.columns:
        mut_p = mut[(mut["annee"] >= year_from) & (mut["annee"] <= year_to)].copy()
    else:
        mut_p = pd.DataFrame()

    story = []

    # ── Couverture ────────────────────────────────────────────────────────────
    story.append(Paragraph("Rapport des Mutations du Personnel", S_TITLE))
    story.append(Paragraph(
        f"Agence de voyages  ·  Période {year_from}–{year_to}  ·  "
        f"Généré le {_dt.now().strftime('%d/%m/%Y')}", S_SUB))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=14))

    # ── Résumé exécutif ───────────────────────────────────────────────────────
    story.append(Paragraph("Résumé exécutif", S_H1))
    n_mut      = len(mut_p)
    n_employes = mut_p["employe_id"].nunique() if not mut_p.empty else 0
    n_pays_imp = len(set(list(mut_p.get("pays_depart", pd.Series()).unique()) +
                         list(mut_p.get("pays_arrivee", pd.Series()).unique()))) if not mut_p.empty else 0
    n_actifs   = len(cur)
    smry = [["Indicateur", "Valeur"],
            ["Employés actifs (postes actuels)",   str(n_actifs)],
            ["Mutations sur la période",           str(n_mut)],
            ["Employés ayant muté",                str(n_employes)],
            ["Pays impliqués",                     str(n_pays_imp)],
            ["Moyenne mutations / an",
             f"{n_mut / max(year_to - year_from + 1, 1):.1f}"]]
    story.append(_tbl(smry, [cw*0.55, cw*0.45],
                       hbg=colors.HexColor("#dbeafe")))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Sur la période {year_from}–{year_to}, l'agence a enregistré "
        f"<b>{n_mut} mutation(s)</b> impliquant <b>{n_employes} employé(s)</b> "
        f"dans <b>{n_pays_imp} pays</b>.", S_BODY))

    # ── Analyse par année ─────────────────────────────────────────────────────
    story.append(Paragraph("Analyse par année", S_H1))
    if not mut_p.empty:
        by_year = (mut_p.groupby("annee")
                        .agg(nb_mutations=("employe_id", "count"),
                             nb_employes=("employe_id", "nunique"),
                             pays_dest=("pays_arrivee", "nunique"))
                        .reset_index()
                        .sort_values("annee"))
        hdr = ["Année", "Mutations", "Employés mutés", "Pays de destination"]
        rows = [hdr] + [[str(int(r["annee"])), str(r["nb_mutations"]),
                          str(r["nb_employes"]),   str(r["pays_dest"])]
                         for _, r in by_year.iterrows()]
        story.append(_tbl(rows, [cw*0.2, cw*0.25, cw*0.3, cw*0.25]))
    else:
        story.append(Paragraph("Aucune mutation sur la période sélectionnée.", S_BODY))

    # ── Top pays d'accueil ────────────────────────────────────────────────────
    story.append(Paragraph("Pays d'accueil les plus fréquents", S_H1))
    if not mut_p.empty and "pays_arrivee" in mut_p.columns:
        top_pays = mut_p["pays_arrivee"].value_counts().head(8)
        hdr2 = ["Pays d'accueil", "Nb mutations", "Employés"]
        rows2 = [hdr2]
        for pays, nb in top_pays.items():
            emp = mut_p[mut_p["pays_arrivee"]==pays]["employe_id"].nunique()
            rows2.append([pays, str(nb), str(emp)])
        story.append(_tbl(rows2, [cw*0.5, cw*0.25, cw*0.25]))

    # ── Employés les plus mobiles ─────────────────────────────────────────────
    story.append(Paragraph("Employés les plus mobiles", S_H1))
    if not mut_p.empty:
        mob = (mut_p.groupby(["employe_id", "nom", "prenom", "poste"])
                    .size().reset_index(name="nb_mutations")
                    .sort_values("nb_mutations", ascending=False).head(10))
        hdr3 = ["Nom", "Prénom", "Poste", "Mutations"]
        rows3 = [hdr3] + [[r["nom"], r["prenom"], r["poste"], str(r["nb_mutations"])]
                           for _, r in mob.iterrows()]
        story.append(_tbl(rows3, [cw*0.22, cw*0.22, cw*0.38, cw*0.18]))

    # ── Détail des mutations ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Détail chronologique des mutations", S_H1))
    if not mut_p.empty:
        hdr4 = ["Date", "Employé", "Poste", "Départ", "Arrivée"]
        rows4 = [hdr4]
        for _, r in mut_p.sort_values("date_mutation", ascending=False).iterrows():
            rows4.append([
                str(r.get("date_mutation",""))[:10],
                f"{r.get('prenom','')} {r.get('nom','')}",
                r.get("poste",""),
                f"{r.get('agence_depart','')} ({r.get('pays_depart','')})",
                f"{r.get('agence_arrivee','')} ({r.get('pays_arrivee','')})",
            ])
        story.append(_tbl(rows4, [cw*0.1, cw*0.2, cw*0.2, cw*0.25, cw*0.25]))

    doc.build(story)
    return buf.getvalue()


def generate_report_mutations_docx(data: dict, year_from: int, year_to: int) -> bytes:
    """Rapport Word des mutations du personnel (python-docx)."""
    import io
    from docx            import Document
    from docx.shared     import Pt, Cm as _Cm, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns    import qn
    from docx.oxml       import OxmlElement
    from datetime import datetime as _dt

    mut   = data["mutations"]
    cur   = data["current"]
    doc   = Document()
    sec   = doc.sections[0]
    sec.page_width  = _Cm(21); sec.page_height = _Cm(29.7)
    sec.left_margin = sec.right_margin = _Cm(2.5)
    sec.top_margin  = sec.bottom_margin = _Cm(2)
    content_cm = 21 - 5

    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)

    def _rgb(h): return RGBColor(int(h[:2],16),int(h[2:4],16),int(h[4:],16))
    def _shd(cell, fill):
        tc=cell._tc; tcPr=tc.get_or_add_tcPr()
        for old in tcPr.findall(qn("w:shd")): tcPr.remove(old)
        shd=OxmlElement("w:shd")
        shd.set(qn("w:val"),"clear"); shd.set(qn("w:color"),"auto")
        shd.set(qn("w:fill"),fill.upper()); tcPr.append(shd)
    def _heading(txt, color="0f172a", size=14):
        p=doc.add_paragraph(); r=p.add_run(txt)
        r.bold=True; r.font.size=Pt(size); r.font.color.rgb=_rgb(color)
        p.paragraph_format.space_before=Pt(12); p.paragraph_format.space_after=Pt(5)
    def _tbl(hdr, rows, cws, hfill="1D4ED8"):
        n=len(hdr); t=doc.add_table(rows=1,cols=n); t.style="Table Grid"
        t.alignment=WD_TABLE_ALIGNMENT.LEFT
        hcells=t.rows[0].cells
        for i,h in enumerate(hdr):
            hcells[i].text=str(h); hcells[i].width=_Cm(cws[i])
            r2=hcells[i].paragraphs[0].runs[0]; r2.bold=True; r2.font.size=Pt(8)
            r2.font.color.rgb=_rgb("FFFFFF"); _shd(hcells[i],hfill)
        for ri,row in enumerate(rows):
            cells=t.add_row().cells; fill="F8FAFC" if ri%2==0 else "FFFFFF"
            for i,v in enumerate(row):
                cells[i].text=str(v); cells[i].width=_Cm(cws[i])
                for rx in cells[i].paragraphs[0].runs: rx.font.size=Pt(8)
                _shd(cells[i],fill)
        return t

    if not mut.empty and "annee" in mut.columns:
        mut_p = mut[(mut["annee"] >= year_from) & (mut["annee"] <= year_to)].copy()
    else:
        mut_p = pd.DataFrame()

    # Titre
    p=doc.add_paragraph(); r=p.add_run("Rapport des Mutations du Personnel")
    r.bold=True; r.font.size=Pt(17); r.font.color.rgb=_rgb("0f172a")
    p.paragraph_format.space_after=Pt(2)
    p2=doc.add_paragraph(f"Période {year_from}–{year_to}  ·  Généré le {_dt.now().strftime('%d/%m/%Y')}")
    p2.runs[0].font.size=Pt(9); p2.runs[0].font.color.rgb=_rgb("6b7280")
    p2.paragraph_format.space_after=Pt(6)

    # Résumé
    _heading("Résumé exécutif")
    n_mut=len(mut_p); n_emp=mut_p["employe_id"].nunique() if not mut_p.empty else 0
    smry=[["Employés actifs",str(len(cur))],["Mutations",str(n_mut)],
          ["Employés mutés",str(n_emp)],
          ["Moy. mutations/an",f"{n_mut/max(year_to-year_from+1,1):.1f}"]]
    _tbl(["Indicateur","Valeur"],smry,[content_cm*0.55,content_cm*0.45],
         hfill="DBEAFE")

    # Par année
    _heading("Par année")
    if not mut_p.empty:
        by_y=(mut_p.groupby("annee").agg(nb=("employe_id","count"),
              emp=("employe_id","nunique")).reset_index().sort_values("annee"))
        _tbl(["Année","Mutations","Employés mutés"],
             [[str(int(r["annee"])),str(r["nb"]),str(r["emp"])] for _,r in by_y.iterrows()],
             [content_cm*0.25,content_cm*0.4,content_cm*0.35])

    # Top pays
    _heading("Pays d'accueil les plus fréquents")
    if not mut_p.empty and "pays_arrivee" in mut_p.columns:
        top=mut_p["pays_arrivee"].value_counts().head(8)
        _tbl(["Pays","Mutations"],[[p,str(n)] for p,n in top.items()],
             [content_cm*0.6,content_cm*0.4])

    # Employés mobiles
    _heading("Employés les plus mobiles")
    if not mut_p.empty:
        mob=(mut_p.groupby(["nom","prenom","poste"]).size()
                  .reset_index(name="n").sort_values("n",ascending=False).head(10))
        _tbl(["Nom","Prénom","Poste","Nb mutations"],
             [[r["nom"],r["prenom"],r["poste"],str(r["n"])] for _,r in mob.iterrows()],
             [content_cm*0.22,content_cm*0.22,content_cm*0.38,content_cm*0.18])

    # Détail
    _heading("Détail chronologique")
    if not mut_p.empty:
        _tbl(["Date","Employé","Départ","Arrivée"],
             [[str(r.get("date_mutation",""))[:10],
               f"{r.get('prenom','')} {r.get('nom','')}",
               f"{r.get('pays_depart','')}",
               f"{r.get('ville_arrivee','')} ({r.get('pays_arrivee','')})"]
              for _,r in mut_p.sort_values("date_mutation",ascending=False).iterrows()],
             [content_cm*0.12,content_cm*0.22,content_cm*0.33,content_cm*0.33])

    buf=io.BytesIO(); doc.save(buf)
    return buf.getvalue()


@st.dialog("📋 Rapport mutations du personnel")
def _mutations_rapport_dialog(data: dict) -> None:
    mut = data.get("mutations", pd.DataFrame())
    years = sorted(mut["annee"].dropna().unique().astype(int)) if not mut.empty and "annee" in mut.columns else [2019,2024]
    y_min, y_max = (int(min(years)), int(max(years))) if years else (2019, 2024)

    st.markdown(
        f"<p style='color:#94a3b8;font-size:.85rem;'>"
        f"{len(mut)} mutation(s)  ·  {y_min}–{y_max}</p>",
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    fmt    = c1.selectbox("Format", ["PDF", "Word (.docx)"], key="mrpt_fmt")
    period = c2.select_slider(
        "Période", options=list(range(y_min, y_max+1)),
        value=(y_min, y_max), key="mrpt_period",
    )

    if st.button("⬇ Générer", type="primary", use_container_width=True, key="mrpt_gen"):
        with st.spinner("Génération…"):
            try:
                yf, yt = int(period[0]), int(period[1])
                if fmt == "PDF":
                    raw   = generate_report_mutations_pdf(data, yf, yt)
                    fname = f"mutations_personnel_{yf}_{yt}.pdf"
                    mime  = "application/pdf"
                else:
                    raw   = generate_report_mutations_docx(data, yf, yt)
                    fname = f"mutations_personnel_{yf}_{yt}.docx"
                    mime  = ("application/vnd.openxmlformats-officedocument"
                             ".wordprocessingml.document")
                st.download_button(f"⬇  {fname}", data=raw,
                                   file_name=fname, mime=mime,
                                   use_container_width=True, key="mrpt_dl")
            except Exception as e:
                st.error(f"Erreur : {e}")


def render_personnel_module() -> None:
    """Module Personnel — affectations mondiales et analyse des mutations."""
    import plotly.express as px

    db = _get_db()
    try:
        pdata = _load_personnel_data(db)
    except Exception as e:
        st.error(f"Tables `employes` / `affectations` introuvables : {e}")
        return

    cur     = pdata["current"]
    mut     = pdata["mutations"]
    all_aff = pdata["all_aff"]

    # ── Métriques ─────────────────────────────────────────────────────────────
    n_actifs   = len(cur)
    n_pays     = cur["pays"].nunique()    if not cur.empty else 0
    n_mut      = len(mut)
    n_cur_year = len(mut[mut["annee"] == pd.Timestamp.now().year]) if not mut.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Employés actifs",   n_actifs)
    m2.metric("Pays couverts",     n_pays)
    m3.metric("Mutations totales", n_mut)
    m4.metric(f"Mutations {pd.Timestamp.now().year}", n_cur_year)

    tab_map, tab_mut, tab_teams = st.tabs(
        ["🌍 Carte des effectifs", "📊 Mutations annuelles", "👥 Équipes par pays"])

    # ── TAB 1 — Carte ─────────────────────────────────────────────────────────
    with tab_map:
        if not cur.empty:
            emp_by_country = (cur.groupby("pays")
                                 .agg(nb_employes=("id","count"),
                                      continents=("continent", lambda x: x.iloc[0]))
                                 .reset_index())
            emp_by_country["iso_alpha"] = emp_by_country["pays"].map(COUNTRY_ISO_MAP)

            fig = px.choropleth(
                emp_by_country,
                locations="iso_alpha",
                color="nb_employes",
                hover_name="pays",
                hover_data={"iso_alpha": False, "nb_employes": "Employés"},
                color_continuous_scale=[[0,"#172554"],[0.4,"#1d4ed8"],[1,"#93c5fd"]],
                custom_data=["pays"],
            )
            _map_geo_layout(fig, 400)
            st.plotly_chart(fig, use_container_width=True, key="pers_map")

            # Bouton rapport
            btn_c, _ = st.columns([2, 8])
            with btn_c:
                if st.button("📋 Rapport mutations", key="pers_rpt_btn",
                             use_container_width=True):
                    _mutations_rapport_dialog(pdata)
        else:
            st.info("Aucun employé actif trouvé.")

    # ── TAB 2 — Mutations par année ───────────────────────────────────────────
    with tab_mut:
        if not mut.empty:
            by_year = (mut.groupby("annee")
                          .agg(nb_mutations=("employe_id","count"),
                               nb_employes=("employe_id","nunique"))
                          .reset_index())
            by_year["annee_str"] = by_year["annee"].astype(str)

            fig2 = px.bar(
                by_year, x="annee_str", y="nb_mutations",
                text="nb_mutations",
                color_discrete_sequence=["#3b82f6"],
                labels={"annee_str": "Année", "nb_mutations": "Mutations"},
            )
            fig2.update_traces(textposition="outside")
            fig2.update_layout(
                paper_bgcolor="#0d0f14", plot_bgcolor="#0d0f14",
                font_color="#e8eaf0", showlegend=False,
                margin=dict(l=0,r=0,t=20,b=0), height=300,
                xaxis=dict(gridcolor="#1e2130"),
                yaxis=dict(gridcolor="#1e2130"),
            )
            st.plotly_chart(fig2, use_container_width=True, key="mut_bar")

            # Détail des mutations récentes
            st.markdown(
                "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                "letter-spacing:1px;font-family:JetBrains Mono,monospace;margin:12px 0 8px;'>"
                "Détail des mutations</div>", unsafe_allow_html=True)

            for _, r in mut.head(20).iterrows():
                c_dep = _CONT_COL_P.get(r.get("cont_depart",""), "#6b7280")
                c_arr = _CONT_COL_P.get(r.get("cont_arrivee",""), "#6b7280")
                st.markdown(
                    f"<div style='background:#13151d;border:1px solid #1e2130;"
                    f"border-radius:10px;padding:9px 16px;margin-bottom:6px;"
                    f"display:flex;align-items:center;gap:12px;'>"
                    f"<span style='font-size:.72rem;color:#475569;font-family:JetBrains Mono;"
                    f"white-space:nowrap;'>{str(r.get('date_mutation',''))[:10]}</span>"
                    f"<span style='font-weight:600;color:#e8eaf0;min-width:130px;'>"
                    f"{r.get('prenom','')} {r.get('nom','')}</span>"
                    f"<span style='font-size:.75rem;color:#64748b;'>{r.get('poste','')}</span>"
                    f"<span style='flex:1;text-align:right;font-size:.8rem;'>"
                    f"<span style='color:{c_dep};'>{r.get('pays_depart','')}</span>"
                    f"<span style='color:#475569;'>  →  </span>"
                    f"<span style='color:{c_arr};'>{r.get('pays_arrivee','')}</span>"
                    f"</span></div>",
                    unsafe_allow_html=True)
        else:
            st.info("Aucune mutation enregistrée.")

    # ── TAB 3 — Équipes par pays ───────────────────────────────────────────────
    with tab_teams:
        if not cur.empty:
            postes = {"Directeur Régional":"#6366f1","Agent Commercial":"#3b82f6",
                      "Responsable Visa":"#10b981","Responsable Opérations":"#f59e0b"}
            for pays, grp in cur.groupby("pays", sort=True):
                cont  = grp.iloc[0]["continent"]
                c_col = _CONT_COL_P.get(cont, "#6b7280")
                st.markdown(
                    f"<div style='color:{c_col};font-size:.75rem;font-weight:500;"
                    f"text-transform:uppercase;letter-spacing:1px;"
                    f"font-family:JetBrains Mono,monospace;margin:14px 0 6px;'>"
                    f"{pays}  ·  {cont}  ·  {len(grp)} poste(s)</div>",
                    unsafe_allow_html=True)
                for _, emp in grp.iterrows():
                    p_col = postes.get(emp.get("poste",""), "#94a3b8")
                    ini   = (str(emp.get("nom","?"))[:1]+str(emp.get("prenom","?"))[:1]).upper()
                    st.markdown(
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-radius:9px;padding:8px 14px;margin-bottom:5px;"
                        f"display:flex;align-items:center;gap:10px;'>"
                        f"<div style='width:30px;height:30px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;font-size:.8rem;color:white;flex-shrink:0;'>{ini}</div>"
                        f"<div style='flex:1;'>"
                        f"<span style='font-weight:600;color:#e8eaf0;'>"
                        f"{emp.get('prenom','')} {emp.get('nom','')}</span>"
                        f"  <span style='font-size:.75rem;color:#64748b;'>"
                        f"{emp.get('agence','')}</span></div>"
                        f"<span style='font-size:.72rem;padding:2px 8px;border-radius:20px;"
                        f"background:{p_col}22;color:{p_col};white-space:nowrap;'>"
                        f"{emp.get('poste','')}</span>"
                        f"<span style='font-size:.7rem;color:#475569;margin-left:6px;'>"
                        f"depuis {str(emp.get('date_debut',''))[:10]}</span>"
                        f"</div>", unsafe_allow_html=True)
        else:
            st.info("Aucune affectation active.")


# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# FICHE PROFIL CLIENT — fonction exportable
# ══════════════════════════════════════════════════════════════════════════════

def _safe_get(data, col, default="—"):
    """
    Accède à data[col] de manière résiliente.
    Retourne default si la colonne est absente, None, NaN, ou vide.
    Compatible avec dict, pd.Series et tout objet subscriptable.

    Exemples
    --------
    _safe_get(row, "email")            → valeur ou "—"
    _safe_get(row, "note", default=0)  → 0 si absent / NaN
    _safe_get(None, "col")             → "—"
    """
    import math
    if data is None:
        return default
    try:
        if hasattr(data, "get") and callable(data.get):
            val = data.get(col)
        elif hasattr(data, "index") and col in data.index:
            val = data[col]
        else:
            return default
    except (KeyError, IndexError, TypeError):
        return default
    if val is None:
        return default
    try:
        if math.isnan(float(val)):
            return default
    except (ValueError, TypeError):
        pass
    if isinstance(val, str) and not val.strip():
        return default
    return val


# ══════════════════════════════════════════════════════════════════════════════
# ENRICHISSEMENT ASYNC DES FICHES CLIENT
# ──────────────────────────────────────────────────────────────────────────────
# Pattern : un thread fait l'appel API et écrit dans un store global thread-safe.
# Un st.fragment(run_every="1s") sur la carte lit le store et bascule du spinner
# au résultat dès que celui-ci est disponible — sans recharger toute la page.
# ══════════════════════════════════════════════════════════════════════════════
import threading
from concurrent.futures import ThreadPoolExecutor

# Store global : { client_id -> {"status": "loading|done|error", "data": ..., "error": ...} }
_enrich_store: dict = {}
_enrich_lock                  = threading.Lock()
_enrich_executor              = ThreadPoolExecutor(
    max_workers=8, thread_name_prefix="client-enrich"
)


def _do_client_enrichment(client_id, snapshot: dict) -> dict:
    """
    ⚠️  À REMPLACER par votre vrai appel API.

    Reçoit un `snapshot` contenant les valeurs FR à traduire :
        {
          "profession":    "Ingénieur",
          "situation_pro": "Salarié",
          "destinations":  ["Paris", "Maroc", ...],
          "types_voyage":  ["loisir", "affaires"],
          ...
        }

    Doit renvoyer un dict avec une clé "translations" qui contient les
    traductions EN pour chacune des valeurs FR :
        {
          "translations": {
            "profession":    {"Ingénieur": "Engineer"},
            "situation_pro": {"Salarié": "Employed"},
            "destinations":  {"Paris": "Paris", "Maroc": "Morocco", ...},
            "types_voyage":  {"loisir": "Leisure", "affaires": "Business"},
          }
        }

    Les clés absentes du dict ne reçoivent pas de badge — le rendu est tolérant.
    """
    # ── Simulation d'un appel API qui prend 0.5 à 1.5 seconde ──
    import time, random
    time.sleep(random.uniform(0.5, 1.5))

    # Dictionnaire de traductions FR→EN (à remplacer par votre vrai appel API)
    _FR_EN = {
        # Professions
        "Ingénieur":           "Engineer",
        "Médecin":             "Doctor",
        "Avocat":              "Lawyer",
        "Enseignant":          "Teacher",
        "Comptable":           "Accountant",
        "Architecte":          "Architect",
        "Développeur":         "Developer",
        "Commercial":          "Sales Rep",
        "Consultant":          "Consultant",
        "Infirmier":           "Nurse",
        "Infirmière":          "Nurse",
        "Pharmacien":          "Pharmacist",
        "Chef de projet":      "Project Manager",
        "Directeur":           "Director",
        "Étudiant":            "Student",
        "Retraité":            "Retired",
        "Artisan":             "Craftsman",
        "Journaliste":         "Journalist",
        "Chercheur":           "Researcher",
        "Designer":            "Designer",
        # Situations pro
        "Salarié":             "Employee",
        "Indépendant":         "Self-employed",
        "Fonctionnaire":       "Civil Servant",
        "Étudiant":            "Student",
        "Retraité":            "Retired",
        "Sans emploi":         "Unemployed",
        "Chef d'entreprise":   "Business Owner",
        "Intérimaire":         "Temp Worker",
        "Apprenti":            "Apprentice",
        "Stagiaire":           "Intern",
        # Types de voyage
        "loisir":              "leisure",
        "Loisir":              "Leisure",
        "affaires":            "business",
        "Affaires":            "Business",
        "tourisme":            "tourism",
        "Tourisme":            "Tourism",
        "professionnel":       "professional",
        "Professionnel":       "Professional",
        "famille":             "family",
        "Famille":             "Family",
        # Destinations / pays (mêmes noms ou variants)
        "Maroc":               "Morocco",
        "Espagne":             "Spain",
        "Italie":              "Italy",
        "Allemagne":           "Germany",
        "Royaume-Uni":         "United Kingdom",
        "Grèce":               "Greece",
        "Belgique":            "Belgium",
        "Suisse":              "Switzerland",
        "Pays-Bas":            "Netherlands",
        "États-Unis":          "United States",
        "Égypte":              "Egypt",
        "Tunisie":             "Tunisia",
        "Brésil":              "Brazil",
        "Inde":                "India",
        "Chine":               "China",
        "Japon":               "Japan",
        "Australie":           "Australia",
        "Canada":              "Canada",
        "Mexique":             "Mexico",
        "Turquie":             "Türkiye",
        "Russie":              "Russia",
        "Norvège":             "Norway",
        "Suède":               "Sweden",
        "Portugal":            "Portugal",
        "Pologne":             "Poland",
    }

    def translate(values):
        """Traduit une liste de valeurs, ne garde que celles trouvées."""
        result = {}
        for v in values:
            if not v or not isinstance(v, str):
                continue
            v_stripped = v.strip()
            if v_stripped in _FR_EN:
                result[v_stripped] = _FR_EN[v_stripped]
        return result

    # ── Pour test d'erreur aléatoire, dé-commenter :
    # if random.random() < 0.1: raise RuntimeError("API timeout")

    return {
        "translations": {
            "profession":    translate([snapshot.get("profession", "")]),
            "situation_pro": translate([snapshot.get("situation_pro", "")]),
            "destinations":  translate(snapshot.get("destinations", []) or []),
            "types_voyage":  translate(snapshot.get("types_voyage", []) or []),
        }
    }


def _enrich_worker(client_id, snapshot: dict) -> None:
    """Tourne dans le pool de threads. Catch tout, écrit dans le store global."""
    try:
        data = _do_client_enrichment(client_id, snapshot)
        with _enrich_lock:
            _enrich_store[client_id] = {"status": "done", "data": data}
    except Exception as exc:
        with _enrich_lock:
            _enrich_store[client_id] = {"status": "error", "error": str(exc)}


def get_enrichment_state(client_id) -> dict:
    """Lecture thread-safe de l'état d'enrichissement d'un client."""
    with _enrich_lock:
        return dict(_enrich_store.get(client_id, {"status": "idle"}))


def ensure_enrichment_started(client_id, snapshot: dict) -> None:
    """
    Lance l'enrichissement s'il n'a pas déjà été démarré pour ce client.
    Idempotent : peut être appelé à chaque rerun sans risque.
    """
    with _enrich_lock:
        if client_id in _enrich_store:
            return  # déjà loading/done/error, on ne relance pas
        _enrich_store[client_id] = {"status": "loading"}
    # Hors du verrou : on submit sans bloquer
    _enrich_executor.submit(_enrich_worker, client_id, snapshot)


# ──────────────────────────────────────────────────────────────────────────────
# BATCH SÉQUENTIEL : un seul thread enrichit toutes les fiches l'une après l'autre
# ──────────────────────────────────────────────────────────────────────────────
_batch_state: dict = {
    "running": False,   # True tant qu'un thread batch tourne
    "total":   0,
    "done":    0,
}
_batch_lock = threading.Lock()


def get_batch_state() -> dict:
    """Lecture thread-safe de l'état du batch global."""
    with _batch_lock:
        return dict(_batch_state)


def _batch_enrich_worker(snapshots: list) -> None:
    """
    Tourne dans UN seul thread. Boucle sur les snapshots et appelle l'API
    en série (1 appel à la fois). Chaque client est ajouté au store individuel,
    donc les cards (qui pollent via leur fragment) voient progressivement les
    résultats.
    """
    try:
        for (cid, snap) in snapshots:
            # Skip si déjà traité (idempotence)
            with _enrich_lock:
                existing = _enrich_store.get(cid)
                if existing and existing.get("status") in ("loading", "done"):
                    with _batch_lock:
                        _batch_state["done"] += 1
                    continue
                # Marquer en loading pour que la card affiche le spinner
                _enrich_store[cid] = {"status": "loading"}

            # Appel API (hors verrou pour ne pas bloquer les autres threads/lectures)
            try:
                data = _do_client_enrichment(cid, snap)
                with _enrich_lock:
                    _enrich_store[cid] = {"status": "done", "data": data}
            except Exception as exc:
                with _enrich_lock:
                    _enrich_store[cid] = {"status": "error", "error": str(exc)}

            with _batch_lock:
                _batch_state["done"] += 1
    finally:
        with _batch_lock:
            _batch_state["running"] = False


def start_batch_enrichment(snapshots: list) -> bool:
    """
    Lance un batch séquentiel. Si un batch est déjà en cours, ne fait rien
    et renvoie False. Sinon True.
    """
    with _batch_lock:
        if _batch_state["running"]:
            return False
        _batch_state["running"] = True
        _batch_state["total"]   = len(snapshots)
        _batch_state["done"]    = 0

    # Thread daemon, séparé du pool (un seul thread = série stricte)
    t = threading.Thread(
        target=_batch_enrich_worker,
        args=(snapshots,),
        daemon=True,
        name="batch-enrich-sequential",
    )
    t.start()
    return True


@st.fragment(run_every="0.8s")
def render_client_enrichment_block(client_id, snapshot: dict, accent_color: str = "#a78bfa"):
    """
    Bloc d'enrichissement async, intégrable dans n'importe quelle carte.

    Comportement (déclenchement géré par un bouton global, pas individuel) :
    • État initial (idle)   → n'affiche rien (le bouton global n'a pas été cliqué)
    • Pendant le chargement → spinner animé, le fragment poll toutes les 0.8s
    • Une fois terminé      → affiche les valeurs renvoyées par l'API (chips)
    • En cas d'erreur       → bandeau rouge avec message

    Le polling continue après le done mais ne fait qu'une lecture dict — coût
    négligeable.
    """
    # snapshot n'est plus utilisé ici (pas de déclenchement individuel),
    # on le garde dans la signature pour compatibilité.
    state = get_enrichment_state(client_id)

    # ── État INITIAL (idle) : ne rien afficher ───────────────────────────────
    if state["status"] == "idle":
        return

    # ── État LOADING : spinner ────────────────────────────────────────────────
    if state["status"] == "loading":
        st.markdown(
            f"<div style='background:#0f1118;border:1px solid #1e2130;"
            f"border-left:3px solid {accent_color};border-radius:8px;"
            f"padding:8px 14px;margin:6px 0;display:flex;align-items:center;gap:10px;"
            f"font-family:JetBrains Mono,monospace;font-size:.78rem;color:#94a3b8;'>"
            f"<span class='spinner' style='display:inline-block;width:12px;height:12px;"
            f"border:2px solid #2a2d3e;border-top-color:{accent_color};border-radius:50%;"
            f"animation:spin 0.8s linear infinite;'></span>"
            f"<span>Enrichissement en cours…</span>"
            f"</div>"
            f"<style>@keyframes spin{{to{{transform:rotate(360deg);}}}}</style>",
            unsafe_allow_html=True,
        )
        return

    # ── État ERROR : bandeau rouge ────────────────────────────────────────────
    if state["status"] == "error":
        st.markdown(
            f"<div style='background:#1a0f0f;border:1px solid #ef4444;"
            f"border-left:3px solid #ef4444;border-radius:8px;"
            f"padding:8px 14px;margin:6px 0;"
            f"font-family:JetBrains Mono,monospace;font-size:.78rem;color:#fca5a5;'>"
            f"⚠️ Enrichissement indisponible "
            f"<span style='opacity:.7;'>({state.get('error','erreur inconnue')})</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    # ── État DONE : récap des traductions effectuées ─────────────────────────
    data = state.get("data") or {}
    translations = data.get("translations") or {}

    # Compter le nombre total de traductions effectuées
    n_total = sum(len(v) for v in translations.values())

    if n_total == 0:
        # Rien à traduire trouvé
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#0f1118,#13151d);"
            f"border:1px solid #1e2130;border-left:3px solid {accent_color};"
            f"border-radius:8px;padding:8px 14px;margin:6px 0;"
            f"font-family:JetBrains Mono,monospace;font-size:.74rem;color:#64748b;'>"
            f"✨ Aucune traduction disponible pour cette fiche</div>",
            unsafe_allow_html=True,
        )
        return

    def section_html(label, pairs_dict):
        if not pairs_dict:
            return ""
        items = " &nbsp; ".join(
            f"<span style='color:#cbd5e1;'>{fr}</span> "
            f"<span style='color:{accent_color};'>→</span> "
            f"<span style='background:{accent_color}22;color:{accent_color};"
            f"padding:1px 7px;border-radius:6px;font-weight:600;'>{en}</span>"
            for fr, en in pairs_dict.items()
        )
        return (
            f"<div style='display:flex;align-items:flex-start;gap:10px;padding:3px 0;'>"
            f"<span style='color:#64748b;font-size:.68rem;min-width:90px;flex-shrink:0;"
            f"text-transform:uppercase;letter-spacing:.8px;'>{label}</span>"
            f"<span style='font-size:.76rem;'>{items}</span></div>"
        )

    sections = filter(None, [
        section_html("Profession",    translations.get("profession", {})),
        section_html("Situation",     translations.get("situation_pro", {})),
        section_html("Destinations",  translations.get("destinations", {})),
        section_html("Types voyage",  translations.get("types_voyage", {})),
    ])

    st.markdown(
        f"<div style='background:linear-gradient(135deg,#0f1118 0%,#13151d 100%);"
        f"border:1px solid #1e2130;border-left:3px solid {accent_color};"
        f"border-radius:8px;padding:10px 14px;margin:6px 0;"
        f"font-family:JetBrains Mono,monospace;'>"
        f"<div style='color:#94a3b8;font-size:.68rem;text-transform:uppercase;"
        f"letter-spacing:1.2px;margin-bottom:6px;'>"
        f"✨ Traductions ({n_total})</div>"
        f"{''.join(sections)}"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_client_profile_card(
    client_row,
    voyages_df=None,
    all_voyages_df=None,
    passeports_df=None,        # DataFrame des passeports de ce client
    # ── Colonnes client — coordonnées ──────────────────────────────────────────
    col_nom="nom", col_prenom="prenom", col_email="email",
    col_telephone="telephone", col_ville="ville", col_statut="statut",
    col_date_inscription="date_inscription",
    # ── Colonnes client — papiers d'identité ────────────────────────────────────
    col_num_ci="num_carte_identite",
    col_exp_ci="date_expiration_ci",
    # ── Colonnes passeports (dans passeports_df) ─────────────────────────────────
    col_pp_num="num_passeport",
    col_pp_nat="nationalite",
    col_pp_emission="date_emission",
    col_pp_expiration="date_expiration",
    # ── Colonnes client — situation professionnelle ─────────────────────────────
    col_profession="profession", col_employeur="employeur",
    col_situation_pro="situation_pro",
    # ── Colonnes voyage ─────────────────────────────────────────────────────────
    col_v_destination="destination", col_v_pays="pays_destination",
    col_v_continent="continent",    col_v_date_dep="date_depart",
    col_v_date_ret="date_retour",   col_v_duree="duree_jours",
    col_v_type="type_voyage",       col_v_transport="transport",
    col_v_hotel="hotel",            col_v_budget="budget",
    col_v_statut="statut_voyage",   col_v_note="note",
    col_v_groupe="groupe_voyage_id",
    # ── Colonnes dans all_voyages_df (compagnons) ────────────────────────────────
    col_c_client_id="client_id", col_c_nom="nom", col_c_prenom="prenom",
    col_c_profession="profession", col_c_ville="ville", col_c_statut="statut",
    # ── Options d'affichage ─────────────────────────────────────────────────────
    show_identity=True, show_professional=True, show_companions=True,
    # ── Traductions FR→EN (badges violets à côté des valeurs) ───────────────────
    translations: dict = None,
):
    """
    Affiche la fiche profil complète d'un client avec ses voyages.

    Paramètres
    ----------
    client_row      : dict ou pd.Series — données du client
    voyages_df      : DataFrame des voyages de ce client (None = pas de voyages)
    all_voyages_df  : DataFrame de TOUS les voyages avec groupe_voyage_id non nul,
                      utilisé pour trouver les compagnons. Colonnes attendues :
                      col_v_groupe, col_c_client_id, col_c_nom, col_c_prenom.
    col_*           : noms de colonnes configurables — permet de brancher la
                      fonction sur n'importe quel schéma DB sans modifier le code.
    show_identity   : afficher la section papiers d'identité
    show_professional : afficher la section situation professionnelle
    show_companions : afficher les compagnons de voyage (expander)

    Les valeurs manquantes (colonne absente, None, NaN, chaîne vide) sont
    gérées silencieusement via _safe_get — aucune ligne vide n'est rendue.
    """
    sg = lambda col, d="—": _safe_get(client_row, col, d)

    # ── Helper : ajoute un badge violet « → EN » à côté d'une valeur FR ─────────
    translations = translations or {}
    def tx_badge(category: str, fr_value):
        """
        Si une traduction EN existe pour `fr_value` dans `translations[category]`,
        retourne un fragment HTML inline « <badge>EN</badge> » à concaténer
        après la valeur FR. Sinon retourne une chaîne vide.
        """
        if not fr_value or fr_value == "—":
            return ""
        cat = translations.get(category) or {}
        en = cat.get(str(fr_value).strip())
        if not en:
            return ""
        return (
            f" <span style='background:#a78bfa22;color:#a78bfa;"
            f"border:1px solid #a78bfa55;border-radius:8px;padding:1px 7px;"
            f"font-size:.66rem;font-weight:600;font-family:JetBrains Mono,monospace;"
            f"margin-left:4px;letter-spacing:.3px;' title='Traduction EN'>"
            f"🇬🇧 {en}</span>"
        )

    # ── En-tête + Identité + Pro : un seul bloc HTML (aucun gap Streamlit) ──────
    nom     = sg(col_nom);        prenom = sg(col_prenom)
    ville   = sg(col_ville, "");  statut = sg(col_statut, "")
    email   = sg(col_email, "");  tel    = sg(col_telephone, "")
    ini     = ((prenom[:1] if prenom and prenom != "—" else "") +
               (nom[:1]   if nom    and nom    != "—" else "")).upper() or "?"
    sc      = "#4ade80" if statut == "actif" else "#f87171"
    contact_html = ""
    if email: contact_html += f"<div style='font-size:.72rem;'>{email}</div>"
    if tel:   contact_html += f"<div style='font-size:.72rem;color:#64748b;'>{tel}</div>"

    # ── Construire identité HTML ─────────────────────────────────────────────
    id_section = ""
    if show_identity:
        ci_num = sg(col_num_ci, ""); ci_exp = sg(col_exp_ci, "")
        id_rows = []
        if passeports_df is not None and not passeports_df.empty:
            from datetime import date as _date
            _today = _date.today().isoformat()
            pp_tags = []
            for _, pp in passeports_df.iterrows():
                num  = _safe_get(pp, col_pp_num, "?")
                nat  = _safe_get(pp, col_pp_nat, "")
                emis = _safe_get(pp, col_pp_emission, "")
                exp  = _safe_get(pp, col_pp_expiration, "")
                expired = bool(exp and exp != "—" and str(exp) < _today)
                bg  = "#450a0a" if expired else "#052e16"
                fg  = "#fca5a5" if expired else "#86efac"
                brd = "#ef4444" if expired else "#22c55e"
                tip = f"Nationalité : {nat} | Émis : {emis} | Exp. : {exp}"
                icon = '✗' if expired else '✓'
                lbl  = f"{icon} {num}"
                pp_tags.append(
                    f"<span class='pp-wrap' style='position:relative;display:inline-block;margin:1px;'>"
                    f"<span style='background:{bg};color:{fg};"
                    f"border:0.5px solid {brd};font-size:.7rem;padding:2px 8px;"
                    f"border-radius:20px;cursor:help;"
                    f"font-family:JetBrains Mono,monospace;display:inline-block;'>{lbl}</span>"
                    f"<span class='pp-tip'>"
                    f"<b>Nationalité</b>&nbsp;&nbsp;{nat}<br>"
                    f"<b>Émis</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{emis}<br>"
                    f"<b>Expiration</b>&nbsp;&nbsp;{exp}"
                    f"</span></span>"
                )
            if pp_tags:
                id_rows.append(("Passeports", " ".join(pp_tags)))
        if ci_num:
            id_rows.append(("Carte d'identité",
                            ci_num + (f"  ·  exp. {ci_exp}" if ci_exp else "")))
        id_body = "".join(
            f"<div style='display:flex;gap:8px;padding:5px 0;border-top:1px solid #1e2130;'><span style='color:#64748b;font-size:.72rem;min-width:100px;flex-shrink:0;'>{k}</span><span style='color:#e8eaf0;font-size:.78rem;font-family:JetBrains Mono,monospace;'>{v}</span></div>"
            for k, v in id_rows
        ) if id_rows else "<span style='color:#334155;font-size:.75rem;font-style:italic;'>Non renseigné</span>"
        _pp_css = (
            "<style>.pp-wrap{position:relative;display:inline-block;}"
            ".pp-tip{visibility:hidden;opacity:0;transition:opacity .12s;"
            "position:absolute;bottom:calc(100% + 6px);left:0;z-index:9999;"
            "background:#0f111a;border:0.5px solid #2a2d3e;border-radius:8px;"
            "padding:9px 13px;font-size:11px;color:#e8eaf0;line-height:1.8;"
            "white-space:nowrap;pointer-events:none;"
            "font-family:JetBrains Mono,monospace;box-shadow:0 4px 16px #00000088;}"
            ".pp-wrap:hover .pp-tip{visibility:visible;opacity:1;}</style>"
        )
        id_section = (
            _pp_css + f"<div style='flex:1;padding:11px 16px;"
            + ("border-right:0.5px solid #1e2130;" if show_professional else "")
            + f"'>"
            f"<div style='color:#a78bfa;font-size:.68rem;text-transform:uppercase;"
            f"letter-spacing:1px;font-family:JetBrains Mono,monospace;"
            f"margin-bottom:7px;'>Papiers d'identité</div>{id_body}</div>"
        )

    # ── Construire pro HTML ───────────────────────────────────────────────────
    pro_section = ""
    if show_professional:
        prof = sg(col_profession, ""); emp = sg(col_employeur, "")
        sit  = sg(col_situation_pro, "")
        pro_rows = []
        if prof: pro_rows.append(("Profession", f"{prof}{tx_badge('profession', prof)}"))
        if emp:  pro_rows.append(("Employeur",  emp))
        if sit:  pro_rows.append(("Contrat",    f"{sit}{tx_badge('situation_pro', sit)}"))
        pro_body = "".join(
            f"<div style='display:flex;gap:8px;padding:5px 0;border-top:1px solid #1e2130;'><span style='color:#64748b;font-size:.72rem;min-width:85px;flex-shrink:0;'>{k}</span><span style='color:#e8eaf0;font-size:.78rem;'>{v}</span></div>"
            for k, v in pro_rows
        ) if pro_rows else "<span style='color:#334155;font-size:.75rem;font-style:italic;'>Non renseigné</span>"
        pro_section = (
            f"<div style='flex:1;padding:11px 16px;'><div style='color:#60a5fa;font-size:.68rem;"
            f"text-transform:uppercase;letter-spacing:1px;font-family:JetBrains Mono,monospace;"
            f"margin-bottom:7px;'>Situation professionnelle</div>{pro_body}</div>"
        )

    # ── Render tout en un seul st.markdown (pas de gap Streamlit) ────────────
    idpro_html = ""
    if show_identity or show_professional:
        idpro_html = (
            f"<div style='display:flex;border-top:0.5px solid #1e2130;'>{id_section}{pro_section}</div>"
        )
    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;"
        f"border-radius:12px 12px 0 0;border-bottom:none;'>"
        f"<div style='padding:14px 20px 10px;display:flex;align-items:center;gap:14px;'>"
        f"<div style='width:44px;height:44px;border-radius:50%;"
        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-weight:700;font-size:.95rem;color:white;flex-shrink:0;'>{ini}</div>"
        f"<div style='flex:1;'>"
        f"<div style='font-weight:700;font-size:.95rem;color:#e8eaf0;'>{prenom} {nom}</div>"
        f"<div style='color:#64748b;font-size:.78rem;margin-top:1px;'>"
        f"{(''+ville+' &nbsp;·&nbsp; ' if ville else '')}"
        f"<span style='color:{sc};'>{statut}</span></div></div>"
        f"<div style='text-align:right;color:#94a3b8;'>{contact_html}</div>"
        f"</div>"
        f"{idpro_html}"
        f"</div>",
        unsafe_allow_html=True)

    # ── Enrichissement async (appel API en arrière-plan) ──────────────────────
    _client_id = _safe_get(client_row, "id", None)
    if _client_id is not None and _client_id != "—":
        try:
            _cid_key = int(float(_client_id))  # clé hashable
        except (TypeError, ValueError):
            _cid_key = str(_client_id)
        # Snapshot léger : on transmet au worker juste ce dont il aurait besoin
        _snapshot = {
            "id":    _cid_key,
            "nom":   sg(col_nom, ""),
            "prenom":sg(col_prenom, ""),
            "email": sg(col_email, ""),
            "ville": sg(col_ville, ""),
        }
        render_client_enrichment_block(_cid_key, _snapshot)

    # ── Voyages ───────────────────────────────────────────────────────────────
    if voyages_df is None or (hasattr(voyages_df, "empty") and voyages_df.empty):
        st.markdown(
            "<div style='background:#13151d;border:1px solid #1e2130;"
            "border-top:none;border-radius:0 0 12px 12px;padding:12px 16px;"
            "color:#334155;font-size:.8rem;font-style:italic;'>"
            "Aucun voyage enregistré.</div>"
            "<div style='margin-bottom:14px'></div>",
            unsafe_allow_html=True)
        return

    n_v = len(voyages_df)

    # Identifiant du client courant (pour exclure de la liste compagnons)
    _own_id = _safe_get(client_row, "id", None)
    if _own_id in ("—", None):
        _own_id = _safe_get(client_row, "clients_id", None)

    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;"
        f"border-top:1px solid #2a2d3e;padding:7px 16px;'>"
        f"<span style='color:#94a3b8;font-size:.68rem;text-transform:uppercase;"
        f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>"
        f"{n_v} voyage{'s' if n_v > 1 else ''}</span></div>",
        unsafe_allow_html=True)

    vrows = list(voyages_df.iterrows())
    for vi, (_, vrow) in enumerate(vrows):
        vsg      = lambda col, d="—": _safe_get(vrow, col, d)
        is_last  = vi == len(vrows) - 1
        br       = "border-radius:0 0 12px 12px;" if is_last else ""
        dest     = vsg(col_v_destination);  pays   = vsg(col_v_pays, "")
        cont     = vsg(col_v_continent, "");tv      = vsg(col_v_type, "")
        date_dep = str(vsg(col_v_date_dep, ""))[:10]
        date_ret = str(vsg(col_v_date_ret, ""))[:10]
        duree    = vsg(col_v_duree, None);   hotel   = vsg(col_v_hotel, "")
        transport= vsg(col_v_transport, ""); note_v  = vsg(col_v_note, None)
        gid      = vsg(col_v_groupe, None)
        cc       = CONT_COLORS.get(cont, "#6b7280")
        tc       = TYPE_COLORS.get(tv,   "#6b7280")
        try:    stars = "⭐" * int(float(note_v)) if note_v and note_v != "—" else ""
        except: stars = ""

        # Compagnons de voyage
        companions = []
        if show_companions and gid and gid != "—" and all_voyages_df is not None:
            try:
                gid_int = int(float(gid))
                cdf = all_voyages_df[
                    all_voyages_df[col_v_groupe].apply(
                        lambda x: int(float(x)) == gid_int
                        if pd.notna(x) and x != "" else False
                    )
                ]
                if _own_id not in ("—", None):
                    cdf = cdf[cdf[col_c_client_id].astype(str)
                              != str(int(float(_own_id)))]
                seen = set()
                for _, cr in cdf.iterrows():
                    cid_ = str(_safe_get(cr, col_c_client_id, ""))
                    if cid_ not in seen:
                        seen.add(cid_)
                        companions.append((
                            _safe_get(cr, col_c_prenom,    ""),
                            _safe_get(cr, col_c_nom,       ""),
                            _safe_get(cr, col_c_profession,""),
                            _safe_get(cr, col_c_ville,     ""),
                            _safe_get(cr, col_c_statut,    ""),
                        ))
            except Exception:
                companions = []

        has_comp = bool(companions)
        last_border = f"border-bottom:1px solid #1e2130;{br}" if is_last else ""

        col_voy, col_comp = st.columns([9.5, 1.5])
        with col_voy:
            d_str = f"  ·  {int(float(duree))}j" \
                    if duree and duree != "—" else ""
            st.markdown(
                f"<div style='background:#13151d;"
                f"border-left:1px solid #1e2130;border-right:1px solid #1e2130;"
                f"{last_border}padding:8px 16px;'>"
                f"<div style='display:flex;align-items:center;gap:8px;"
                f"border-top:1px solid #1e2130;padding-top:6px;'>"
                f"<div style='width:3px;height:26px;border-radius:2px;"
                f"background:{cc};flex-shrink:0;'></div>"
                f"<div style='flex:1;'>"
                f"<span style='color:#e8eaf0;font-weight:600;font-size:.85rem;'>"
                f"{dest}{tx_badge('destinations', dest)}</span>"
                f"<span style='color:#475569;font-size:.73rem;margin-left:8px;'>"
                f"{pays}{tx_badge('destinations', pays)}{'  ·  ' if pays else ''}{date_dep}"
                f"{'  →  '+date_ret if date_ret and date_ret != date_dep else ''}"
                f"{d_str}</span></div>"
                f"<span style='background:{tc}22;color:{tc};font-size:.68rem;"
                f"padding:2px 7px;border-radius:10px;white-space:nowrap;'>{tv}</span>"
                f"{tx_badge('types_voyage', tv)}"
                f"{'<span style=\"font-size:.72rem;margin-left:4px;\">'+stars+'</span>' if stars else ''}"
                f"</div></div>",
                unsafe_allow_html=True)


        with col_comp:
            # Client courant toujours en premier — popover toujours actif
            _self = (
                _safe_get(client_row, col_prenom,     ""),
                _safe_get(client_row, col_nom,        ""),
                _safe_get(client_row, col_profession, ""),
                _safe_get(client_row, col_ville,      ""),
                _safe_get(client_row, col_statut,     ""),
            )
            all_members = [_self] + companions
            if len(all_members) <= 1:
                # Solo : bouton non cliquable
                st.markdown(
                    "<div style='display:flex;align-items:center;justify-content:center;"
                    "height:36px;border:1px solid #1e2130;border-radius:6px;"
                    "color:#334155;font-size:.83rem;cursor:not-allowed;user-select:none;'>"
                    f"👥 {len(all_members)}</div>",
                    unsafe_allow_html=True)
            else:
             with st.popover(f"👥 {len(all_members)}", use_container_width=True):
                st.markdown(
                    f"<div style='font-size:.7rem;text-transform:uppercase;"
                    f"letter-spacing:1px;font-family:JetBrains Mono,monospace;"
                    f"color:#94a3b8;margin-bottom:8px;'>"
                    f"{len(all_members)} participant"
                    f"{'s' if len(all_members)>1 else ''}</div>",
                    unsafe_allow_html=True)
                for mp, mn, mprof, mvil, mstat in all_members:
                    cp_ini = ((mp[:1] if mp else "")+(mn[:1] if mn else "")).upper() or "?"
                    sc2    = "#4ade80" if mstat == "actif" else "#f87171"
                    meta   = "  ·  ".join(filter(None, [mprof, mvil]))
                    st.markdown(
                        f"<div style='display:flex;align-items:flex-start;gap:10px;"
                        f"padding:8px 0;border-top:1px solid #1e2130;'>"
                        f"<div style='width:32px;height:32px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;font-size:.72rem;color:white;"
                        f"flex-shrink:0;margin-top:1px;'>{cp_ini}</div>"
                        f"<div style='flex:1;'>"
                        f"<div style='font-weight:600;font-size:.85rem;color:#e8eaf0;'>"
                        f"{mp} {mn}</div>"
                        f"{'<div style=\"font-size:.72rem;color:#64748b;margin-top:2px;\">' + meta + '</div>' if meta else ''}"
                        f"<div style='margin-top:3px;'>"
                        f"<span style='font-size:.68rem;padding:1px 7px;border-radius:20px;"
                        f"background:{sc2}22;color:{sc2};'>{mstat or '—'}</span>"
                        f"</div></div></div>",
                        unsafe_allow_html=True)

        if is_last:
            st.markdown(
                "<div style='background:#13151d;border:1px solid #1e2130;"
                "border-top:none;border-radius:0 0 12px 12px;height:6px;'></div>",
                unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:14px'></div>", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# FICHE VOYAGE — fonction exportable (vue centrée sur le voyage)
# ══════════════════════════════════════════════════════════════════════════════

def render_voyage_profile_card(
    voyage_row,
    all_voyages_df=None,
    # ── Colonnes voyage ──────────────────────────────────────────────────────
    col_destination="destination",  col_pays="pays_destination",
    col_continent="continent",      col_date_dep="date_depart",
    col_date_ret="date_retour",     col_duree="duree_jours",
    col_type="type_voyage",         col_transport="transport",
    col_hotel="hotel",
    col_statut="statut",            col_note="note",
    col_groupe="groupe_voyage_id",  col_client_id="client_id",
    # ── Colonnes client dans voyage_row (si JOIN) ─────────────────────────────
    col_nom="nom",                  col_prenom="prenom",
    col_ville="ville",              col_statut_client="statut",
    col_profession="profession",
    # ── Colonnes membres dans all_voyages_df ──────────────────────────────────
    col_m_client_id="client_id",   col_m_nom="nom",
    col_m_prenom="prenom",         col_m_profession="profession",
    col_m_ville="ville",           col_m_statut="statut",
    # ── Options ───────────────────────────────────────────────────────────────
    show_client_info=True,
):
    """
    Affiche une carte centrée sur un voyage, avec popover des participants.

    Symétrique à render_client_profile_card — même convention col_*,
    même _safe_get, même résilience aux colonnes manquantes.

    voyage_row      : pd.Series ou dict — une ligne de résultat
    all_voyages_df  : DataFrame avec groupe_voyage_id + infos clients,
                      utilisé pour afficher tous les participants du groupe.
                      Passer None pour désactiver.
    show_client_info: afficher la mini-carte du client principal en bas
    """
    vsg = lambda col, d="—": _safe_get(voyage_row, col, d)

    dest     = vsg(col_destination)
    pays     = vsg(col_pays,     "")
    cont     = vsg(col_continent,"")
    date_dep = str(vsg(col_date_dep, ""))[:10]
    date_ret = str(vsg(col_date_ret, ""))[:10]
    duree    = vsg(col_duree,    None)
    tv       = vsg(col_type,     "")
    transport= vsg(col_transport,"")
    hotel    = vsg(col_hotel,    "")
    statut   = vsg(col_statut,   "")
    note_v   = vsg(col_note,     None)
    gid      = vsg(col_groupe,   None)
    own_cid  = vsg(col_client_id,None)

    cc  = CONT_COLORS.get(cont, "#6b7280")
    tc  = TYPE_COLORS.get(tv,   "#6b7280")
    try:   stars = "⭐" * int(float(note_v)) if note_v and note_v != "—" else ""
    except: stars = ""
    sv_col = {"terminé":"#4ade80","à venir":"#fbbf24","annulé":"#f87171"}.get(statut,"#94a3b8")

    d_str  = f"{int(float(duree))}j" if duree and duree != "—" else ""
    dt_str = f"{date_dep} → {date_ret}" if date_ret and date_ret != date_dep else date_dep

    # ── Participants : client principal + compagnons ───────────────────────────
    nom_c    = vsg(col_nom,     "")
    prenom_c = vsg(col_prenom,  "")
    members  = []
    if nom_c or prenom_c:
        members.append((prenom_c, nom_c,
                         vsg(col_profession,""), vsg(col_ville,""),
                         vsg(col_statut_client,"")))

    if gid and gid != "—" and all_voyages_df is not None:
        try:
            gid_int = int(float(gid))
            cdf = all_voyages_df[
                all_voyages_df[col_groupe].apply(
                    lambda x: int(float(x)) == gid_int
                    if pd.notna(x) and x != "" else False)]
            if own_cid not in ("—", None):
                cdf = cdf[cdf[col_m_client_id].astype(str) != str(int(float(own_cid)))]
            seen = set()
            for _, cr in cdf.iterrows():
                cid_ = str(_safe_get(cr, col_m_client_id, ""))
                if cid_ not in seen:
                    seen.add(cid_)
                    members.append((
                        _safe_get(cr, col_m_prenom,    ""),
                        _safe_get(cr, col_m_nom,       ""),
                        _safe_get(cr, col_m_profession,""),
                        _safe_get(cr, col_m_ville,     ""),
                        _safe_get(cr, col_m_statut,    ""),
                    ))
        except Exception:
            pass

    n_mbr = len(members)

    # ── Hero : destination + méta + hôtel + transport ───────────────────────
    meta = "  ·  ".join(filter(None, [pays, cont, d_str, dt_str]))
    ht   = "  ·  ".join(filter(None, [
        f"🏨 {hotel}"     if hotel     and hotel     != "—" else "",
        f"✈️ {transport}" if transport and transport != "—" else "",
    ]))
    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;"
        f"border-bottom:none;border-radius:12px 12px 0 0;"
        f"border-left:4px solid {cc};padding:13px 20px 10px;'>"
        f"<div style='display:flex;align-items:flex-start;"
        f"justify-content:space-between;gap:8px;'>"
        f"<div>"
        f"<div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>{dest}</div>"
        f"<div style='color:#64748b;font-size:.77rem;margin-top:3px;'>{meta}</div>"
        f"{'<div style=\'color:#94a3b8;font-size:.75rem;margin-top:2px;\'>' + ht + '</div>' if ht else ''}"
        f"</div>"
        f"{'<div style=\'font-size:.8rem;flex-shrink:0;\'>' + stars + '</div>' if stars else ''}"
        f"</div></div>",
        unsafe_allow_html=True)

    # ── Tags + membres ────────────────────────────────────────────────────────
    col_tg, col_mb = st.columns([8, 2])

    with col_tg:
        t1 = (f"<span style='background:{tc}22;color:{tc};font-size:.7rem;"
              f"padding:2px 8px;border-radius:10px;margin-right:5px;'>{tv}</span>"
              if tv else "")
        t2 = (f"<span style='background:{sv_col}22;color:{sv_col};font-size:.7rem;"
              f"padding:2px 8px;border-radius:10px;'>{statut}</span>"
              if statut else "")
        st.markdown(
            f"<div style='background:#13151d;border-left:1px solid #1e2130;"
            f"border-right:1px solid #1e2130;border-top:1px solid #1e2130;"
            f"padding:7px 16px;min-height:36px;display:flex;align-items:center;'>"
            f"{t1}{t2}</div>",
            unsafe_allow_html=True)


    with col_mb:
        if members:
            with st.popover(f"👥 {n_mbr}", use_container_width=True):
                st.markdown(
                    f"<div style='font-size:.7rem;text-transform:uppercase;"
                    f"letter-spacing:1px;font-family:JetBrains Mono,monospace;"
                    f"color:#94a3b8;margin-bottom:8px;'>"
                    f"{n_mbr} participant{'s' if n_mbr > 1 else ''}</div>",
                    unsafe_allow_html=True)
                for mp, mn, mprof, mvil, mstat in members:
                    m_ini = ((mp[:1] if mp else "")+(mn[:1] if mn else "")).upper() or "?"
                    m_sc  = "#4ade80" if mstat=="actif" else ("#f87171" if mstat=="inactif" else "#94a3b8")
                    m_meta= "  ·  ".join(filter(None, [mprof, mvil]))
                    st.markdown(
                        f"<div style='display:flex;align-items:flex-start;gap:10px;"
                        f"padding:7px 0;border-top:1px solid #1e2130;'>"
                        f"<div style='width:30px;height:30px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;font-size:.7rem;color:white;"
                        f"flex-shrink:0;margin-top:1px;'>{m_ini}</div>"
                        f"<div style='flex:1;'>"
                        f"<div style='font-weight:600;font-size:.83rem;color:#e8eaf0;'>"
                        f"{mp} {mn}</div>"
                        f"{'<div style=\"font-size:.72rem;color:#64748b;margin-top:1px;\">' + m_meta + '</div>' if m_meta else ''}"
                        f"{'<div style=\"margin-top:2px;\"><span style=\"font-size:.68rem;padding:1px 7px;border-radius:20px;background:'+m_sc+'22;color:'+m_sc+';\">'+mstat+'</span></div>' if mstat and mstat != '—' else ''}"
                        f"</div></div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='display:flex;align-items:center;justify-content:center;"
                "height:36px;border:1px solid #1e2130;border-radius:6px;"
                "color:#334155;font-size:.83rem;cursor:not-allowed;user-select:none;'>"
                "👥 0</div>",
                unsafe_allow_html=True)

    # ── Client principal ──────────────────────────────────────────────────────
    if show_client_info and (nom_c or prenom_c):
        sc_c  = "#4ade80" if vsg(col_statut_client) == "actif" else "#f87171"
        ini_c = ((prenom_c[:1] if prenom_c else "")+(nom_c[:1] if nom_c else "")).upper() or "?"
        meta_c = "  ·  ".join(filter(None, [vsg(col_profession,""), vsg(col_ville,"")]))
        st.markdown(
            f"<div style='background:#13151d;border:1px solid #1e2130;"
            f"border-top:1px solid #2a2d3e;border-radius:0 0 12px 12px;"
            f"padding:8px 16px;display:flex;align-items:center;gap:10px;'>"
            f"<div style='width:28px;height:28px;border-radius:50%;"
            f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:.7rem;color:white;flex-shrink:0;'>{ini_c}</div>"
            f"<div style='flex:1;'>"
            f"<span style='font-weight:600;font-size:.84rem;color:#e8eaf0;'>"
            f"{prenom_c} {nom_c}</span>"
            f"{'<span style=\"font-size:.72rem;color:#64748b;margin-left:8px;\">' + meta_c + '</span>' if meta_c else ''}"
            f"</div>"
            f"<span style='font-size:.68rem;padding:2px 8px;border-radius:20px;"
            f"background:{sc_c}22;color:{sc_c};'>{vsg(col_statut_client,'')}</span>"
            f"</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#13151d;border:1px solid #1e2130;"
            "border-top:none;border-radius:0 0 12px 12px;height:5px;'></div>",
            unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DE LA CONFIGURATION EXTERNE (YAML ou TOML)
# ══════════════════════════════════════════════════════════════════════════════

# Chemin par défaut : config.yaml dans le même répertoire que ce fichier.
# Changez en "config.toml" pour utiliser le format TOML.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def _validate_config(data: dict) -> None:
    """Lève ValueError si le fichier de config est mal formé."""
    for key in ("schema", "enrich"):
        if key not in data:
            raise ValueError(f"Clé '{key}' manquante dans le fichier de config.")

    schema = data["schema"]
    for table, info in schema.items():
        if "columns" not in info:
            raise ValueError(f"schema.{table} : 'columns' manquant.")
        if "pk" not in info:
            raise ValueError(f"schema.{table} : 'pk' manquant.")
        if info["pk"] not in info["columns"]:
            raise ValueError(f"schema.{table} : pk '{info['pk']}' absent de columns.")
        for fk in info.get("fk") or []:
            for k in ("col", "ref", "ref_col"):
                if k not in fk:
                    raise ValueError(f"schema.{table}.fk : clé '{k}' manquante.")
            if fk["ref"] not in schema:
                raise ValueError(f"schema.{table}.fk : table '{fk['ref']}' inexistante.")


@st.cache_data
def _load_config_cached(path: str, mtime: float) -> dict:
    """Lit et valide le fichier de config (cache invalidé automatiquement si mtime change)."""
    with open(path, "rb") as fh:
        raw = fh.read()

    if path.endswith(".toml"):
        try:
            import tomllib                    # Python ≥ 3.11
        except ImportError:
            import tomli as tomllib           # pip install tomli  (Python < 3.11)
        data = tomllib.loads(raw.decode("utf-8"))
    else:
        import yaml                           # pip install pyyaml
        data = yaml.safe_load(raw)

    # Normalise les fk: None → []
    for info in data.get("schema", {}).values():
        if info.get("fk") is None:
            info["fk"] = []

    _validate_config(data)
    return data


def load_config(path: str = CONFIG_PATH) -> dict:
    """
    Charge la config depuis un fichier YAML ou TOML.
    Rechargement automatique dès que le fichier est modifié sur disque
    (détecté via mtime à chaque rerun Streamlit).
    """
    try:
        mtime = os.path.getmtime(path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Fichier de config introuvable : {path}\n"
            "Créez config.yaml (ou config.toml) dans le même répertoire que ce script."
        )
    return _load_config_cached(path, mtime)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS ENRICH  (enrich passé en paramètre pour éviter le global)
# ══════════════════════════════════════════════════════════════════════════════
def _find_col(df, *candidates: str):
    """
    Retourne le premier nom de colonne présent dans df parmi les candidats.
    Robuste aux alias générés lors des jointures (ex. 'id' → 'clients_id').
    Retourne None si aucun candidat n'existe.
    """
    for c in candidates:
        if c in df.columns:
            return c
    return None
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


# ══════════════════════════════════════════════════════════════════════════════
# RENDU DE L'ARBRE  (aucune référence aux constantes métier)
# ══════════════════════════════════════════════════════════════════════════════
BRANCH_STYLES = {
    "ET": {"color": "#fca5a5", "bg": "#450a0a", "border": "#991b1b"},
    "OU": {"color": "#93c5fd", "bg": "#172554", "border": "#1d4ed8"},
}
NEUTRAL = "#475569"

OP_NATURAL = {
    "Contient": "contient", "Commence par": "commence par", "Finit par": "finit par",
    "Égal à": "est", "Différent de": "n'est pas", "Supérieur à": ">", "Inférieur à": "<",
}


def _date_label(val):
    p = val.split("-")
    try:
        if len(p) == 1: return f"année {p[0]}"
        if len(p) == 2: return f"{MONTHS_FR[int(p[1])]} {p[0]}"
        return f"{int(p[2])} {MONTHS_FR[int(p[1])]} {p[0]}"
    except Exception:
        return val


def _leaf_html(conditions, idx):
    c           = conditions[idx]
    col_display = c.get("label", c["column"])   # label si dispo, sinon nom brut

    # ── Recherche par couples ────────────────────────────────────────────────
    if c.get("is_pair"):
        pairs = c.get("pairs", [])
        n     = len(pairs)
        col1, col2 = c["columns"]
        col_labels = c.get("col_labels") or [col1, col2]
        # Aperçu des 2 premiers couples
        shown = pairs[:2]
        preview_items = []
        for v1, v2 in shown:
            preview_items.append(f"«{v1}·{v2}»")
        preview = " · ".join(preview_items)
        suffix  = (f" <span style='color:#64748b;font-size:.75rem;'>+{n-2} autres</span>"
                   if n > 2 else "")
        return (f"<span class='t-leaf'>"
                f"<b style='color:#a5f3fc;'>{col_labels[0]} + {col_labels[1]}</b> "
                f"<span style='color:#fbbf24;'>parmi {n} couple{'s' if n > 1 else ''}</span> "
                f"<span style='color:#86efac;'>[{preview}{suffix}]</span>"
                f"</span>")

    if c.get("is_date"):
        if isinstance(c["value"], (tuple, list)) and len(c["value"]) == 2:
            date1, date2 = c["value"]
            return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{col_display}</b> " 
                    f"<span style='color:#fbbf24;'>entre le</span> "
                    f"<span style='color:#86efac;'>{_format_date_fr(date1)}</span> "
                    f"<span style='color:#fbbf24;'>et le</span> "
                    f"<span style='color:#86efac;'>{_format_date_fr(date2)}</span></span>")
        else:
            return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{col_display}</b> "
                    f"<span style='color:#fbbf24;'>en</span> " 
                    f"<span style='color:#86efac;'>{_date_label(c['value'])}</span></span>")
    if c.get("is_bulk"):
        values  = c["values"]
        n       = len(values)
        op_str  = OP_NATURAL.get(c["operator"], c["operator"])
        shown   = values[:3]
        preview = " · ".join(f"«{v}»" for v in shown)
        suffix  = f" <span style='color:#64748b;font-size:.75rem;'>+{n-3} autres</span>" if n > 3 else ""
        return (f"<span class='t-leaf'>"
                f"<b style='color:#a5f3fc;'>{col_display}</b> "
                f"<span style='color:#fbbf24;'>{op_str}</span> "
                f"<span style='color:#86efac;'>[{preview}{suffix}]</span>"
                f"</span>")
    op_str = OP_NATURAL.get(c["operator"], c["operator"])
    return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{col_display}</b> "
            f"<span style='color:#fbbf24;'>{op_str}</span> "
            f"<span style='color:#86efac;'>«\u202f{c['value']}\u202f»</span></span>")


def _prefix_html(prefix_parts, connector, connector_color):
    spans = "".join(
        f"<span style='font-family:JetBrains Mono,monospace;font-size:.82rem;"
        f"white-space:pre;color:{c};'>{t}</span>" for t, c in prefix_parts)
    if connector:
        spans += (f"<span style='font-family:JetBrains Mono,monospace;font-size:.82rem;"
                  f"white-space:pre;color:{connector_color};'>{connector}</span>")
    return spans


def _small_edit_button(idx):
    m = f"editbtn-{idx}"
    st.markdown(
        f'<div id="{m}"></div><style>'
        f"div.element-container:has(#{m}) + div.element-container button{{"
        f"background:transparent!important;color:#475569!important;"
        f"border:1px solid #2a2d3e!important;border-radius:4px!important;"
        f"font-size:.72rem!important;padding:1px 6px!important;"
        f"min-height:0!important;line-height:1.4!important;}}"
        f"div.element-container:has(#{m}) + div.element-container button:hover{{"
        f"color:#94a3b8!important;border-color:#475569!important;"
        f"background:#1a1d27!important;transform:none!important;box-shadow:none!important;}}"
        f"</style>", unsafe_allow_html=True)
    if st.button("✏️", key=f"editbtn_{idx}", help="Modifier / Supprimer"):
        st.session_state.editing[idx] = "leaf"
        st.rerun()


def _render_leaf_editor(conditions, idx):
    cond    = conditions[idx]
    is_date = cond.get("is_date", False)
    is_bulk = cond.get("is_bulk", False)
    is_pair = cond.get("is_pair", False)

    # ── Édition d'une condition couples (pair) ───────────────────────────────
    if is_pair:
        pairs        = cond.get("pairs", [])
        col_labels   = cond.get("col_labels") or cond["columns"]
        current_text = "\n".join(f"{v1}, {v2}" for v1, v2 in pairs)
        st.text_area(
            f"Couples ({col_labels[0]}, {col_labels[1]})",
            value=current_text, key=f"epair_{idx}",
            height=140, label_visibility="visible",
            placeholder="Un couple par ligne, séparé par une virgule\nExemple :\nDupont, 1985-03-15\nMartin, 1990-07-22",
        )
        e1, e2 = st.columns([1, 1])
        with e1:
            if st.button("✓ Valider", key=f"eok_{idx}", width="stretch"):
                raw   = st.session_state.get(f"epair_{idx}", "")
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                new_pairs = []
                for ln in lines:
                    # On accepte virgule ou tab comme séparateur
                    parts = [p.strip() for p in re.split(r"[,\t]", ln, maxsplit=1) if p.strip()]
                    if len(parts) == 2:
                        new_pairs.append((parts[0], parts[1]))
                if new_pairs:
                    st.session_state.conditions[idx]["pairs"] = new_pairs
                    st.session_state.editing.pop(idx, None)
                    st.rerun()
                else:
                    st.warning("Entrez au moins un couple valide « valeur1, valeur2 ».")
        with e2:
            if st.button("🗑 Supprimer", key=f"edel_{idx}", width="stretch"):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx, None)
                st.rerun()
        return

    if is_bulk:
        current_text = "\n".join(cond["values"])
        st.text_area("Valeurs", value=current_text, key=f"ev_{idx}",
                     height=110, label_visibility="collapsed",
                     placeholder="Une valeur par ligne, ou séparées par des virgules")
        e1, e2, e3 = st.columns([2, 1, 1])
        with e1:
            new_op_bulk = st.selectbox("Op", OP_LABELS,
                                       index=OP_LABELS.index(cond["operator"]),
                                       key=f"eop_{idx}", label_visibility="collapsed")
        with e2:
            if st.button("✓", key=f"eok_{idx}", help="Valider", width="stretch"):
                raw    = st.session_state.get(f"ev_{idx}", current_text)
                values = [v.strip() for v in re.split(r"[,\n]", raw) if v.strip()]
                if values:
                    st.session_state.conditions[idx]["values"]   = values
                    st.session_state.conditions[idx]["value"]    = ", ".join(values)
                    st.session_state.conditions[idx]["operator"] = st.session_state.get(f"eop_{idx}", cond["operator"])
                    st.session_state.editing.pop(idx, None)
                    st.rerun()
                else:
                    st.warning("Entrez au moins une valeur.")
        with e3:
            if st.button("🗑", key=f"edel_{idx}", help="Supprimer", width="stretch"):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx, None)
                st.rerun()

    elif is_date:
        # Détection du mode initial : tuple/list de 2 = plage de dates, sinon date unique
        _val_is_range = (
            isinstance(cond["value"], (tuple, list)) and len(cond["value"]) == 2
        )

        # Extraction de la date de référence (string YYYY-MM-DD)
        def _date_str(v):
            """Convertit une valeur en string YYYY-MM-DD si possible."""
            if v is None:
                return "2023-01-01"
            if hasattr(v, "strftime"):
                return v.strftime("%Y-%m-%d")
            return str(v)

        if _val_is_range:
            _ref_start = _date_str(cond["value"][0])
            _ref_end   = _date_str(cond["value"][1])
        else:
            _ref_start = _date_str(cond["value"])
            _ref_end   = _ref_start

        em, ec1, ec2, ec3, ec4, ec5 = st.columns([1.6, 1.4, 1.0, 1.0, 0.45, 0.45])

        with em:
            _initial_idx = 1 if _val_is_range else 0
            date_mode = st.selectbox(
                "Mode", ["📅 Date unique", "📆 Plage de dates"],
                index=_initial_idx,
                key=f"date_mode_{idx}",
                label_visibility="collapsed",
            )
        is_range = date_mode == "📆 Plage de dates"

        # ── Mode plage de dates ─────────────────────────────────────────────
        if is_range:
            try:
                _ds = datetime.strptime(_ref_start, "%Y-%m-%d").date()
            except Exception:
                _ds = datetime(2023, 1, 1).date()
            try:
                _de = datetime.strptime(_ref_end, "%Y-%m-%d").date()
            except Exception:
                _de = _ds

            with ec1:
                st.date_input("Début", value=_ds, key=f"estart_{idx}",
                              label_visibility="collapsed")
            with ec2:
                st.date_input("Fin", value=_de, key=f"eend_{idx}",
                              label_visibility="collapsed")
            # ec3 vide pour conserver l'alignement
        # ── Mode date unique ────────────────────────────────────────────────
        else:
            parts = _ref_start.split("-")
            cur_year  = int(parts[0]) if len(parts) >= 1 and parts[0].isdigit() else 2023
            cur_month = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
            cur_day   = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 0
            ec1.number_input("Année", 1900, 2100, cur_year, key=f"ey_{idx}",
                             label_visibility="collapsed")
            ec2.number_input("Mois", 0, 12, cur_month, key=f"em_{idx}",
                             label_visibility="collapsed")
            ec3.number_input("Jour", 0, 31, cur_day, key=f"ed_{idx}",
                             label_visibility="collapsed")

        with ec4:
            if st.button("✓", key=f"eok_{idx}", help="Valider"):
                if is_range:
                    _s = st.session_state.get(f"estart_{idx}")
                    _e = st.session_state.get(f"eend_{idx}")
                    if _s and _e and _s > _e:
                        st.warning("Date de début > date de fin.")
                    else:
                        st.session_state.conditions[idx]["value"] = (
                            _s.strftime("%Y-%m-%d") if _s else "",
                            _e.strftime("%Y-%m-%d") if _e else "",
                        )
                        st.session_state.conditions[idx]["is_range"] = True
                        st.session_state.conditions[idx].pop("values", None)
                        st.session_state.editing.pop(idx, None)
                        st.rerun()
                else:
                    st.session_state.conditions[idx]["value"] = build_date_value(
                        int(st.session_state.get(f"ey_{idx}", 2023)),
                        int(st.session_state.get(f"em_{idx}", 0)),
                        int(st.session_state.get(f"ed_{idx}", 0)),
                    )
                    st.session_state.conditions[idx]["is_range"] = False
                    st.session_state.editing.pop(idx, None)
                    st.rerun()
        with ec5:
            if st.button("🗑", key=f"edel_{idx}", help="Supprimer"):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx, None)
                st.rerun()

    else:
        e1, e2, e3, e4, e5 = st.columns([2.2, 1.8, 0.45, 0.45, 0.45])
        e1.text_input("Valeur", value=cond["value"],
                      key=f"ev_{idx}", label_visibility="collapsed")
        e2.selectbox("Op", OP_LABELS, index=OP_LABELS.index(cond["operator"]),
                     key=f"eop_{idx}", label_visibility="collapsed")
        with e3:
            if st.button("✓", key=f"eok_{idx}", help="Valider"):
                st.session_state.conditions[idx]["value"]    = st.session_state.get(f"ev_{idx}",  cond["value"])
                st.session_state.conditions[idx]["operator"] = st.session_state.get(f"eop_{idx}", cond["operator"])
                st.session_state.editing.pop(idx, None)
                st.rerun()
        with e4:
            if st.button("🗑", key=f"edel_{idx}", help="Supprimer"):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx, None)
                st.rerun()
        with e5:
            if st.button("✗", key=f"ecancel_{idx}", help="Annuler"):
                st.session_state.editing.pop(idx, None)
                st.rerun()


def _render_node(node, conditions, prefix_parts=None, is_last=True, is_root=False, parent_op=None):
    if prefix_parts is None: prefix_parts = []
    connector       = "" if is_root else ("└── " if is_last else "├── ")
    connector_color = BRANCH_STYLES[parent_op]["color"] if parent_op else NEUTRAL
    prefix_len      = sum(len(t) for t, _ in prefix_parts) + len(connector)
    ph              = _prefix_html(prefix_parts, connector, connector_color)

    # ── Nœud fantôme : aperçu cliquable de la condition en attente ───────────
    if node["type"] == "ghost":
        pending = node["pending"]
        target  = node["target"]
        oc      = BRANCH_STYLES[pending["join_op"]]["border"]
        m       = f"ghost-{target}"
        css = (
            f'<div id="{m}"></div><style>'
            f"div.element-container:has(#{m})+div.element-container button{{"
            f"background:transparent!important;color:#cbd5e1!important;"
            f"border:1px dashed {oc}!important;border-radius:5px!important;"
            f"font-family:'JetBrains Mono',monospace!important;font-size:.78rem!important;"
            f"opacity:.55!important;padding:3px 10px!important;min-height:0!important;"
            f"text-align:left!important;justify-content:flex-start!important;}}"
            f"div.element-container:has(#{m})+div.element-container button:hover{{"
            f"opacity:1!important;background:{oc}1a!important;"
            f"box-shadow:0 0 10px {oc}66!important;}}"
            f"div.element-container:has(#{m})+div.element-container button p{{"
            f"text-align:left!important;}}</style>"
        )
        tip = ("Relier à la dernière feuille" if target == "leaf"
               else "Créer une nouvelle branche au sommet")
        # Label lisible selon le type de la condition en attente
        _coldisp = pending.get("label", pending["column"])
        if pending.get("is_pair"):
            _n = len(pending.get("pairs", []))
            cond_txt = f"{_coldisp} parmi {_n} couple{'s' if _n > 1 else ''}"
        elif pending.get("is_date"):
            if isinstance(pending["value"], (tuple, list)) and len(pending["value"]) == 2:
                d1, d2 = pending["value"]
                cond_txt = f"{_coldisp} entre le {_format_date_fr(d1)} et le {_format_date_fr(d2)}"
            else:
                cond_txt = f"{_coldisp} en {_date_label(pending['value'])}"
        elif pending.get("is_bulk"):
            _ops = OP_NATURAL.get(pending["operator"], pending["operator"])
            _vals = pending.get("values", [])
            _prev = " · ".join(f"«{v}»" for v in _vals[:3])
            _suf  = f" +{len(_vals)-3}" if len(_vals) > 3 else ""
            cond_txt = f"{_coldisp} {_ops} [{_prev}{_suf}]"
        else:
            _ops = OP_NATURAL.get(pending["operator"], pending["operator"])
            cond_txt = f"{_coldisp} {_ops} « {pending.get('value','')} »"
        btn_label = f"＋ {cond_txt}"
        def _do_click():
            st.session_state.conditions.append(dict(pending, or_target=target))
            st.session_state.pop("_pending_cond", None)
            st.rerun()
        if ph:
            w = max(prefix_len * 0.135, 0.35)
            ca, cb = st.columns([w, max(9 - w, 1)])
            ca.markdown(f"<div style='padding-top:7px;line-height:1;'>{ph}</div>",
                        unsafe_allow_html=True)
            with cb:
                st.markdown(css, unsafe_allow_html=True)
                if st.button(btn_label, key=f"_ghostbtn_{target}",
                             help=tip, use_container_width=True):
                    _do_click()
        else:
            st.markdown(css, unsafe_allow_html=True)
            if st.button(btn_label, key=f"_ghostbtn_{target}",
                         help=tip, use_container_width=True):
                _do_click()
        return

    if node["type"] == "leaf":
        idx        = node["idx"]
        is_editing = st.session_state.editing.get(idx) == "leaf"
        if is_editing:
            if ph:
                w = max(prefix_len * 0.135, 0.35)
                ca, cb = st.columns([w, max(9 - w, 1)])
                ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>",
                            unsafe_allow_html=True)
                with cb:
                    _render_leaf_editor(conditions, idx)
            else:
                _render_leaf_editor(conditions, idx)
        else:
            leaf_h = _leaf_html(conditions, idx)
            if ph:
                w = max(prefix_len * 0.135, 0.35)
                ca, cb, cc = st.columns([w, max(8.4 - w, 1), 0.6])
                ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>",
                            unsafe_allow_html=True)
                cb.markdown(f"<div style='padding-top:6px;'>{leaf_h}</div>",
                            unsafe_allow_html=True)
                with cc:
                    _small_edit_button(idx)
            else:
                c1, c2 = st.columns([9.4, 0.6])
                c1.markdown(f"<div style='padding-top:2px;'>{leaf_h}</div>",
                            unsafe_allow_html=True)
                with c2:
                    _small_edit_button(idx)
    elif node["type"] == "or_group":
        # Groupe OR local : convertir en arbre binaire pour le rendu
        children = node["children"]
        sub = children[0]
        for child in children[1:]:
            sub = {"type": "branch", "op": "OU", "left": sub, "right": child}
        _render_node(sub, conditions, prefix_parts, is_last=is_last,
                     is_root=is_root, parent_op=parent_op)
    else:
        op = node["op"]
        if node.get("ghost"):
            # Branche fantôme : opérateur en label estompé (pas de bouton toggle)
            oc = BRANCH_STYLES[op]["border"]
            op_html = (f"<span style='font-family:JetBrains Mono,monospace;"
                       f"font-size:.78rem;color:{oc};opacity:.55;"
                       f"border:1px dashed {oc};border-radius:4px;"
                       f"padding:1px 9px;'>{op}</span>")
            if ph:
                st.markdown(f"<div style='padding-top:5px;'>{ph}{op_html}</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding-top:2px;'>{op_html}</div>",
                            unsafe_allow_html=True)
        else:
            # node["right"] peut être feuille, or_group, ou sous-arbre AND
            right_idx = _first_leaf_idx(node["right"])
            if ph:
                w = max(prefix_len * 0.135, 0.35)
                ca, cb = st.columns([w, max(9 - w, 1)])
                ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>", unsafe_allow_html=True)
                with cb: _branch_button(op, right_idx)
            else:
                _branch_button(op, right_idx)
        new_pfx = (prefix_parts if is_root else
                   prefix_parts + [("│   ", connector_color)] if not is_last else
                   prefix_parts + [("    ", connector_color)])
        _render_node(node["left"],  conditions, new_pfx, is_last=False, parent_op=op)
        _render_node(node["right"], conditions, new_pfx, is_last=True,  parent_op=op)


def _first_leaf_idx(node):
    """Retourne l'idx de la première feuille d'un sous-arbre (quel que soit son type)."""
    if node["type"] == "leaf":
        return node["idx"]
    if node["type"] == "or_group":
        return node["children"][0]["idx"]
    # branch
    return _first_leaf_idx(node["left"])


def _branch_button(op, right_idx):
    s = BRANCH_STYLES[op]
    bg, color, border = s["bg"], s["color"], s["border"]
    m = f"tbtn-{right_idx}"
    st.markdown(
        f'<div id="{m}"></div><style>'
        f"div.element-container:has(#{m}) + div.element-container button{{"
        f"background:{bg}!important;color:{color}!important;"
        f"border:1.5px solid {border}!important;font-family:'JetBrains Mono',monospace!important;"
        f"font-size:.82rem!important;font-weight:700!important;padding:3px 16px!important;"
        f"border-radius:5px!important;box-shadow:0 0 8px {border}55!important;min-height:0!important;}}"
        f"div.element-container:has(#{m}) + div.element-container button:hover{{"
        f"filter:brightness(1.3)!important;transform:translateY(-1px)!important;}}"
        f"</style>", unsafe_allow_html=True)
    if st.button(op, key=f"treeop_{right_idx}", help="Cliquer pour basculer ET / OU"):
        st.session_state.conditions[right_idx]["join_op"] = "OU" if op == "ET" else "ET"
        st.rerun()


def render_tree(conditions, table):
    st.markdown(
        f"<div class='tree-wrap'>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>Requête</span>"
        f"<div style='margin:6px 0 12px;'><span class='t-root'>SELECT * FROM {table}</span></div>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>WHERE</span></div>",
        unsafe_allow_html=True)
    _pending = st.session_state.get("_pending_cond")
    if _pending and conditions:
        tree = build_preview_tree(conditions, _pending)
    else:
        tree = build_tree(conditions)
    if tree is None:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>Aucune condition.</p>",
                    unsafe_allow_html=True)
        return
    _render_node(tree, conditions, prefix_parts=[], is_last=True, is_root=True, parent_op=None)

    # En mode placement : rappel + bouton annuler discret
    if _pending:
        st.markdown(
            "<div style='margin-top:8px;color:#64748b;font-size:.72rem;"
            "font-family:JetBrains Mono,monospace;'>"
            "↑ Cliquez un emplacement fantôme (pointillés) pour valider</div>",
            unsafe_allow_html=True)
        _mc = "gh-cancel"
        st.markdown(
            f'<div id="{_mc}"></div><style>'
            f"div.element-container:has(#{_mc})+div.element-container button{{"
            f"background:transparent!important;color:#475569!important;border:none!important;"
            f"font-size:.72rem!important;min-height:0!important;padding:2px!important;}}"
            f"div.element-container:has(#{_mc})+div.element-container button:hover{{"
            f"color:#94a3b8!important;}}</style>",
            unsafe_allow_html=True)
        if st.button("✕ annuler", key="_place_cancel"):
            st.session_state.pop("_pending_cond", None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# DIALOG  (lit tables/enrich via session_state pour rester compatible @st.dialog)
# ══════════════════════════════════════════════════════════════════════════════
@st.dialog("🔎 Explorer cette valeur")
def cell_filter_dialog(col_name, cell_value):
    # Récupération de la config injectée par run_app
    tables = st.session_state._app_tables
    enrich = st.session_state._app_enrich

    str_value = str(cell_value)
    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;"
        f"padding:12px 16px;margin-bottom:16px;'>"
        f"<span style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
        f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Cellule sélectionnée</span><br>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:.92rem;'>"
        f"<b style='color:#a5f3fc;'>{col_name}</b>"
        f" <span style='color:#fbbf24;'>=</span>"
        f" <span style='color:#86efac;'>«{str_value}»</span></span></div>",
        unsafe_allow_html=True)

    tables_with_col = [t for t, cols in tables.items() if col_name in cols]
    target_table = st.selectbox("Table cible", tables_with_col,
        index=tables_with_col.index(st.session_state.selected_table)
              if st.session_state.selected_table in tables_with_col else 0,
        key="dlg_table")
    op = st.selectbox("Opérateur", OP_LABELS, key="dlg_op")
    sym, fn = OPERATORS[op]
    tv = fn(str_value)
    st.markdown(
        f"<div style='background:#0a0c12;border:1px solid #1e2130;border-left:3px solid #6366f1;"
        f"border-radius:8px;padding:8px 14px;font-family:JetBrains Mono,monospace;"
        f"font-size:.8rem;color:#a5f3fc;margin:8px 0 14px;'>"
        f"SELECT * FROM <b>{target_table}</b> WHERE <b>{col_name}</b>"
        f" <span style='color:#fbbf24'>{sym}</span>"
        f" <span style='color:#86efac'>'{tv}'</span></div>",
        unsafe_allow_html=True)

    if st.button("▶ Lancer la requête", width="stretch", type="primary", key="dlg_run"):
        q = f"SELECT * FROM {target_table} WHERE {col_name} {sym} ?"
        try:
            st.session_state.results        = _get_db().read_sql(q, [tv])
            st.session_state.selected_table = target_table
            st.session_state.conditions     = [{"column": col_name, "operator": op,
                                                 "value": str_value, "join_op": "ET"}]
            where, params = build_where(st.session_state.conditions)
            st.session_state.last_where     = where
            st.session_state.last_params    = params
            st.session_state.enrich_count   = compute_enrich_count(target_table, where, params, enrich)
            st.session_state["_last_cell_click"] = None
        except Exception as e:
            st.error(f"Erreur SQL : {e}")
            return
        st.rerun()

    ck = f"cnt_{target_table}__{col_name}__{op}__{str_value}"
    if ck in st.session_state:
        cnt = st.session_state[ck]
        st.markdown(
            f"<div style='background:#14532d;border:2px solid #16a34a;border-radius:8px;"
            f"padding:12px;text-align:center;'>"
            f"<span style='color:#86efac;font-size:.72rem;text-transform:uppercase;"
            f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Résultats estimés</span><br>"
            f"<span style='color:#4ade80;font-size:2.2rem;font-weight:800;"
            f"font-family:JetBrains Mono,monospace;'>{cnt}</span>"
            f"<span style='color:#86efac;font-size:.85rem;'> ligne(s)</span></div>",
            unsafe_allow_html=True)
    else:
        if st.button("🔢 Estimer le nombre de résultats (COUNT)", width="stretch", key="dlg_count"):
            q2 = f"SELECT COUNT(*) AS total FROM {target_table} WHERE {col_name} {sym} ?"
            try:
                r2 = _get_db().read_sql(q2, [tv])
                st.session_state[ck] = int(r2["total"].iloc[0])
            except Exception as e:
                st.error(f"Erreur SQL : {e}")
            st.rerun()

    st.divider()
    st.markdown("<span style='color:#94a3b8;font-size:.8rem;'>Ou ajouter comme condition dans l'arbre :</span>",
                unsafe_allow_html=True)
    join = st.radio("Lier avec", ["ET", "OU"], horizontal=True, key="dlg_join") \
        if st.session_state.conditions else "ET"
    if st.button("➕ Ajouter à l'arbre", width="stretch", key="dlg_add"):
        st.session_state.conditions.append({"column": col_name, "operator": op,
                                             "value": str_value, "join_op": join})
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HISTORIQUE
# ══════════════════════════════════════════════════════════════════════════════
MAX_HISTORY = 20


# ══════════════════════════════════════════════════════════════════════════════
# HISTORIQUE  —  persisté dans la table SQL _app_history
# ══════════════════════════════════════════════════════════════════════════════
def _init_history_table(conn) -> None:
    """Crée la table _app_history si elle n'existe pas encore."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _app_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT    NOT NULL,
            ts         TEXT    NOT NULL,
            table_name TEXT    NOT NULL,
            summary    TEXT    NOT NULL,
            conds_json TEXT    NOT NULL,
            joins_json TEXT    NOT NULL DEFAULT '[]',
            row_count  INTEGER NOT NULL
        )
    """)
    try:
        conn.execute("ALTER TABLE _app_history ADD COLUMN joins_json TEXT NOT NULL DEFAULT '[]'")
    except Exception:
        pass
    conn.commit()


def _db_push_history(conn, user_id: str, table: str,
                     conditions: list, row_count: int,
                     joins: list | None = None) -> None:
    """Insère ou met à jour la dernière entrée d'historique pour ce user."""
    qd = build_query_display(table, conditions)
    summary = qd.split("\nWHERE ", 1)[1] if "\nWHERE " in qd else "Tous les enregistrements"
    ts = datetime.now().strftime("%d/%m %H:%M:%S")

    # Dédoublonnage : même table + même WHERE → mise à jour
    last = conn.execute(
        "SELECT id, summary, table_name FROM _app_history "
        "WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (user_id,)
    ).fetchone()

    if last and last[2] == table and last[1] == summary:
        conn.execute(
            "UPDATE _app_history SET ts=?, row_count=? WHERE id=?",
            (ts, row_count, last[0])
        )
    else:
        conn.execute(
            "INSERT INTO _app_history "
            "(user_id, ts, table_name, summary, conds_json, joins_json, row_count) "
            "VALUES (?,?,?,?,?,?,?)",
            (user_id, ts, table, summary,
             json.dumps(conditions, ensure_ascii=False),
             json.dumps(joins or [],  ensure_ascii=False),
             row_count)
        )

    # Borne à MAX_HISTORY entrées par user
    conn.execute("""
        DELETE FROM _app_history
        WHERE user_id = ? AND id NOT IN (
            SELECT id FROM _app_history
            WHERE user_id = ? ORDER BY id DESC LIMIT ?
        )
    """, (user_id, user_id, MAX_HISTORY))
    conn.commit()


def _db_get_history(conn, user_id: str) -> list[dict]:
    """Retourne les entrées d'historique du user, plus récentes en premier."""
    rows = conn.execute(
        "SELECT id, ts, table_name, summary, conds_json, joins_json, row_count "
        "FROM _app_history WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    result = []
    for r in rows:
        try:
            joins_val = json.loads(r[6]) if r[6] else []
        except Exception:
            joins_val = []
        result.append({
            "id":         r[0],
            "ts":         r[1],
            "table":      r[2],
            "summary":    r[3],
            "conditions": json.loads(r[4]),
            "joins":      joins_val,
            "row_count":  r[5],
        })
    return result


def _render_history_popover(conn, user_id: str, enrich: dict) -> None:
    """Bouton popover top-right avec la liste des requêtes passées."""
    history = _db_get_history(conn, user_id)
    n       = len(history)
    label   = f"🕐  {n}" if n else "🕐"

    with st.popover(label, use_container_width=True):
        st.markdown(
            "<span style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
            "letter-spacing:1px;font-family:JetBrains Mono,monospace;'>"
            f"Historique ({n} / {MAX_HISTORY})  —  user {user_id}</span>",
            unsafe_allow_html=True)

        if not history:
            st.markdown(
                "<p style='color:#4a5170;font-style:italic;font-size:.82rem;"
                "margin-top:6px;'>Aucune requête exécutée.</p>",
                unsafe_allow_html=True)
            return

        for entry in history:
            n_rows  = entry["row_count"]
            summ_d  = (entry["summary"][:160] + "…") \
                      if len(entry["summary"]) > 160 else entry["summary"]

            st.markdown(
                f"<div style='background:#13151d;border:1px solid #1e2130;"
                f"border-radius:10px;padding:10px 12px;margin-bottom:8px;'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;margin-bottom:5px;'>"
                f"<span style='font-family:JetBrains Mono,monospace;"
                f"font-size:.72rem;color:#6366f1;font-weight:600;'>"
                f"{entry['table']}</span>"
                f"<span style='font-size:.7rem;color:#475569;'>{entry['ts']}</span>"
                f"</div>"
                f"<div style='font-family:JetBrains Mono,monospace;font-size:.72rem;"
                f"color:#a5f3fc;white-space:pre-wrap;word-break:break-word;"
                f"line-height:1.55;margin-bottom:7px;'>{summ_d}</div>"
                f"<span style='font-size:.7rem;color:#4ade80;'>"
                f"{n_rows} ligne{'s' if n_rows != 1 else ''}</span>"
                f"</div>",
                unsafe_allow_html=True)

            if st.button("↩ Relancer", key=f"hist_replay_{entry['id']}",
                         use_container_width=True):
                st.session_state.selected_table      = entry["table"]
                st.session_state.conditions          = copy.deepcopy(entry["conditions"])
                st.session_state.joins               = copy.deepcopy(entry.get("joins", []))
                st.session_state.results             = None
                st.session_state.enrich_count        = None
                st.session_state["_last_cell_click"] = None
                st.session_state["_auto_execute"]    = True
                st.rerun()

        st.divider()
        if st.button("🗑 Vider mon historique", key="hist_clear",
                     use_container_width=True):
            conn.execute("DELETE FROM _app_history WHERE user_id=?", (user_id,))
            conn.commit()
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RÉSUMÉ D'UNE SOURCE DE DONNÉES (carte d'info table + dates min/max)
# ══════════════════════════════════════════════════════════════════════════════
def _format_date_fr(date_str: str) -> str:
    """Convertit '2023-04-10' en '10/04/2023'. Renvoie la chaîne d'origine en cas d'échec."""
    if not date_str:
        return "—"
    try:
        parts = str(date_str).split(" ")[0].split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        pass
    return str(date_str)


def render_table_summary(table_name: str, columns: list, labels_map: dict) -> None:
    """
    Affiche une carte stylisée résumant la source de données sélectionnée :
    • nombre total d'enregistrements
    • dates min/max pour chaque colonne de type date
    """
    date_cols = tuple(c for c in columns if is_date_col(c))
    summary   = get_table_summary(table_name, date_cols)

    row_count = summary["row_count"]
    date_info = summary["date_info"]
    # Formatage français : espace comme séparateur de milliers
    row_count_fmt = f"{row_count:,}".replace(",", " ")

    # ── Bloc principal : carte sombre avec accent violet ─────────────────────
    header_html = (
        "<div style='background:linear-gradient(135deg,#13151d 0%,#161826 100%);"
        "border:1px solid #2a2d3e;border-left:3px solid #a78bfa;"
        "border-radius:10px;padding:14px 18px;margin:8px 0 14px 0;'>"

        # En-tête : nom de table + badge nombre de lignes
        "<div style='display:flex;align-items:center;justify-content:space-between;"
        "flex-wrap:wrap;gap:10px;margin-bottom:10px;'>"
        "<div>"
        "<span style='color:#94a3b8;font-size:.68rem;text-transform:uppercase;"
        "letter-spacing:1.2px;font-family:JetBrains Mono,monospace;'>"
        "📊 Source de données</span><br>"
        f"<span style='color:#e8eaf0;font-size:1.05rem;font-weight:700;"
        f"font-family:Syne,sans-serif;'>{table_name}</span>"
        "</div>"
        "<div style='background:#1e293b;border:1px solid #334155;border-radius:20px;"
        "padding:4px 14px;'>"
        "<span style='color:#94a3b8;font-size:.7rem;font-family:JetBrains Mono,monospace;'>"
        "enregistrements</span> "
        f"<span style='color:#86efac;font-weight:700;font-family:JetBrains Mono,monospace;'>"
        f"{row_count_fmt}</span>"
        "</div></div>"
    )

    # ── Lignes : une par colonne de type date ────────────────────────────────
    if date_info:
        rows_html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
        for col, info in date_info.items():
            label = labels_map.get(col, col)
            vmin  = _format_date_fr(info.get("min"))
            vmax  = _format_date_fr(info.get("max"))
            rows_html += (
                "<div style='display:flex;align-items:center;gap:10px;"
                "background:#0f111a;border:1px solid #1e2130;border-radius:6px;"
                "padding:6px 12px;font-family:JetBrains Mono,monospace;font-size:.78rem;'>"
                f"<span style='color:#a5f3fc;min-width:140px;'>📅 {label}</span>"
                f"<span style='color:#64748b;'>du</span>"
                f"<span style='color:#86efac;font-weight:600;'>{vmin}</span>"
                f"<span style='color:#64748b;'>au</span>"
                f"<span style='color:#86efac;font-weight:600;'>{vmax}</span>"
                "</div>"
            )
        rows_html += "</div>"
    else:
        rows_html = (
            "<div style='color:#475569;font-size:.78rem;font-style:italic;"
            "font-family:JetBrains Mono,monospace;'>"
            "Aucune colonne de type date.</div>"
        )

    st.markdown(header_html + rows_html + "</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE UNIQUE
# ══════════════════════════════════════════════════════════════════════════════
def run_app(schema: dict, enrich: dict):
    """
    Lance l'application SQL Query Builder.

    Paramètres
    ----------
    schema : dict
        { nom_table: { "columns": [...], "pk": str, "fk": [...] } }
        fk  =  [ { "col": str, "ref": nom_table, "ref_col": str } ]

    enrich : dict
        Dictionnaire de jointure enrichissement (inchangé).
    """
    tables = {t: d["columns"] for t, d in schema.items()}
    # ── Injection de la config pour le dialog ─────────────────────────────────
    st.session_state._app_tables = tables
    st.session_state._app_enrich = enrich

    # ── Initialisation de l'état ──────────────────────────────────────────────
    default_table = next(iter(tables))
    for k, v in [("conditions", []), ("selected_table", default_table),
                 ("results", None), ("enrich_count", None),
                 ("last_where", ""), ("last_params", []), ("editing", {}),
                 ("joins", []), ("fiches_visible", 100)]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ── User ID + table SQL historique ────────────────────────────────────────
    conn    = get_connection()
    user_id = st.session_state.setdefault("user_id", str(uuid.uuid4())[:8])
    _init_history_table(conn)

    # ── Auto-exécution : relance depuis le popover historique ─────────────────
    if st.session_state.pop("_auto_execute", False):
        _q, _p = build_query(st.session_state.selected_table, st.session_state.conditions,
                             st.session_state.joins, schema)
        try:
            _res = _get_db().read_sql(_q, _p)
            st.session_state.results = _res
            _w, _wp = build_where(st.session_state.conditions)
            st.session_state.last_where   = _w
            st.session_state.last_params  = _wp
            st.session_state.enrich_count = compute_enrich_count(
                st.session_state.selected_table, _w, _wp, enrich)
            _db_push_history(conn, user_id, st.session_state.selected_table,
                             st.session_state.conditions, len(_res),
                             joins=st.session_state.joins)
        except Exception as _e:
            st.error(f"Erreur SQL (relance) : {_e}")

    # ── En-tête + popover historique (top-right) ──────────────────────────────
    col_hdr, col_cfg, col_pop = st.columns([5, 2, 1], vertical_alignment="bottom")
    with col_hdr:
        st.markdown("# 🔍 SQL Query Builder")
        st.markdown("<p style='color:#6b7280;margin-top:-14px;margin-bottom:20px;'>"
                    "Construisez vos requêtes SQL visuellement, sans écrire une ligne de code.</p>",
                    unsafe_allow_html=True)
    with col_cfg:
        cfg_name = os.path.basename(CONFIG_PATH)
        st.markdown(
            f"<div style='text-align:right;padding-bottom:2px;'>"
            f"<span style='font-size:.68rem;color:#475569;"
            f"font-family:JetBrains Mono,monospace;'>⚙ {cfg_name}</span></div>",
            unsafe_allow_html=True)
        if st.button("↺", key="cfg_reload", help=f"Recharger {CONFIG_PATH}",
                     use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_pop:
        _render_history_popover(conn, user_id, enrich)

    # ── Navigation principale ──────────────────────────────────────────────────
    app_mode = st.session_state.get("app_mode", "query")
    _nav_pills = {"query": "🔍  Requêtes", "map": "🗺️  Carte", "personnel": "👥  Personnel"}
    nav_cols = st.columns(len(_nav_pills) + 5)
    for i, (mode_key, mode_label) in enumerate(_nav_pills.items()):
        is_active = (app_mode == mode_key)
        m_id = f"navpill-{mode_key}"
        nav_cols[i].markdown(
            f'<div id="{m_id}"></div><style>'
            f"div.element-container:has(#{m_id}) + div.element-container button{{"
            f"background:{'linear-gradient(135deg,#3b82f6,#7c3aed)' if is_active else '#1a1d27'}!important;"
            f"color:{'#ffffff' if is_active else '#94a3b8'}!important;"
            f"border:{'none' if is_active else '1px solid #2a2d3e'}!important;"
            f"border-radius:20px!important;font-size:.85rem!important;}}</style>",
            unsafe_allow_html=True)
        if nav_cols[i].button(mode_label, key=f"nav_{mode_key}", use_container_width=True):
            st.session_state["app_mode"] = mode_key
            st.rerun()
    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    # ── Dispatch selon le mode ─────────────────────────────────────────────────
    if app_mode == "map":
        render_map_module()
        return
    if app_mode == "personnel":
        render_personnel_module()
        return

    # ── Sélecteur de table ────────────────────────────────────────────────────
    st.markdown("<span style='color:#94a3b8;font-size:.78rem;text-transform:uppercase;"
                "letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Table source</span>",
                unsafe_allow_html=True)
    t_cols = st.columns(len(tables))
    for i, tname in enumerate(tables):
        is_active = (st.session_state.selected_table == tname)
        m = f"tpill-{tname}"
        t_cols[i].markdown(
            f'<div id="{m}"></div><style>'
            f"div.element-container:has(#{m}) + div.element-container button{{"
            f"background:{'linear-gradient(135deg,#3b82f6,#7c3aed)' if is_active else '#1a1d27'}!important;"
            f"color:{'#ffffff' if is_active else '#94a3b8'}!important;"
            f"border:{'none' if is_active else '1px solid #2a2d3e'}!important;"
            f"border-radius:20px!important;width:100%;font-size:.85rem!important;}}</style>",
            unsafe_allow_html=True)
        if t_cols[i].button(tname, key=f"tpill_{tname}", width="stretch"):
            st.session_state.selected_table = tname
            st.session_state.conditions     = []
            st.session_state.results        = None
            st.session_state.enrich_count   = None
            st.session_state.joins          = []
            st.rerun()

    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
    current_table = st.session_state.selected_table

    # ── Résumé de la source de données ─────────────────────────────────────────
    _summary_labels = schema.get(current_table, {}).get("labels", {}) or {}
    render_table_summary(current_table, tables[current_table], _summary_labels)

    # ── Sources de données ─────────────────────────────────────────────────────
    available_joins = get_available_joins(schema, current_table, st.session_state.joins)

    if st.session_state.joins or available_joins:
        st.markdown(
            "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
            "letter-spacing:1px;font-family:JetBrains Mono,monospace;"
            "margin-bottom:6px;'>Sources de données</div>",
            unsafe_allow_html=True)

        # Calcul du nombre de colonnes : base + actives + disponibles + spacer
        n_active = len(st.session_state.joins)
        n_avail  = len(available_joins)
        _pill_cols = st.columns(
            [2] + [1.5] * n_active + [1.5] * n_avail + [4],
        )

        # Table de base (verrouillée)
        _pill_cols[0].markdown(
            f"<div style='background:#1d4ed822;color:#93c5fd;"
            f"border:0.5px solid #1d4ed8;border-radius:20px;"
            f"padding:4px 12px;font-size:.8rem;text-align:center;"
            f"white-space:nowrap;'>🔒 {current_table}</div>",
            unsafe_allow_html=True)

        # Tables déjà jointes (bouton ✕ pour retirer)
        for _i, _j in enumerate(list(st.session_state.joins)):
            if _pill_cols[1 + _i].button(
                f"✕ {_j['table']}", key=f"del_join_{_i}",
                use_container_width=True,
                help=f"Retirer {_j['table']}",
            ):
                st.session_state.joins.pop(_i)
                st.session_state.conditions = []
                st.session_state.results    = None
                st.rerun()

        # Tables disponibles (bouton ＋ pour ajouter)
        _off = 1 + n_active
        for _i, _aj in enumerate(available_joins):
            if _pill_cols[_off + _i].button(
                f"＋ {_aj['table']}", key=f"add_join_{_aj['table']}",
                use_container_width=True,
                help=f"Joindre {_aj['table']}  —  {_aj['on']}",
            ):
                st.session_state.joins.append({
                    "table": _aj["table"],
                    "type":  "LEFT JOIN",
                    "on":    _aj["on"],
                })
                st.session_state.conditions = []
                st.session_state.results    = None
                st.rerun()

        st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)

    # Colonnes disponibles : qualifiées (table.col) si jointures actives
    if st.session_state.joins:
        current_cols = get_all_columns(schema, current_table, st.session_state.joins)
    else:
        current_cols = tables[current_table]

    # ── Ajout de critère ──────────────────────────────────────────────────────
    # Labels lisibles pour le sélecteur de colonnes
    col_labels_map = get_column_labels(schema, current_table, st.session_state.joins)

    # Nonce pour pouvoir "vider" les textareas du mode couples au prochain run
    if "pair_text_nonce" not in st.session_state:
        st.session_state.pair_text_nonce = 0

    st.markdown("### ➕ Ajouter un critère")

    # ── Sélecteur de type de critère ─────────────────────────────────────────
    crit_type = st.radio(
        "Type de critère",
        ["🔍 Simple", "🔗 Couples (col1, col2)"],
        horizontal=True,
        key="crit_type",
        label_visibility="collapsed",
    )
    is_pair_mode = crit_type.startswith("🔗")

    # ════════════════════════════════════════════════════════════════════════
    # MODE SIMPLE : 1 colonne, 1 opérateur, 1+ valeur(s)
    # ════════════════════════════════════════════════════════════════════════
    if not is_pair_mode:
        fa, fb, fc, fd = st.columns([2, 2, 3, 1])
        with fa:
            new_col = st.selectbox(
                "Colonne", current_cols, key="new_col", label_visibility="collapsed",
                format_func=lambda c: col_labels_map.get(c, c),
            )
        with fb:
            is_date = is_date_col(new_col)
            if is_date:
                new_date_mode = st.radio(
                    "Mode de date",
                    ["📅 Date unique", "📆 Plage de dates"],
                    key="new_date_mode",
                    horizontal=False,
                    label_visibility="collapsed",
                )
            else:
                new_op = st.selectbox("Opérateur", OP_LABELS, key="new_op", label_visibility="collapsed")
        with fc:
            if is_date:
                is_range_mode = (new_date_mode == "📆 Plage de dates")
                if is_range_mode:
                    rc1, rc2 = st.columns(2)
                    with rc1:
                        new_date_start = st.date_input("Date de début", key="new_date_start")
                    with rc2:
                        new_date_end = st.date_input("Date de fin", key="new_date_end")
                else:
                    dc, bc = st.columns(2)
                    with dc:
                        new_date = st.date_input("Date", key="new_date")
                    with bc:
                        new_dates = st.text_input("Dates multiples", key="new_bulk_dates",
                                                  placeholder="YYYY-MM-DD, YYYY-MM-DD...")
            else:
                st.text_area("Valeur(s)", key="new_val",
                             placeholder="Une valeur, ou plusieurs séparées par des virgules / sauts de ligne",
                             height=80, label_visibility="collapsed")
        with fd:
            new_join = (st.radio("Lier", ["ET", "OU"], horizontal=False, key="new_join",
                                 label_visibility="collapsed")
                        if st.session_state.conditions else "ET")

    # ════════════════════════════════════════════════════════════════════════
    # MODE COUPLES : 2 colonnes, deux champs par couple, accumulation
    # ════════════════════════════════════════════════════════════════════════
    else:
        # Sélection des 2 colonnes
        pa, pb, pj = st.columns([2, 2, 1])
        with pa:
            _pair_col1 = st.selectbox(
                "1ère colonne", current_cols, key="pair_col1",
                format_func=lambda c: col_labels_map.get(c, c),
            )
        with pb:
            _other = [c for c in current_cols if c != _pair_col1]
            _pair_col2 = st.selectbox(
                "2ème colonne", _other, key="pair_col2",
                format_func=lambda c: col_labels_map.get(c, c),
            )
        with pj:
            new_join = (st.radio("Lier", ["ET", "OU"], horizontal=False,
                                 key="new_join_pair", label_visibility="collapsed")
                        if st.session_state.conditions else "ET")

        # ── Saisie en bulk : 2 textareas côte-à-côte ─────────────────────────
        _label1 = col_labels_map.get(_pair_col1, _pair_col1)
        _label2 = col_labels_map.get(_pair_col2, _pair_col2)
        _nonce  = st.session_state.pair_text_nonce
        _key1   = f"pair_text1_{_nonce}"
        _key2   = f"pair_text2_{_nonce}"

        st.caption(
            "💡 Collez vos données : une valeur par ligne dans chaque zone. "
            "Les couples se forment par appariement positionnel (ligne N + ligne N)."
        )

        ta1, ta2 = st.columns(2)
        with ta1:
            _pair_text1 = st.text_area(
                f"Valeurs pour « {_label1} »",
                key=_key1,
                height=180,
                placeholder=f"Une valeur de {_label1} par ligne\nDupont\nMartin\nDurand",
            )
        with ta2:
            _pair_text2 = st.text_area(
                f"Valeurs pour « {_label2} »",
                key=_key2,
                height=180,
                placeholder=(f"Une valeur de {_label2} par ligne\n"
                             f"1985-03-15\n1990-07-22\n2001-12-04"
                             if is_date_col(_pair_col2)
                             else f"Une valeur de {_label2} par ligne"),
            )

        # ── Aperçu en temps réel : nombre de lignes + alerte si déséquilibre ──
        _lines1 = [ln.strip() for ln in _pair_text1.splitlines() if ln.strip()]
        _lines2 = [ln.strip() for ln in _pair_text2.splitlines() if ln.strip()]
        _n1, _n2 = len(_lines1), len(_lines2)

        if _n1 == 0 and _n2 == 0:
            st.markdown(
                "<div style='color:#475569;font-size:.78rem;font-style:italic;"
                "font-family:JetBrains Mono,monospace;margin:6px 0;'>"
                "En attente de valeurs dans les deux zones.</div>",
                unsafe_allow_html=True,
            )
        elif _n1 != _n2:
            # Alerte : déséquilibre
            st.markdown(
                f"<div style='background:#3a1a1a;border:1px solid #ef4444;"
                f"border-left:3px solid #ef4444;border-radius:8px;"
                f"padding:10px 14px;margin:6px 0;"
                f"font-family:JetBrains Mono,monospace;font-size:.8rem;color:#fca5a5;'>"
                f"⚠️ <b>Déséquilibre détecté</b> &nbsp;·&nbsp; "
                f"« {_label1} » : <b style='color:#fbbf24;'>{_n1}</b> valeur(s) &nbsp;·&nbsp; "
                f"« {_label2} » : <b style='color:#fbbf24;'>{_n2}</b> valeur(s)<br>"
                f"<span style='color:#fca5a5;opacity:.85;'>"
                f"Les deux zones doivent contenir le même nombre de lignes "
                f"non-vides pour former des couples valides.</span></div>",
                unsafe_allow_html=True,
            )
        else:
            # Tout est OK : aperçu vert
            _preview_html = (
                f"<div style='background:#0f1e14;border:1px solid #14532d;"
                f"border-left:3px solid #4ade80;border-radius:8px;"
                f"padding:8px 14px;margin:6px 0;"
                f"font-family:JetBrains Mono,monospace;font-size:.78rem;color:#86efac;'>"
                f"✓ <b>{_n1} couple{'s' if _n1 > 1 else ''} prêt{'s' if _n1 > 1 else ''}</b> "
                f"à être ajouté{'s' if _n1 > 1 else ''}"
            )
            # Aperçu des 3 premiers couples
            if _n1 > 0:
                _show = list(zip(_lines1, _lines2))[:3]
                _items = " · ".join(f"«{v1}»+«{v2}»" for v1, v2 in _show)
                _suffix = f" +{_n1 - 3} autres" if _n1 > 3 else ""
                _preview_html += f"&nbsp;&nbsp;<span style='color:#94a3b8;'>[{_items}{_suffix}]</span>"
            _preview_html += "</div>"
            st.markdown(_preview_html, unsafe_allow_html=True)

    btn_a, btn_b = st.columns([3, 1])
    with btn_a:
        if st.button("➕ Ajouter le critère", width="stretch", type="primary"):
            _cond = None

            # ── Mode Couples ─────────────────────────────────────────────────
            if is_pair_mode:
                # Lire directement les variables locales (à jour pour ce run)
                _l1lines = [ln.strip() for ln in _pair_text1.splitlines() if ln.strip()]
                _l2lines = [ln.strip() for ln in _pair_text2.splitlines() if ln.strip()]

                if not _l1lines and not _l2lines:
                    st.warning("Saisissez des valeurs dans les deux zones.")
                elif len(_l1lines) != len(_l2lines):
                    st.warning(
                        f"Déséquilibre : « {col_labels_map.get(_pair_col1, _pair_col1)} » "
                        f"contient {len(_l1lines)} valeur(s), "
                        f"« {col_labels_map.get(_pair_col2, _pair_col2)} » "
                        f"en contient {len(_l2lines)}. "
                        f"Les deux zones doivent contenir le même nombre de lignes."
                    )
                else:
                    _pairs_final = list(zip(_l1lines, _l2lines))
                    _l1 = col_labels_map.get(_pair_col1, _pair_col1)
                    _l2 = col_labels_map.get(_pair_col2, _pair_col2)
                    _cond = {
                        "column":     f"({_pair_col1}, {_pair_col2})",
                        "label":      f"{_l1} + {_l2}",
                        "columns":    [_pair_col1, _pair_col2],
                        "col_labels": [_l1, _l2],
                        "operator":   "Couples",
                        "pairs":      _pairs_final,
                        "is_pair":    True,
                        "is_date":    False,
                        "is_bulk":    False,
                    }

            # ── Mode Simple ──────────────────────────────────────────────────
            else:
                _new_label = col_labels_map.get(new_col, new_col)
                if is_date:
                    _is_range = (st.session_state.get("new_date_mode") == "📆 Plage de dates")
                    if _is_range:
                        _ds = st.session_state.get("new_date_start")
                        _de = st.session_state.get("new_date_end")
                        if _ds and _de:
                            if _ds > _de:
                                st.warning("La date de début doit être antérieure à la date de fin.")
                            else:
                                _s = _ds.strftime("%Y-%m-%d")
                                _e = _de.strftime("%Y-%m-%d")
                                _cond = {
                                    "column": new_col, "label": _new_label,
                                    "operator": "Entre",
                                    "value": (_s, _e),
                                    "is_date": True, "is_bulk": False, "is_range": True,
                                }
                        else:
                            st.warning("Veuillez sélectionner une date de début et une date de fin.")
                    else:
                        _bulk_raw = st.session_state.get("new_bulk_dates", "")
                        _single   = st.session_state.get("new_date")
                        if _bulk_raw:
                            _vals = [d.strip() for d in re.split(r"[,\n]", _bulk_raw) if d.strip()]
                            _dts = []
                            for v in _vals:
                                if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                                    _dts.append(v)
                                else:
                                    st.warning(f"Format de date invalide : {v}")
                            if _dts:
                                _cond = {
                                    "column": new_col, "label": _new_label,
                                    "operator": "Commence par",
                                    "value": ", ".join(_dts), "values": _dts,
                                    "is_date": True, "is_bulk": True,
                                }
                            else:
                                st.warning("Aucune date valide")
                        elif _single is not None:
                            _cond = {
                                "column": new_col, "label": _new_label,
                                "operator": "Commence par",
                                "value": _single.strftime("%Y-%m-%d"),
                                "is_date": True, "is_bulk": False,
                            }
                        else:
                            st.warning("Veuillez sélectionner une date.")
                else:
                    raw    = st.session_state.get("new_val", "")
                    values = [v.strip() for v in re.split(r"[,\n]", raw) if v.strip()]
                    if not values:
                        st.warning("Veuillez entrer au moins une valeur.")
                    elif len(values) == 1:
                        _cond = {
                            "column": new_col, "label": _new_label, "operator": new_op,
                            "value": values[0], "is_date": False, "is_bulk": False,
                        }
                    else:
                        _cond = {
                            "column": new_col, "label": _new_label, "operator": new_op,
                            "value": ", ".join(values), "values": values,
                            "is_date": False, "is_bulk": True,
                        }

            # ── Finalisation : ajout direct ou placement dans l'arbre ──────────
            if _cond is not None:
                if not st.session_state.conditions:
                    _cond["join_op"]   = "ET"
                    _cond["or_target"] = "leaf"
                    st.session_state.conditions.append(_cond)
                else:
                    _cond["join_op"] = new_join
                    st.session_state._pending_cond = _cond
                # Vider les zones de couples après ajout réussi
                # (en incrémentant la nonce → les widgets seront recréés vides)
                if is_pair_mode:
                    st.session_state.pair_text_nonce += 1
                st.rerun()
    with btn_b:
        if st.button("🗑 Effacer", width="stretch"):
            st.session_state.conditions    = []
            st.session_state.results       = None
            st.session_state.enrich_count  = None
            st.session_state.pair_text_nonce += 1   # vide les textareas du mode couples
            st.session_state.pop("_pending_cond", None)
            st.rerun()

    st.markdown("---")

    # ── Arbre + requête SQL ───────────────────────────────────────────────────
    col_tree, col_sql = st.columns([3, 2], gap="large")
    with col_tree:
        st.markdown("### 🌳 Arbre de décision")
        st.caption("Cliquez sur un nœud ET / OU pour le basculer.")
        render_tree(st.session_state.conditions, current_table)
    with col_sql:
        with st.expander("🧾 Voir la requête SQL générée", expanded=False):
            st.markdown(f"<div class='sql-display'>"
                        f"{build_query_display(current_table, st.session_state.conditions, st.session_state.joins, schema)}"
                        f"</div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        if st.button("▶ Exécuter la requête", width="stretch", type="primary"):
            q, params = build_query(current_table, st.session_state.conditions, st.session_state.joins, schema)
            try:
                results = _get_db().read_sql(q, params)
                st.session_state.results = results
                st.session_state.fiches_visible = 100  # reset pagination
                where, wparams = build_where(st.session_state.conditions)
                st.session_state.last_where   = where
                st.session_state.last_params  = wparams
                st.session_state.enrich_count = compute_enrich_count(current_table, where, wparams, enrich)
                st.session_state["_last_cell_click"] = None
                _db_push_history(conn, user_id, current_table,
                                 st.session_state.conditions, len(results),
                                 joins=st.session_state.joins)
                st.rerun()  # le popover (rendu en haut) relit la DB avec la nouvelle entrée
            except Exception as e:
                st.error(f"Erreur SQL : {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # RÉSULTATS
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.results is None:
        return

    df          = st.session_state.results
    cnt         = st.session_state.enrich_count
    other_table = enrich[current_table]["label"]

    st.markdown("---")
    st.markdown("### 📊 Résultats")

    m1, m2, m3 = st.columns(3)
    m1.metric("Lignes",     len(df))
    m2.metric("Colonnes",   len(df.columns))
    m3.metric("Conditions", len(st.session_state.conditions))

    if len(df) == 0:
        st.info("Aucun résultat ne correspond à vos critères.")
    else:
        # ── Flags de colonnes présentes ───────────────────────────────────────
        has_nom        = "nom"           in df.columns
        has_prenom     = "prenom"        in df.columns
        has_dest       = "destination"   in df.columns
        has_depart     = "date_depart"   in df.columns
        has_budget     = "budget"        in df.columns
        has_note       = "note"          in df.columns
        has_continent  = "continent"     in df.columns
        has_type       = "type_voyage"   in df.columns
        has_duree      = "duree_jours"   in df.columns
        has_client_nom = "client_nom"    in df.columns
        has_ville      = "ville"         in df.columns
        has_client_id  = "client_id"     in df.columns

        tab1, tab2, tab3, tab4 = st.tabs(["📋 Grille", "👤 Fiches", "🗓 Timeline", "📈 Statistiques"])

        # ── TAB 1 — Grille ────────────────────────────────────────────────────
        with tab1:
            st.caption("💡 Cliquez sur une cellule pour explorer sa valeur.")
            event  = st.dataframe(df, width="stretch", hide_index=True,
                                  on_select="rerun", selection_mode=["single-row", "single-column"],
                                  key="result_df")
            sel    = getattr(event, "selection", None)
            rows_s = list(getattr(sel, "rows",    None) or (sel or {}).get("rows",    []))
            cols_s = list(getattr(sel, "columns", None) or (sel or {}).get("columns", []))
            if rows_s and cols_s:
                col_ref  = cols_s[0]
                col_name = col_ref if isinstance(col_ref, str) else df.columns[int(col_ref)]
                row_idx  = int(rows_s[0])
                try:
                    cell_val = df.iloc[row_idx][col_name]
                except KeyError:
                    cell_val = df.iloc[row_idx, df.columns.get_loc(col_name)]
                click_sig = f"{row_idx}__{col_name}__{cell_val}"
                if click_sig != st.session_state.get("_last_cell_click"):
                    st.session_state["_last_cell_click"]     = click_sig
                    st.session_state["_cell_dialog_pending"] = (col_name, cell_val)
            st.download_button("⬇ Télécharger CSV",
                df.to_csv(index=False).encode("utf-8"),
                f"resultats_{current_table}.csv", "text/csv")

        # ── TAB 2 — Fiches ────────────────────────────────────────────────────
        with tab2:
            _id_col     = _find_col(df, "id", "clients_id")
            _statut_col = _find_col(df, "statut", "clients_statut")

            # ── Helper de pagination ──────────────────────────────────────────
            def _render_load_more(total: int, scope_key: str) -> None:
                """Affiche un bouton 'Charger les 100 suivants' + un compteur.
                `total` est le nombre total d'éléments dans la vue courante.
                `scope_key` rend la key du bouton unique par vue.
                """
                visible = min(st.session_state.fiches_visible, total)
                st.markdown(
                    "<div style='display:flex;justify-content:center;align-items:center;"
                    "gap:14px;margin:18px 0 4px;color:#94a3b8;font-size:.82rem;"
                    "font-family:JetBrains Mono,monospace;'>"
                    f"<span>📄 Affichage <b style='color:#a5f3fc;'>{visible}</b> "
                    f"sur <b style='color:#86efac;'>{total}</b></span>"
                    "</div>",
                    unsafe_allow_html=True)
                if visible < total:
                    remaining   = total - visible
                    next_chunk  = min(100, remaining)
                    if st.button(
                        f"⬇ Charger les {next_chunk} suivantes  ({remaining} restantes)",
                        key=f"load_more_{scope_key}",
                        use_container_width=True,
                    ):
                        st.session_state.fiches_visible += 100
                        st.rerun()

            # ── Toggle vue (toujours visible) ─────────────────────────────────
            _prev_view = st.session_state.get("_tab2_view_prev", "client")
            _sel  = st.radio(
                "Vue", ["👤  Client", "✈️  Voyage"],
                horizontal=True,
                label_visibility="collapsed",
                key="tab2_view_radio",
            )
            _view = "voyage" if "Voyage" in _sel else "client"
            if _view != _prev_view:
                st.session_state.fiches_visible = 100   # reset pagination
                st.session_state["_tab2_view_prev"] = _view

            # Préchargement des compagnons (voyages de groupe)
            try:
                _all_voy = _get_db().read_sql("""
                    SELECT v.groupe_voyage_id, v.client_id,
                           c.nom, c.prenom, c.profession, c.ville, c.statut
                    FROM voyages v
                    JOIN clients c ON v.client_id = c.id
                    WHERE v.groupe_voyage_id IS NOT NULL
                """)
            except Exception:
                _all_voy = None

            # Passeports — uniquement pour les clients présents dans les résultats
            _all_pp = None
            _pp_id  = _id_col or _find_col(df, "client_id")
            if _pp_id and _pp_id in df.columns:
                try:
                    _cids = (df[_pp_id].dropna()
                             .apply(lambda x: str(int(float(x))))
                             .unique().tolist())
                    if _cids:
                        _all_pp = _get_db().read_sql(
                            f"SELECT * FROM passeports WHERE client_id IN ({','.join(_cids)})"
                        )
                except Exception:
                    _all_pp = None

            # ── BOUTON GLOBAL D'ENRICHISSEMENT (vue Client uniquement) ────────
            if _view == "client" and _id_col and _id_col in df.columns:
                # Collecte des client_ids uniques visibles (selon la pagination)
                _limit_for_enrich = st.session_state.fiches_visible
                # Pour la vue groupée, on prend les N premiers groupes ; pour la
                # vue simple, on prend les N premières lignes uniques par id
                _unique_df = (df.drop_duplicates(subset=[_id_col])
                                .iloc[:_limit_for_enrich])

                _enrich_snapshots = []
                for _, _r in _unique_df.iterrows():
                    _cid_raw = _r.get(_id_col)
                    if _cid_raw is None:
                        continue
                    try:
                        _cid_key = int(float(_cid_raw))
                    except (TypeError, ValueError):
                        _cid_key = str(_cid_raw)

                    # Collecter les destinations et types_voyage du client depuis le df complet
                    _client_rows = df[df[_id_col] == _cid_raw]
                    _destinations = []
                    _types_voyage = []
                    if "destination" in df.columns:
                        _destinations = [str(v) for v in _client_rows["destination"].dropna().unique() if str(v).strip()]
                    if "pays_destination" in df.columns:
                        _destinations += [str(v) for v in _client_rows["pays_destination"].dropna().unique() if str(v).strip()]
                    if "type_voyage" in df.columns:
                        _types_voyage = [str(v) for v in _client_rows["type_voyage"].dropna().unique() if str(v).strip()]

                    _enrich_snapshots.append((_cid_key, {
                        "id":            _cid_key,
                        "nom":           str(_r.get("nom", "")),
                        "prenom":        str(_r.get("prenom", "")),
                        "email":         str(_r.get("email", "")),
                        "ville":         str(_r.get("ville", "")),
                        "profession":    str(_r.get("profession", "")),
                        "situation_pro": str(_r.get("situation_pro", "")),
                        "destinations":  list(set(_destinations)),
                        "types_voyage":  list(set(_types_voyage)),
                    }))

                # Combien sont à enrichir (= pas encore dans le store) ?
                with _enrich_lock:
                    _todo = sum(1 for cid, _ in _enrich_snapshots
                                if cid not in _enrich_store)
                _batch = get_batch_state()

                # ── Barre d'enrichissement (bouton + progression live) ──────
                @st.fragment(run_every="0.8s" if _batch["running"] else None)
                def _render_global_enrich_bar(snapshots=_enrich_snapshots, todo=_todo):
                    bstate = get_batch_state()

                    # ── Détection : batch tout juste terminé → force un rerun ──
                    # global pour afficher les badges de traduction dans les cards
                    if (not bstate["running"]
                            and st.session_state.get("_batch_pending_refresh")):
                        st.session_state["_batch_pending_refresh"] = False
                        st.rerun(scope="app")

                    if bstate["running"]:
                        # Progression live
                        done  = bstate["done"]
                        total = bstate["total"]
                        pct   = int(100 * done / total) if total else 100
                        st.markdown(
                            f"<div style='background:linear-gradient(135deg,#0f1118,#13151d);"
                            f"border:1px solid #2a2d3e;border-left:3px solid #a78bfa;"
                            f"border-radius:10px;padding:10px 14px;margin:6px 0 12px;"
                            f"font-family:JetBrains Mono,monospace;'>"
                            f"<div style='display:flex;justify-content:space-between;"
                            f"align-items:center;gap:10px;font-size:.78rem;color:#94a3b8;'>"
                            f"<span>✨ Enrichissement en cours… "
                            f"<b style='color:#a5f3fc;'>{done}</b>"
                            f"<span style='opacity:.6;'> / {total}</span></span>"
                            f"<span style='color:#86efac;'>{pct} %</span></div>"
                            f"<div style='margin-top:6px;background:#1e2130;height:4px;"
                            f"border-radius:2px;overflow:hidden;'>"
                            f"<div style='width:{pct}%;height:100%;"
                            f"background:linear-gradient(90deg,#a78bfa,#86efac);"
                            f"transition:width .4s ease;'></div></div></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        # Bouton de déclenchement
                        if todo == 0:
                            st.markdown(
                                "<div style='color:#475569;font-size:.78rem;font-style:italic;"
                                "font-family:JetBrains Mono,monospace;margin:6px 0 12px;'>"
                                "✓ Toutes les fiches visibles sont déjà enrichies.</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            _marker = "global-enrich-trigger"
                            st.markdown(
                                f'<div id="{_marker}"></div><style>'
                                f'div.element-container:has(#{_marker})+div.element-container button {{'
                                f'background:linear-gradient(135deg,#a78bfa22,#86efac22) !important;'
                                f'color:#e8eaf0 !important;'
                                f'border:1px solid #a78bfa !important; border-radius:8px !important;'
                                f'font-family:"JetBrains Mono",monospace !important;'
                                f'font-size:.82rem !important; font-weight:600 !important;'
                                f'padding:10px 18px !important;'
                                f'}}'
                                f'div.element-container:has(#{_marker})+div.element-container button:hover {{'
                                f'background:linear-gradient(135deg,#a78bfa44,#86efac44) !important;'
                                f'box-shadow:0 0 16px #a78bfa66 !important;'
                                f'}}</style>',
                                unsafe_allow_html=True,
                            )
                            if st.button(
                                f"✨ Enrichir toutes les fiches  ·  {todo} à traiter",
                                key="global_enrich_btn",
                                use_container_width=True,
                                help="Lance les appels API en série, 1 fiche à la fois",
                            ):
                                if start_batch_enrichment(snapshots):
                                    # Marqueur pour qu'à la fin du batch on
                                    # rerun toute l'app et que les badges
                                    # de traduction apparaissent dans les cards
                                    st.session_state["_batch_pending_refresh"] = True
                                    st.rerun(scope="fragment")

                _render_global_enrich_bar()

            # ── VUE CLIENT ────────────────────────────────────────────────────
            if _view == "client":
                if has_nom and has_prenom and has_dest and _id_col:
                    _groups       = list(df.groupby(_id_col, sort=False))
                    _total        = len(_groups)
                    _limit        = st.session_state.fiches_visible
                    for client_id, group in _groups[:_limit]:
                        if _all_pp is not None:
                            try:
                                _cid = str(int(float(group.iloc[0].get(_id_col) or 0)))
                                _pp  = _all_pp[_all_pp["client_id"].astype(str) == _cid]
                            except Exception:
                                _pp = None
                        else:
                            _pp = None
                        # Récupérer les traductions si l'enrichissement est terminé
                        try:
                            _ck = int(float(group.iloc[0].get(_id_col) or 0))
                        except (TypeError, ValueError):
                            _ck = str(group.iloc[0].get(_id_col))
                        _state = get_enrichment_state(_ck)
                        _tx = None
                        if _state["status"] == "done":
                            _tx = (_state.get("data") or {}).get("translations")
                        render_client_profile_card(
                            client_row=group.iloc[0],
                            voyages_df=group,
                            all_voyages_df=_all_voy,
                            passeports_df=_pp,
                            translations=_tx,
                        )
                    _render_load_more(_total, "client_grouped")

                elif has_nom and has_prenom:
                    _total = len(df)
                    _limit = st.session_state.fiches_visible
                    _df_slice = df.iloc[:_limit]
                    cols_grid = st.columns(2)
                    _seen_cids = set()   # pour ne rendre le bloc enrich qu'une fois par client
                    for i, (_, row) in enumerate(_df_slice.iterrows()):
                        _s_val     = row.get(_statut_col) if _statut_col else None
                        stat_color = "#4ade80" if str(_s_val or "") == "actif" else "#f87171"
                        initials   = (str(row.get("prenom", "?"))[:1] + str(row.get("nom", "?"))[:1]).upper()
                        with cols_grid[i % 2]:
                            st.markdown(
                                f"<div style='background:#13151d;border:1px solid #1e2130;"
                                f"border-radius:12px;padding:16px 18px;margin-bottom:0;"
                                f"border-bottom-left-radius:0;border-bottom-right-radius:0;'>"
                                f"<div style='display:flex;align-items:center;gap:12px;'>"
                                f"<div style='width:40px;height:40px;border-radius:50%;"
                                f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                                f"display:flex;align-items:center;justify-content:center;"
                                f"font-weight:700;color:white;'>{initials}</div>"
                                f"<div><div style='font-weight:600;color:#e8eaf0;'>"
                                f"{row.get('prenom','')} {row.get('nom','')}</div>"
                                f"<div style='font-size:.8rem;color:#64748b;'>"
                                f"{row.get('ville','')} &nbsp;·&nbsp; "
                                f"<span style='color:{stat_color};'>{row.get('statut','')}</span>"
                                f"</div></div></div></div>",
                                unsafe_allow_html=True)

                            # ── Bloc enrichissement API (1 fois max par client) ──
                            _cid_raw = row.get(_id_col) if _id_col else row.get("id")
                            _cid_key = None
                            if _cid_raw is not None and str(_cid_raw) not in ("", "—", "nan"):
                                try:
                                    _cid_key = int(float(_cid_raw))
                                except (TypeError, ValueError):
                                    _cid_key = str(_cid_raw)

                            if _cid_key is not None and _cid_key not in _seen_cids:
                                _seen_cids.add(_cid_key)
                                _snapshot = {
                                    "id":     _cid_key,
                                    "nom":    str(row.get("nom", "")),
                                    "prenom": str(row.get("prenom", "")),
                                    "email":  str(row.get("email", "")),
                                    "ville":  str(row.get("ville", "")),
                                }
                                render_client_enrichment_block(_cid_key, _snapshot)

                            # Fermeture visuelle de la carte (ligne du bas arrondie)
                            st.markdown(
                                "<div style='background:#13151d;border:1px solid #1e2130;"
                                "border-top:none;border-radius:0 0 12px 12px;height:6px;"
                                "margin-bottom:12px;'></div>",
                                unsafe_allow_html=True)
                    _render_load_more(_total, "client_simple")

                elif has_dest:
                    _total = len(df)
                    _limit = st.session_state.fiches_visible
                    _df_slice = df.iloc[:_limit]
                    cols_grid = st.columns(2)
                    for i, (_, row) in enumerate(_df_slice.iterrows()):
                        cont     = row.get("continent", "")
                        tv       = row.get("type_voyage", "")
                        cont_col = CONT_COLORS.get(cont, "#6b7280")
                        tv_col   = TYPE_COLORS.get(tv,   "#6b7280")
                        note_v   = row.get("note", None)
                        stars    = ("⭐" * int(note_v)) if note_v and not pd.isna(note_v) else "—"
                        cnom     = ""
                        if has_client_nom:
                            cnom = f"{row.get('client_prenom','')} {row.get('client_nom','')}".strip()
                        elif has_client_id:
                            cnom = f"Client #{int(row.get('client_id', 0))}"
                        cols_grid[i % 2].markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-top:3px solid {cont_col};"
                            f"border-radius:12px;padding:16px 18px;margin-bottom:12px;'>"
                            f"<div style='display:flex;justify-content:space-between;align-items:start;'>"
                            f"<div><div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>"
                            f"{row.get('destination','')}</div>"
                            f"<div style='font-size:.78rem;color:#64748b;'>"
                            f"{row.get('pays_destination','')} · "
                            f"<span style='color:{cont_col};'>{cont}</span></div></div>"
                            f"<span style='background:{tv_col}22;color:{tv_col};"
                            f"font-size:.7rem;padding:3px 10px;border-radius:10px;"
                            f"white-space:nowrap;'>{tv}</span></div>"
                            f"<div style='margin:10px 0;font-size:.8rem;color:#94a3b8;'>"
                            f"📅 {str(row.get('date_depart',''))[:10]} → "
                            f"{str(row.get('date_retour',''))[:10]}"
                            f"{'&nbsp;&nbsp;·&nbsp;&nbsp;🕒 ' + str(row.get('duree_jours','')) + 'j' if row.get('duree_jours') else ''}"
                            f"{'&nbsp;&nbsp;·&nbsp;&nbsp;' + cnom if cnom else ''}</div>"
                            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                            f"<span style='color:#64748b;font-size:.78rem;'>🏨 {row.get('hotel','')}</span>"
                            f"<div style='text-align:right;'>"
                            f"<div style='color:#4ade80;font-weight:700;"
                            f"font-family:JetBrains Mono,monospace;'>"
                            f"{int(row.get('budget', 0)):,}€</div>"
                            f"<div style='font-size:.75rem;'>{stars}</div>"
                            f"</div></div></div>",
                            unsafe_allow_html=True)
                    _render_load_more(_total, "client_dest")
                else:
                    st.info("Aucune vue fiche disponible pour ces colonnes.")

            # ── VUE VOYAGE ────────────────────────────────────────────────────
            else:
                if has_dest:
                    _total = len(df)
                    _limit = st.session_state.fiches_visible
                    _df_slice = df.iloc[:_limit]
                    for _, vrow in _df_slice.iterrows():
                        render_voyage_profile_card(
                            voyage_row=vrow,
                            all_voyages_df=_all_voy,
                            col_statut_client=_statut_col or "statut",
                            show_client_info=False,
                        )
                    _render_load_more(_total, "voyage")
                else:
                    st.info("La vue Voyage nécessite une colonne destination.")

        # ── TAB 3 — Timeline ──────────────────────────────────────────────────
        with tab3:
            if not has_depart:
                st.info("La timeline nécessite une colonne `date_depart`.")
            else:
                df_tl = df.copy()
                df_tl["date_depart"] = pd.to_datetime(df_tl["date_depart"], errors="coerce")
                if "date_retour" in df_tl.columns:
                    df_tl["date_retour"] = pd.to_datetime(df_tl["date_retour"], errors="coerce")
                df_tl = df_tl.dropna(subset=["date_depart"]).sort_values("date_depart")
                if df_tl.empty:
                    st.info("Aucune date valide trouvée.")
                else:
                    d_min     = df_tl["date_depart"].min()
                    d_max     = df_tl["date_retour"].max() if "date_retour" in df_tl.columns else df_tl["date_depart"].max()
                    span      = max((d_max - d_min).days, 1)
                    current_ym = None
                    for _, row in df_tl.iterrows():
                        ym = row["date_depart"].strftime("%B %Y").capitalize()
                        if ym != current_ym:
                            current_ym = ym
                            st.markdown(
                                f"<div style='color:#6366f1;font-size:.75rem;font-weight:700;"
                                f"text-transform:uppercase;letter-spacing:1px;"
                                f"font-family:JetBrains Mono,monospace;margin:18px 0 6px;'>{ym}</div>",
                                unsafe_allow_html=True)
                        dep      = row["date_depart"]
                        ret      = row.get("date_retour", dep)
                        if pd.isna(ret): ret = dep
                        duree    = max((ret - dep).days, 1)
                        cont     = row.get("continent", "")
                        tv       = row.get("type_voyage", "")
                        cont_col = CONT_COLORS.get(cont, "#6b7280")
                        tv_col   = TYPE_COLORS.get(tv, "#6b7280")
                        note_v   = row.get("note", None)
                        stars    = "⭐" * int(note_v) if note_v and not pd.isna(note_v) else ""
                        cnom     = ""
                        if has_client_nom:
                            cnom = f"{row.get('client_prenom','')} {row.get('client_nom','')}".strip()
                        elif has_nom and has_prenom:
                            cnom = f"{row.get('prenom','')} {row.get('nom','')}".strip()
                        left_pct  = round((dep - d_min).days / span * 100, 1)
                        width_pct = max(round(duree / span * 100, 1), 1.5)
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:12px 16px;margin-bottom:8px;'>"
                            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>"
                            f"<span style='width:8px;height:8px;border-radius:50%;"
                            f"background:{cont_col};display:inline-block;flex-shrink:0;'></span>"
                            f"<span style='font-weight:600;color:#e8eaf0;font-size:.9rem;'>{row.get('destination','')}</span>"
                            f"{'<span style=\"color:#94a3b8;font-size:.78rem;\"> · ' + cnom + '</span>' if cnom else ''}"
                            f"<span style='margin-left:auto;color:#64748b;font-size:.75rem;'>"
                            f"{dep.strftime('%d %b %Y')} → {ret.strftime('%d %b %Y')} · {duree}j</span></div>"
                            f"<div style='position:relative;height:10px;background:#1e293b;"
                            f"border-radius:5px;overflow:hidden;'>"
                            f"<div style='position:absolute;left:{left_pct}%;width:{width_pct}%;"
                            f"height:100%;background:linear-gradient(90deg,{cont_col},{tv_col});"
                            f"border-radius:5px;'></div></div>"
                            f"<div style='margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;'>"
                            f"<span style='background:{tv_col}22;color:{tv_col};font-size:.7rem;"
                            f"padding:2px 8px;border-radius:10px;'>{tv}</span>"
                            f"{'<span style=\"font-size:.75rem;color:#4ade80;font-family:JetBrains Mono,monospace;\">' + str(int(row.get('budget',0))) + '€</span>' if row.get('budget') else ''}"
                            f"<span style='font-size:.72rem;'>{stars}</span>"
                            f"</div></div>",
                            unsafe_allow_html=True)

        # ── TAB 4 — Statistiques ──────────────────────────────────────────────
        with tab4:
            def _hbar(label, value, total, color, fmt=None):
                pct   = round(value / total * 100) if total else 0
                v_str = fmt(value) if fmt else str(value)
                return (
                    f"<div style='margin-bottom:10px;'>"
                    f"<div style='display:flex;justify-content:space-between;"
                    f"font-size:.8rem;margin-bottom:3px;'>"
                    f"<span style='color:#c8cad6;'>{label}</span>"
                    f"<span style='color:#94a3b8;font-family:JetBrains Mono,monospace;'>{v_str}</span>"
                    f"</div>"
                    f"<div style='background:#1e293b;border-radius:4px;height:8px;'>"
                    f"<div style='width:{pct}%;height:100%;border-radius:4px;"
                    f"background:{color};transition:width .3s;'></div></div></div>"
                )

            if has_dest:
                sa, sb = st.columns(2)
                n_total = len(df)
                with sa:
                    if has_budget:
                        bgt_total = df["budget"].sum()
                        bgt_moy   = df["budget"].mean()
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                            f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
                            f"letter-spacing:1px;margin-bottom:6px;'>Budget total</div>"
                            f"<div style='color:#4ade80;font-size:1.6rem;font-weight:800;"
                            f"font-family:JetBrains Mono,monospace;'>{int(bgt_total):,}€</div>"
                            f"<div style='color:#64748b;font-size:.8rem;'>moy. {int(bgt_moy):,}€ / voyage</div>"
                            f"</div>", unsafe_allow_html=True)
                    if has_duree:
                        d_moy = df["duree_jours"].mean()
                        d_max_v = df["duree_jours"].max()
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                            f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
                            f"letter-spacing:1px;margin-bottom:6px;'>Durée moyenne</div>"
                            f"<div style='color:#60a5fa;font-size:1.6rem;font-weight:800;"
                            f"font-family:JetBrains Mono,monospace;'>{d_moy:.1f}j</div>"
                            f"<div style='color:#64748b;font-size:.8rem;'>max {int(d_max_v)}j</div>"
                            f"</div>", unsafe_allow_html=True)
                    if has_note:
                        _note_col = _find_col(df, "note", "voyages_note")
                        notes = df[_note_col].dropna() if _note_col else pd.Series([], dtype=float)
                        if len(notes):
                            note_moy = notes.mean()
                            st.markdown(
                                f"<div style='background:#13151d;border:1px solid #1e2130;"
                                f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                                f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
                                f"letter-spacing:1px;margin-bottom:6px;'>Note moyenne</div>"
                                f"<div style='color:#fbbf24;font-size:1.6rem;font-weight:800;'>"
                                f"{'⭐' * round(note_moy)} <span style='font-size:.9rem;"
                                f"font-family:JetBrains Mono,monospace;'>{note_moy:.1f}/5</span></div>"
                                f"<div style='color:#64748b;font-size:.8rem;'>{len(notes)} avis</div>"
                                f"</div>", unsafe_allow_html=True)
                with sb:
                    if has_continent:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                    "letter-spacing:1px;margin-bottom:8px;'>Par continent</div>",
                                    unsafe_allow_html=True)
                        bars = "".join(_hbar(c, v, n_total, CONT_COLORS.get(c, "#6b7280"))
                                       for c, v in df["continent"].value_counts().items())
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                    f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>{bars}</div>",
                                    unsafe_allow_html=True)
                    if has_type:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                    "letter-spacing:1px;margin-bottom:8px;'>Par type</div>",
                                    unsafe_allow_html=True)
                        bars = "".join(_hbar(tv, v, n_total, TYPE_COLORS.get(tv, "#6b7280"))
                                       for tv, v in df["type_voyage"].value_counts().items())
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                    f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                                    unsafe_allow_html=True)
                if has_budget:
                    st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                "letter-spacing:1px;margin:14px 0 8px;'>Top destinations — budget</div>",
                                unsafe_allow_html=True)
                    top_dest = df.groupby("destination")["budget"].sum().sort_values(ascending=False).head(8)
                    max_b    = top_dest.max()
                    bars = "".join(
                        _hbar(dest, int(b), int(max_b),
                              CONT_COLORS.get(df[df["destination"] == dest]["continent"].iloc[0] if has_continent else "", "#6b7280"),
                              fmt=lambda x: f"{x:,}€")
                        for dest, b in top_dest.items()
                    )
                    st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                                unsafe_allow_html=True)

            elif has_nom:
                sa, sb = st.columns(2)
                n_total = len(df)
                with sa:
                    if "statut" in df.columns or "clients_statut" in df.columns:
                        _sc = _find_col(df, "statut", "clients_statut")
                        n_actif = (_sc and (df[_sc] == "actif").sum()) or 0
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                            f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
                            f"letter-spacing:1px;margin-bottom:6px;'>Statut</div>"
                            f"<div style='display:flex;gap:14px;'>"
                            f"<div><div style='color:#4ade80;font-size:1.4rem;font-weight:800;"
                            f"font-family:JetBrains Mono,monospace;'>{n_actif}</div>"
                            f"<div style='color:#64748b;font-size:.78rem;'>actifs</div></div>"
                            f"<div><div style='color:#f87171;font-size:1.4rem;font-weight:800;"
                            f"font-family:JetBrains Mono,monospace;'>{n_total - n_actif}</div>"
                            f"<div style='color:#64748b;font-size:.78rem;'>inactifs</div></div>"
                            f"</div></div>", unsafe_allow_html=True)
                with sb:
                    if has_ville:
                        _ville_col = _find_col(df, "ville", "clients_ville")
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                    "letter-spacing:1px;margin-bottom:8px;'>Par ville</div>",
                                    unsafe_allow_html=True)
                        bars = "".join(_hbar(v, c, n_total, "#6366f1")
                                       for v, c in df[_ville_col].value_counts().head(8).items())
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                    f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                                    unsafe_allow_html=True)
            else:
                st.info("Statistiques non disponibles pour cette combinaison de colonnes.")

    # ── Dialog cellule ─────────────────────────────────────────────────────────
    if st.session_state.get("_cell_dialog_pending"):
        col_n, val_n = st.session_state.pop("_cell_dialog_pending")
        cell_filter_dialog(col_n, val_n)

    # ── Rapport ────────────────────────────────────────────────────────────────
    if st.session_state.results is not None and len(st.session_state.results) > 0:
        _r_col, _ = st.columns([2, 8])
        with _r_col:
            m_id = "rpt-marker"
            st.markdown(
                f'<div id="{m_id}"></div><style>'
                f"div.element-container:has(#{m_id}) + div.element-container button{{"
                f"background:linear-gradient(135deg,#059669,#0d9488)!important;"
                f"color:white!important;border:none!important;"
                f"border-radius:8px!important;font-size:.85rem!important;}}"
                f"div.element-container:has(#{m_id}) + div.element-container button:hover{{"
                f"filter:brightness(1.12)!important;transform:translateY(-1px)!important;}}"
                f"</style>", unsafe_allow_html=True)
            if st.button("📄 Rapport", key="rpt_open",
                         help="Générer un rapport Word ou PDF de ces résultats",
                         use_container_width=True):
                _rapport_dialog(
                    st.session_state.results,
                    st.session_state.conditions,
                    current_table,
                    st.session_state.joins,
                    st.session_state.last_where,
                )

    # ── Bouton Enrichir (masqué si la table est déjà jointe manuellement) ──────
    joined_tables = {j["table"] for j in st.session_state.joins}
    if enrich.get(current_table) and enrich[current_table]["other"] in joined_tables:
        return   # jointure déjà active → bouton Enrichir inutile

    st.markdown("---")
    if cnt is None:
        st.info(f"Calcul du lien avec **{other_table}** en cours…")
    elif cnt == "done":
        pass
    elif cnt == 0:
        st.markdown(
            f"<div style='background:#1a1d27;border:1px solid #2a2d3e;border-radius:10px;"
            f"padding:14px 18px;color:#6b7280;font-size:.9rem;'>"
            f"ℹ️ Aucune information supplémentaire dans la table "
            f"<b style='color:#94a3b8;'>{other_table}</b> pour ces résultats.</div>",
            unsafe_allow_html=True)
    else:
        m = "enrich-btn-marker"
        st.markdown(
            f'<div id="{m}"></div><style>'
            f"div.element-container:has(#{m}) + div.element-container button{{"
            f"background:linear-gradient(135deg,#065f46,#047857)!important;"
            f"border:1px solid #059669!important;box-shadow:0 0 14px #05966966!important;"
            f"font-size:.92rem!important;padding:10px 0!important;}}"
            f"div.element-container:has(#{m}) + div.element-container button:hover{{"
            f"filter:brightness(1.15)!important;transform:translateY(-1px)!important;}}</style>",
            unsafe_allow_html=True)
        if st.button(
            f"🔗 Enrichir avec {other_table} — {cnt} ligne{'s' if cnt > 1 else ''} disponible{'s' if cnt > 1 else ''}",
            width="stretch", key="enrich_btn"):
            try:
                enriched = run_enrich_query(current_table,
                                            st.session_state.last_where,
                                            st.session_state.last_params,
                                            enrich)
                st.session_state.results      = enriched
                st.session_state.enrich_count = "done"
                st.session_state["_last_cell_click"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erreur enrichissement : {e}")


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION MÉTIER  —  modifier ici pour changer les tables / colonnes
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# LANCEMENT
# ══════════════════════════════════════════════════════════════════════════════

# 1. Page de connexion — affichée tant qu'aucune DB n'est configurée
try:
    _cfg   = load_config()
    SCHEMA = _cfg["schema"]
    ENRICH = _cfg.get("enrich", {})
except FileNotFoundError as _e:
    st.error(f"⚠️ {_e}")
    st.stop()
except (ValueError, KeyError) as _e:
    st.error(f"⚠️ Erreur dans le fichier de config : {_e}")
    st.stop()

run_app(SCHEMA, ENRICH)
