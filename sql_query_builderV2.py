import streamlit as st
import pandas as pd
import sqlite3
import re
import time

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
/* Enrich button override */
.enrich-btn button{
   background:linear-gradient(135deg,#065f46,#047857)!important;
   border:1px solid #059669!important;
   box-shadow:0 0 12px #05966944!important;}
.enrich-btn button:hover{
   filter:brightness(1.15)!important;}
</style>
""", unsafe_allow_html=True)

# ── DB ─────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,nom TEXT,prenom TEXT,
      email TEXT,telephone TEXT,ville TEXT,pays TEXT,date_inscription TEXT,statut TEXT);
    INSERT INTO clients VALUES
    (1,'Lemaire','Sophie','sophie.lemaire@mail.fr','0612345678','Paris','France','2020-01-15','actif'),
    (2,'Garnier','Thomas','t.garnier@mail.fr','0623456789','Lyon','France','2019-06-22','actif'),
    (3,'Faure','Julie','julie.faure@mail.fr','0634567890','Marseille','France','2021-03-10','actif'),
    (4,'Chevalier','Marc','marc.chev@mail.fr','0645678901','Bordeaux','France','2018-11-05','inactif'),
    (5,'Morin','Lucie','lucie.morin@mail.fr','0656789012','Nantes','France','2022-07-30','actif'),
    (6,'Perrin','Antoine','a.perrin@mail.fr','0667890123','Toulouse','France','2020-09-14','actif'),
    (7,'Blanc','Camille','c.blanc@mail.fr','0678901234','Strasbourg','France','2023-02-01','actif'),
    (8,'Renard','Nicolas','n.renard@mail.fr','0689012345','Lille','France','2017-05-18','inactif'),
    (9,'Vidal','Inès','ines.vidal@mail.fr','0690123456','Nice','France','2021-12-25','actif'),
    (10,'Roy','Kevin','kevin.roy@mail.fr','0601234567','Rennes','France','2022-04-03','actif'),
    (11,'Caron','Éléonore','e.caron@mail.fr','0611223344','Paris','France','2019-08-19','actif'),
    (12,'Picard','Bastien','b.picard@mail.fr','0622334455','Montpellier','France','2023-10-11','actif');

    CREATE TABLE IF NOT EXISTS voyages(id INTEGER PRIMARY KEY,client_id INTEGER,
      destination TEXT,pays_destination TEXT,continent TEXT,
      date_depart TEXT,date_retour TEXT,duree_jours INTEGER,
      type_voyage TEXT,transport TEXT,hotel TEXT,
      budget REAL,statut TEXT,note INTEGER,
      FOREIGN KEY(client_id) REFERENCES clients(id));
    INSERT INTO voyages VALUES
    (1,1,'Tokyo','Japon','Asie','2023-04-10','2023-04-24',14,'Tourisme','Avion','Grand Hyatt Tokyo',3200.00,'terminé',5),
    (2,1,'Barcelone','Espagne','Europe','2022-07-15','2022-07-22',7,'Tourisme','Train','Hotel Arts',1100.00,'terminé',4),
    (3,2,'New York','États-Unis','Amérique','2023-08-01','2023-08-10',9,'Affaires','Avion','Marriott Times Square',2800.00,'terminé',4),
    (4,2,'Rome','Italie','Europe','2022-12-20','2022-12-27',7,'Tourisme','Avion','Hotel Eden',1350.00,'terminé',5),
    (5,3,'Bali','Indonésie','Asie','2023-06-01','2023-06-15',14,'Détente','Avion','Four Seasons Bali',2900.00,'terminé',5),
    (6,3,'Lisbonne','Portugal','Europe','2024-03-10','2024-03-14',4,'City Break','Avion','Bairro Alto Hotel',750.00,'terminé',4),
    (7,4,'Dubai','Émirats Arabes Unis','Asie','2023-01-05','2023-01-12',7,'Luxe','Avion','Burj Al Arab',5500.00,'terminé',5),
    (8,5,'Marrakech','Maroc','Afrique','2023-10-20','2023-10-27',7,'Culturel','Avion','La Mamounia',1800.00,'terminé',5),
    (9,5,'Amsterdam','Pays-Bas','Europe','2024-05-01','2024-05-04',3,'City Break','Train','Hotel V Nesplein',620.00,'terminé',3),
    (10,6,'Maldives','Maldives','Asie','2023-02-14','2023-02-21',7,'Lune de miel','Avion','Conrad Maldives',6200.00,'terminé',5),
    (11,6,'Prague','Tchéquie','Europe','2022-11-03','2022-11-06',3,'City Break','Avion','Augustine Hotel',580.00,'terminé',4),
    (12,7,'Sydney','Australie','Océanie','2023-12-22','2024-01-05',14,'Tourisme','Avion','Park Hyatt Sydney',4100.00,'terminé',5),
    (13,7,'Athènes','Grèce','Europe','2023-09-08','2023-09-15',7,'Culturel','Avion','Hotel Grande Bretagne',1250.00,'terminé',4),
    (14,8,'Reykjavik','Islande','Europe','2023-03-15','2023-03-20',5,'Aventure','Avion','Ion Adventure Hotel',1700.00,'terminé',4),
    (15,9,'Kyoto','Japon','Asie','2024-04-01','2024-04-10',9,'Culturel','Avion','The Ritz-Carlton Kyoto',3600.00,'terminé',5),
    (16,9,'Séville','Espagne','Europe','2023-05-18','2023-05-22',4,'City Break','Avion','Hotel Alfonso XIII',890.00,'terminé',4),
    (17,10,'Cancún','Mexique','Amérique','2023-07-01','2023-07-14',13,'Plage','Avion','Nizuc Resort',3100.00,'terminé',5),
    (18,10,'Berlin','Allemagne','Europe','2022-10-29','2022-10-31',2,'City Break','Train','Hotel de Rome',410.00,'terminé',3),
    (19,11,'Cape Town','Afrique du Sud','Afrique','2023-11-10','2023-11-24',14,'Safari','Avion','The Silo Hotel',4800.00,'terminé',5),
    (20,11,'Bruges','Belgique','Europe','2024-02-14','2024-02-16',2,'Romantique','Train','Hotel Dukes Palace',490.00,'terminé',4),
    (21,12,'Costa Rica','Costa Rica','Amérique','2024-01-15','2024-01-28',13,'Aventure','Avion','Nayara Springs',3900.00,'terminé',5),
    (22,1,'Singapour','Singapour','Asie','2024-06-20','2024-06-28',8,'Affaires','Avion','Marina Bay Sands',3400.00,'à venir',NULL),
    (23,3,'New York','États-Unis','Amérique','2024-09-01','2024-09-08',7,'Tourisme','Avion','The Plaza',2600.00,'à venir',NULL),
    (24,5,'Tenerife','Espagne','Europe','2024-08-10','2024-08-17',7,'Plage','Avion','Royal Hideaway',1500.00,'à venir',NULL);
    """)
    conn.commit()
    return conn

# ── Constants ──────────────────────────────────────────────────────────────────
TABLES = {
    "clients": ["id","nom","prenom","email","telephone","ville","pays","date_inscription","statut"],
    "voyages": ["id","client_id","destination","pays_destination","continent",
                "date_depart","date_retour","duree_jours","type_voyage",
                "transport","hotel","budget","statut","note"],
}

# ══════════════════════════════════════════════════════════════════════════════
# FK INTROSPECTION — lit le schéma SQLite via PRAGMA
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def get_fk_graph(_conn_id: int):
    """
    Retourne toutes les relations FK trouvées dans le schéma.
    Format : [(from_table, from_col, to_table, to_col), ...]
    Accepte _conn_id (hash) pour invalider le cache si besoin.
    """
    conn = get_connection()
    rels = []
    cursor = conn.cursor()
    for table in TABLES:
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for fk in cursor.fetchall():
            # fk: (id, seq, ref_table, from_col, to_col, ...)
            rels.append((table, fk[3], fk[2], fk[4]))
    return rels   # ex: [("voyages","client_id","clients","id")]


def fk_rels() -> list:
    """Raccourci — retourne les relations FK cachées."""
    return get_fk_graph(id(get_connection()))


def build_join_sql(tables: list, rels: list) -> tuple[str, list]:
    """
    Construit la clause FROM … JOIN … ON … pour une liste de tables ordonnée.
    Retourne (from_sql, join_conditions_display).
    """
    if len(tables) == 1:
        return tables[0], []

    base  = tables[0]
    parts = [base]
    infos = []
    joined = {base}

    for t in tables[1:]:
        cond = None
        for (t1, c1, t2, c2) in rels:
            if t1 in joined and t2 == t:
                cond = f"{t1}.{c1} = {t}.{c2}"
                break
            if t2 in joined and t1 == t:
                cond = f"{t}.{c1} = {t2}.{c2}"
                break
        if cond:
            parts.append(f"JOIN {t} ON {cond}")
            infos.append(f"{cond}")
        else:
            parts.append(f"CROSS JOIN {t}")
            infos.append(None)
        joined.add(t)

    return " ".join(parts), infos


def enrich_options(current_tables: list, where: str, params: list) -> list:
    """
    Propose les tables joignables via FK qui ont des données en commun.
    Retourne [{"table", "join_on", "count", "fk_label"}, ...]
    """
    rels  = fk_rels()
    conn  = get_connection()
    opts  = []
    seen  = set()

    for (t1, c1, t2, c2) in rels:
        # t1 → t2 : t1 est dans current_tables, t2 est une table à proposer
        if t1 in current_tables and t2 not in current_tables and t2 in TABLES and t2 not in seen:
            try:
                sql = (f"SELECT COUNT(*) AS total FROM {t2} "
                       f"WHERE {t2}.{c2} IN (SELECT {t1}.{c1} FROM {t1} WHERE {where})")
                r   = pd.read_sql_query(sql, conn, params=params)
                opts.append({"table": t2, "join_on": f"{t1}.{c1} = {t2}.{c2}",
                              "count": int(r["total"].iloc[0]),
                              "fk_label": f"{t1}.{c1} → {t2}.{c2}"})
                seen.add(t2)
            except Exception:
                pass
        # Inverse : t2 est dans current_tables, t1 est à proposer
        if t2 in current_tables and t1 not in current_tables and t1 in TABLES and t1 not in seen:
            try:
                sql = (f"SELECT COUNT(*) AS total FROM {t1} "
                       f"WHERE {t1}.{c1} IN (SELECT {t2}.{c2} FROM {t2} WHERE {where})")
                r   = pd.read_sql_query(sql, conn, params=params)
                opts.append({"table": t1, "join_on": f"{t1}.{c1} = {t2}.{c2}",
                              "count": int(r["total"].iloc[0]),
                              "fk_label": f"{t2}.{c2} → {t1}.{c1}"})
                seen.add(t1)
            except Exception:
                pass
    return opts


def run_join_query(tables: list, where: str, params: list) -> "pd.DataFrame":
    """Exécute un SELECT * avec JOIN sur toutes les tables données."""
    rels = fk_rels()
    from_sql, _ = build_join_sql(tables, rels)
    # Alias les colonnes ambiguës (id, statut…)
    col_parts = []
    for t in tables:
        for c in TABLES[t]:
            alias = f"{t}__{c}" if any(c in TABLES[o] for o in tables if o != t) else c
            col_parts.append(f"{t}.{c} AS {alias}")
    select = ", ".join(col_parts)
    sql    = f"SELECT {select} FROM {from_sql}"
    if where and where != "1=1":
        sql += f" WHERE {where}"
    return pd.read_sql_query(sql, get_connection(), params=params)

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

# Colonnes visibles en mode simplifié : (col_technique, label_affichage)
SIMPLIFIED_COLS = {
    "clients": [
        ("nom",              "Nom de famille"),
        ("prenom",           "Prénom"),
        ("email",            "Email"),
        ("ville",            "Ville"),
        ("pays",             "Pays"),
        ("date_inscription", "Date d'inscription"),
        ("statut",           "Statut (actif / inactif)"),
    ],
    "voyages": [
        ("destination",      "Destination"),
        ("pays_destination", "Pays de destination"),
        ("continent",        "Continent"),
        ("date_depart",      "Date de départ"),
        ("date_retour",      "Date de retour"),
        ("type_voyage",      "Type de voyage"),
        ("transport",        "Moyen de transport"),
        ("budget",           "Budget (€)"),
        ("statut",           "Statut du voyage"),
        ("note",             "Note (1 – 5)"),
    ],
}

def is_date_col(col: str) -> bool:
    return "date" in col.lower()

def build_date_value(year: int, month: int, day: int) -> str:
    if month == 0:   return f"{year:04d}"
    elif day == 0:   return f"{year:04d}-{month:02d}"
    else:            return f"{year:04d}-{month:02d}-{day:02d}"

# ── State ──────────────────────────────────────────────────────────────────────
for k, v in [("conditions",[]),("selected_tables",["clients"]),
             ("results",None),("enrich_count",None),
             ("last_where",""),("last_params",[]),("editing",{}),
             ("_selected_row_idx", None), ("expert_mode", False),
             ("enrich_opts", [])]:
    if k not in st.session_state:
        st.session_state[k] = v
# Compatibilité : si l'ancienne clé existe, migrer
if "selected_table" in st.session_state and "selected_tables" not in st.session_state:
    st.session_state["selected_tables"] = [st.session_state.pop("selected_table")]

# ══════════════════════════════════════════════════════════════════════════════
# BINARY TREE + SQL
# ══════════════════════════════════════════════════════════════════════════════
def build_tree(conditions):
    if not conditions: return None
    tree = {"type":"leaf","idx":0}
    for i in range(1, len(conditions)):
        tree = {"type":"branch","op":conditions[i]["join_op"],
                "left":tree,"right":{"type":"leaf","idx":i}}
    return tree

def _col_ref(c: dict, multi: bool) -> str:
    """Retourne 'table.colonne' en mode multi-table, sinon 'colonne' seul."""
    tbl = c.get("table", "")
    return f"{tbl}.{c['column']}" if (multi and tbl) else c["column"]

def _sql_from_tree(node, conditions, params, display, multi=False):
    if node["type"] == "leaf":
        c   = conditions[node["idx"]]
        col = _col_ref(c, multi)
        if c.get("is_bulk"):
            sym, fn = OPERATORS[c["operator"]]
            if display:
                clauses = [f"{col} {sym} '{fn(v)}'" for v in c["values"]]
            else:
                clauses = []
                for v in c["values"]:
                    clauses.append(f"{col} {sym} ?")
                    params.append(fn(v))
            return "(" + " OR ".join(clauses) + ")"
        sym, fn = OPERATORS[c["operator"]]
        val = fn(c["value"])
        if display: return f"{col} {sym} '{val}'"
        params.append(val); return f"{col} {sym} ?"
    sql_op = "AND" if node["op"] == "ET" else "OR"
    L = _sql_from_tree(node["left"],  conditions, params, display, multi)
    R = _sql_from_tree(node["right"], conditions, params, display, multi)
    return f"({L} {sql_op} {R})"

def build_where(conditions, display=False):
    if not conditions: return "1=1", []
    multi  = len({c.get("table","") for c in conditions if c.get("table")}) > 1
    multi |= any(c.get("table") for c in conditions)   # dès qu'une condition a un champ table
    params = []
    where  = _sql_from_tree(build_tree(conditions), conditions, params, display, multi=multi)
    return where, params

def _from_clause(tables: list) -> str:
    rels     = fk_rels()
    from_sql, _ = build_join_sql(tables, rels)
    return from_sql

def build_query(tables: list, conditions: list):
    where, params = build_where(conditions)
    from_sql = _from_clause(tables)
    if where == "1=1":
        return f"SELECT *\nFROM {from_sql}", params
    return f"SELECT *\nFROM {from_sql}\nWHERE {where}", params

def build_query_display(tables: list, conditions: list) -> str:
    where, _ = build_where(conditions, display=True)
    from_sql  = _from_clause(tables)
    if where == "1=1":
        return f"SELECT *\nFROM {from_sql}"
    return f"SELECT *\nFROM {from_sql}\nWHERE {where}"


# ══════════════════════════════════════════════════════════════════════════════
# TREE RENDERER
# ══════════════════════════════════════════════════════════════════════════════
BRANCH_STYLES = {
    "ET": {"color":"#fca5a5","bg":"#450a0a","border":"#991b1b"},
    "OU": {"color":"#93c5fd","bg":"#172554","border":"#1d4ed8"},
}
NEUTRAL = "#475569"

OP_NATURAL = {
    "Contient":"contient","Commence par":"commence par","Finit par":"finit par",
    "Égal à":"est","Différent de":"n'est pas","Supérieur à":">","Inférieur à":"<",
}

def _date_label(val):
    p = val.split("-")
    try:
        if len(p)==1: return f"année {p[0]}"
        if len(p)==2: return f"{MONTHS_FR[int(p[1])]} {p[0]}"
        return f"{int(p[2])} {MONTHS_FR[int(p[1])]} {p[0]}"
    except Exception: return val

TABLE_BADGE_COLORS = {
    "clients": ("#1e3a5f", "#60a5fa"),
    "voyages": ("#1a3a2a", "#4ade80"),
}

def _leaf_html(conditions, idx):
    c = conditions[idx]
    display_col = c.get("label") or c["column"]
    tbl = c.get("table", "")
    badge = ""
    if tbl:
        bg, fg = TABLE_BADGE_COLORS.get(tbl, ("#1e293b", "#94a3b8"))
        badge = (f"<span style='background:{bg};color:{fg};font-size:.65rem;"
                 f"padding:1px 6px;border-radius:4px;margin-right:5px;"
                 f"font-family:JetBrains Mono,monospace;vertical-align:middle;'>{tbl}</span>")
    if c.get("is_date"):
        return (f"<span class='t-leaf'>{badge}<b style='color:#a5f3fc;'>{display_col}</b> "
                f"<span style='color:#fbbf24;'>en</span> "
                f"<span style='color:#86efac;'>{_date_label(c['value'])}</span></span>")
    if c.get("is_bulk"):
        values  = c["values"]
        n       = len(values)
        op_str  = OP_NATURAL.get(c["operator"], c["operator"])
        preview = " · ".join(f"«{v}»" for v in values[:3])
        suffix  = f" <span style='color:#64748b;font-size:.75rem;'>+{n-3} autres</span>" if n > 3 else ""
        return (f"<span class='t-leaf'>{badge}<b style='color:#a5f3fc;'>{display_col}</b> "
                f"<span style='color:#fbbf24;'>{op_str}</span> "
                f"<span style='color:#86efac;'>[{preview}{suffix}]</span></span>")
    op_str = OP_NATURAL.get(c["operator"], c["operator"])
    return (f"<span class='t-leaf'>{badge}<b style='color:#a5f3fc;'>{display_col}</b> "
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
    """Petit bouton ✏️ discret positionné sur la feuille."""
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
    """Formulaire d'édition inline affiché à la place de la feuille."""
    cond    = conditions[idx]
    is_date = cond.get("is_date", False)
    is_bulk = cond.get("is_bulk", False)

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
        parts     = cond["value"].split("-")
        cur_year  = int(parts[0]) if len(parts) >= 1 else 2023
        cur_month = int(parts[1]) if len(parts) >= 2 else 0
        cur_day   = int(parts[2]) if len(parts) >= 3 else 0
        e1, e2, e3, e4, e5 = st.columns([1.5, 1, 1, 0.5, 0.5])
        e1.number_input("Année", 1900, 2100, cur_year,  key=f"ey_{idx}", label_visibility="collapsed")
        e2.number_input("Mois",  0, 12, cur_month,      key=f"em_{idx}", label_visibility="collapsed")
        e3.number_input("Jour",  0, 31, cur_day,        key=f"ed_{idx}", label_visibility="collapsed")
        with e4:
            if st.button("✓", key=f"eok_{idx}", help="Valider"):
                st.session_state.conditions[idx]["value"] = build_date_value(
                    int(st.session_state.get(f"ey_{idx}", cur_year)),
                    int(st.session_state.get(f"em_{idx}", cur_month)),
                    int(st.session_state.get(f"ed_{idx}", cur_day)),
                )
                st.session_state.editing.pop(idx, None)
                st.rerun()
        with e5:
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

    if node["type"] == "leaf":
        idx        = node["idx"]
        is_editing = st.session_state.editing.get(idx) == "leaf"

        if is_editing:
            # Formulaire d'édition — même indentation que la feuille
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
            # Feuille normale + petit bouton ✏️ discret
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
    else:
        op, right_idx = node["op"], node["right"]["idx"]
        if ph:
            w = max(prefix_len * 0.135, 0.35)
            ca, cb = st.columns([w, max(9-w, 1)])
            ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>", unsafe_allow_html=True)
            with cb: _branch_button(op, right_idx)
        else:
            _branch_button(op, right_idx)
        new_pfx = (prefix_parts if is_root else
                   prefix_parts + [("│   ", connector_color)] if not is_last else
                   prefix_parts + [("    ", connector_color)])
        _render_node(node["left"],  conditions, new_pfx, is_last=False, parent_op=op)
        _render_node(node["right"], conditions, new_pfx, is_last=True,  parent_op=op)

def _branch_button(op, right_idx):
    s = BRANCH_STYLES[op]; bg, color, border = s["bg"], s["color"], s["border"]
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

def render_tree(conditions, tables):
    tables_list  = tables if isinstance(tables, list) else [tables]
    tables_label = " ⋈ ".join(tables_list)
    st.markdown(
        f"<div class='tree-wrap'>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>Requête</span>"
        f"<div style='margin:6px 0 12px;'><span class='t-root'>SELECT * FROM {tables_label}</span></div>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>WHERE</span></div>",
        unsafe_allow_html=True)
    tree = build_tree(conditions)
    if tree is None:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>Aucune condition.</p>",
                    unsafe_allow_html=True); return
    _render_node(tree, conditions, prefix_parts=[], is_last=True, is_root=True, parent_op=None)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL INLINE (remplace @st.dialog — fiable dans toutes les versions Streamlit)
# ══════════════════════════════════════════════════════════════════════════════
def render_row_panel(df: "pd.DataFrame", row_idx: int) -> None:
    """Panel affiché sous le tableau quand une ligne est sélectionnée."""
    row     = df.iloc[row_idx]
    cols    = list(df.columns)

    # Colonne et valeur actives (persistées via session_state)
    col_key = f"panel_col_{row_idx}"
    if col_key not in st.session_state:
        st.session_state[col_key] = cols[0]

    st.markdown(
        "<div style='background:#13151d;border:1px solid #6366f1;"
        "border-radius:12px;padding:16px 20px;margin-top:12px;'>",
        unsafe_allow_html=True,
    )

    # ── En-tête ────────────────────────────────────────────────────────────────
    h1, h2 = st.columns([8, 1])
    with h1:
        st.markdown(
            f"<span style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
            f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Ligne {row_idx} sélectionnée</span>",
            unsafe_allow_html=True,
        )
    with h2:
        if st.button("✕", key="panel_close", help="Fermer"):
            st.session_state["_selected_row_idx"] = None
            st.rerun()

    # ── Valeurs de la ligne (badges cliquables) ────────────────────────────────
    st.markdown("<div style='display:flex;flex-wrap:wrap;gap:6px;margin:10px 0;'>",
                unsafe_allow_html=True)
    badge_html = ""
    for c in cols:
        val = row[c]
        is_active = (c == st.session_state.get(col_key))
        bg    = "#1e3a5f" if is_active else "#1e293b"
        border= "#6366f1" if is_active else "#334155"
        color = "#a5f3fc" if is_active else "#94a3b8"
        badge_html += (
            f"<span style='background:{bg};border:1px solid {border};"
            f"border-radius:6px;padding:3px 10px;font-size:.75rem;"
            f"font-family:JetBrains Mono,monospace;cursor:pointer;'>"
            f"<span style='color:{color};font-weight:600;'>{c}</span>"
            f"<span style='color:#64748b;'> : </span>"
            f"<span style='color:#e2e8f0;'>{val}</span></span>"
        )
    st.markdown(badge_html + "</div>", unsafe_allow_html=True)

    # ── Sélecteurs ────────────────────────────────────────────────────────────
    pc1, pc2, pc3 = st.columns([2, 2, 3])
    with pc1:
        # Colonne : label avec valeur
        col_options = [f"{c} : {row[c]}" for c in cols]
        cur_label   = f"{st.session_state[col_key]} : {row[st.session_state[col_key]]}"
        sel_label   = st.selectbox(
            "Colonne", col_options,
            index=col_options.index(cur_label) if cur_label in col_options else 0,
            key=f"panel_col_sel_{row_idx}",
            label_visibility="collapsed",
        )
        sel_col = sel_label.split(" : ")[0]
        st.session_state[col_key] = sel_col

    with pc2:
        sel_op = st.selectbox("Opérateur", OP_LABELS,
                              key=f"panel_op_{row_idx}",
                              label_visibility="collapsed")

    with pc3:
        tables_with_col = [t for t, tc in TABLES.items() if sel_col in tc]
        sel_table = st.selectbox(
            "Table",
            tables_with_col,
            index=tables_with_col.index(st.session_state.selected_table)
                  if st.session_state.selected_table in tables_with_col else 0,
            key=f"panel_tbl_{row_idx}",
            label_visibility="collapsed",
        )

    # ── SQL preview ────────────────────────────────────────────────────────────
    sel_val = str(row[sel_col])
    sym, fn = OPERATORS[sel_op]
    tv      = fn(sel_val)
    st.markdown(
        f"<div style='background:#0a0c12;border-left:3px solid #6366f1;"
        f"border-radius:6px;padding:7px 12px;font-family:JetBrains Mono,monospace;"
        f"font-size:.78rem;color:#a5f3fc;margin:8px 0;'>"
        f"SELECT * FROM <b>{sel_table}</b> WHERE <b>{sel_col}</b>"
        f" <span style='color:#fbbf24'>{sym}</span>"
        f" <span style='color:#86efac'>'{tv}'</span></div>",
        unsafe_allow_html=True,
    )

    # ── Boutons ────────────────────────────────────────────────────────────────
    pb1, pb2, pb3 = st.columns(3)

    with pb1:
        if st.button("▶ Lancer la requête", key="panel_run",
                     width="stretch", type="primary"):
            conn = get_connection()
            q    = f"SELECT * FROM {sel_table} WHERE {sel_col} {sym} ?"
            try:
                st.session_state.results         = pd.read_sql_query(q, conn, params=[tv])
                st.session_state.selected_tables = [sel_table]
                cond_new = {"table": sel_table, "column": sel_col, "operator": sel_op,
                            "value": sel_val, "join_op": "ET", "is_date": False, "is_bulk": False}
                st.session_state.conditions      = [cond_new]
                where, params = build_where(st.session_state.conditions)
                st.session_state.last_where   = where
                st.session_state.last_params  = params
                st.session_state.enrich_opts  = enrich_options([sel_table], where, params)
                st.session_state["_selected_row_idx"] = None
            except Exception as e:
                st.error(f"Erreur SQL : {e}")
            st.rerun()

    count_key = f"panel_cnt_{sel_table}__{sel_col}__{sel_op}__{sel_val}"
    with pb2:
        if count_key in st.session_state:
            cnt_val = st.session_state[count_key]
            st.markdown(
                f"<div style='background:#14532d;border:1.5px solid #16a34a;"
                f"border-radius:8px;padding:8px;text-align:center;'>"
                f"<div style='color:#4ade80;font-size:1.4rem;font-weight:800;"
                f"font-family:JetBrains Mono,monospace;'>{cnt_val}</div>"
                f"<div style='color:#86efac;font-size:.68rem;'>ligne(s)</div></div>",
                unsafe_allow_html=True,
            )
        else:
            if st.button("🔢 Compter", key="panel_count", width="stretch"):
                conn = get_connection()
                q    = f"SELECT COUNT(*) AS total FROM {sel_table} WHERE {sel_col} {sym} ?"
                try:
                    r = pd.read_sql_query(q, conn, params=[tv])
                    st.session_state[count_key] = int(r["total"].iloc[0])
                except Exception as e:
                    st.error(f"Erreur : {e}")
                st.rerun()

    with pb3:
        join = "ET"
        if st.session_state.conditions:
            join = st.radio("Lier", ["ET","OU"], horizontal=True,
                            key=f"panel_join_{row_idx}", label_visibility="collapsed")
        if st.button("➕ Ajouter à l'arbre", key="panel_add", width="stretch"):
            st.session_state.conditions.append({
                "column": sel_col, "operator": sel_op,
                "value": sel_val, "join_op": join,
                "is_date": False, "is_bulk": False,
            })
            st.session_state["_selected_row_idx"] = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# 🔍 SQL Query Builder")
st.markdown("<p style='color:#6b7280;margin-top:-14px;margin-bottom:20px;'>"
            "Construisez vos requêtes SQL visuellement, sans écrire une ligne de code.</p>",
            unsafe_allow_html=True)

# ── Table selector — multi-sélection ──────────────────────────────────────────
st.markdown("<span style='color:#94a3b8;font-size:.78rem;text-transform:uppercase;"
            "letter-spacing:1px;font-family:JetBrains Mono,monospace;'>"
            "Tables sources <span style='font-weight:400;font-size:.72rem;'>"
            "(cliquez pour sélectionner / désélectionner)</span></span>",
            unsafe_allow_html=True)

sel_tables = st.session_state.selected_tables  # list
t_cols = st.columns(len(TABLES))
for i, tname in enumerate(TABLES):
    is_active = tname in sel_tables
    bg_color  = TABLE_BADGE_COLORS.get(tname, ("#1e293b","#94a3b8"))
    bg  = f"linear-gradient(135deg,{bg_color[1]}22,{bg_color[1]}44)" if is_active else "#1a1d27"
    col = bg_color[1] if is_active else "#94a3b8"
    brd = f"1px solid {bg_color[1]}" if is_active else "1px solid #2a2d3e"
    m   = f"tpill-{tname}"
    t_cols[i].markdown(
        f'<div id="{m}"></div><style>'
        f"div.element-container:has(#{m}) + div.element-container button{{"
        f"background:{bg}!important;color:{col}!important;border:{brd}!important;"
        f"border-radius:20px!important;width:100%;font-size:.85rem!important;}}</style>",
        unsafe_allow_html=True)
    if t_cols[i].button(
        ("☑ " if is_active else "☐ ") + tname,
        key=f"tpill_{tname}", width="stretch"
    ):
        new_sel = list(sel_tables)
        if tname in new_sel:
            if len(new_sel) > 1:   # au moins 1 table toujours active
                new_sel.remove(tname)
                # Supprimer les conditions de cette table
                st.session_state.conditions = [
                    c for c in st.session_state.conditions if c.get("table") != tname
                ]
        else:
            new_sel.append(tname)
        st.session_state.selected_tables = new_sel
        st.session_state.results         = None
        st.session_state.enrich_count    = None
        st.rerun()

# Afficher les FK détectées quand multi-tables
if len(sel_tables) > 1:
    rels = fk_rels()
    _, join_infos = build_join_sql(sel_tables, rels)
    for info in join_infos:
        if info:
            st.markdown(
                f"<span style='color:#4ade80;font-size:.72rem;"
                f"font-family:JetBrains Mono,monospace;'>🔗 FK détectée : {info}</span>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                "<span style='color:#f87171;font-size:.72rem;'>⚠️ Aucune FK trouvée — CROSS JOIN</span>",
                unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

# ── Add condition ──────────────────────────────────────────────────────────────
hdr_l, hdr_r = st.columns([5, 3])
with hdr_l:
    st.markdown("### ➕ Ajouter une condition")
with hdr_r:
    st.markdown("<div style='padding-top:18px;'>", unsafe_allow_html=True)
    expert_mode = st.toggle(
        "🔧 Mode expert", key="expert_mode",
        help="**Mode simplifié** : colonnes essentielles avec libellés clairs\n\n"
             "**Mode expert** : toutes les colonnes techniques disponibles",
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ── Sélection de la table cible de la condition ───────────────────────────────
if len(sel_tables) > 1:
    form_table = st.selectbox(
        "Table de la condition",
        sel_tables,
        key="new_cond_table",
        help="Sur quelle table porte cette condition ?",
    )
else:
    form_table = sel_tables[0]

current_cols = TABLES[form_table]

# ── Résoudre les colonnes selon le mode ───────────────────────────────────────
if expert_mode:
    col_options   = current_cols
    col_key       = f"new_col_expert_{form_table}"
    new_col_label = None
else:
    simp        = SIMPLIFIED_COLS.get(form_table, [(c, c) for c in current_cols])
    col_options = [label for _, label in simp]
    col_map     = {label: col for col, label in simp}
    col_key     = f"new_col_simple_{form_table}"

# ── Ligne de formulaire ────────────────────────────────────────────────────────
fa, fb, fc, fd = st.columns([2, 2, 3, 1])
with fa:
    selected = st.selectbox("Colonne", col_options, key=col_key,
                             label_visibility="collapsed")
    if expert_mode:
        new_col       = selected
        new_col_label = selected
    else:
        new_col       = col_map.get(selected, selected)
        new_col_label = selected

with fb:
    is_date = is_date_col(new_col)
    if is_date:
        st.markdown("<span style='color:#a78bfa;font-size:.78rem;'>📅 Colonne date</span>",
                    unsafe_allow_html=True)
    else:
        new_op = st.selectbox("Opérateur", OP_LABELS, key="new_op",
                               label_visibility="collapsed")
with fc:
    if is_date:
        d1, d2, d3 = st.columns(3)
        new_year  = d1.number_input("Année *", 1900, 2100, 2023, 1, key="new_year")
        new_month = d2.number_input("Mois",    0,    12,   0,    1, key="new_month",
                                    help="0 = non précisé")
        new_day   = d3.number_input("Jour",    0,    31,   0,    1, key="new_day",
                                    help="0 = non précisé")
    else:
        st.text_area("Valeur(s)", key="new_val",
                     placeholder="Une valeur, ou plusieurs séparées par des virgules / sauts de ligne",
                     height=80, label_visibility="collapsed")
with fd:
    new_join = (st.radio("Lier", ["ET","OU"], horizontal=False, key="new_join",
                          label_visibility="collapsed")
                if st.session_state.conditions else "ET")

btn_a, btn_b = st.columns([3, 1])
with btn_a:
    if st.button("➕ Ajouter la condition", width="stretch"):
        base = {"table": form_table, "column": new_col, "label": new_col_label,
                "join_op": new_join, "is_date": is_date, "is_bulk": False}
        if is_date:
            st.session_state.conditions.append({
                **base, "operator": "Commence par",
                "value": build_date_value(int(new_year), int(new_month), int(new_day)),
            })
            st.rerun()
        else:
            raw    = st.session_state.get("new_val", "")
            values = [v.strip() for v in re.split(r"[,\n]", raw) if v.strip()]
            if not values:
                st.warning("Veuillez entrer au moins une valeur.")
            elif len(values) == 1:
                st.session_state.conditions.append({**base, "operator": new_op, "value": values[0]})
                st.rerun()
            else:
                st.session_state.conditions.append({
                    **base, "operator": new_op, "is_bulk": True,
                    "value": ", ".join(values), "values": values,
                })
                st.rerun()
with btn_b:
    if st.button("🗑 Effacer", width="stretch"):
        st.session_state.conditions   = []
        st.session_state.results      = None
        st.session_state.enrich_count = None
        st.rerun()

st.markdown("---")

# ── Tree + SQL expander ────────────────────────────────────────────────────────
col_tree, col_sql = st.columns([3, 2], gap="large")
with col_tree:
    st.markdown("### 🌳 Arbre de décision")
    st.caption("Cliquez sur un nœud ET / OU pour le basculer.")
    render_tree(st.session_state.conditions, sel_tables)
with col_sql:
    with st.expander("🧾 Voir la requête SQL générée", expanded=False):
        st.markdown(f"<div class='sql-display'>"
                    f"{build_query_display(sel_tables, st.session_state.conditions)}"
                    f"</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    if st.button("▶ Exécuter la requête", width="stretch", type="primary"):
        conn = get_connection()
        q, params = build_query(sel_tables, st.session_state.conditions)
        try:
            st.session_state.results = pd.read_sql_query(q, conn, params=params)
            where, wparams = build_where(st.session_state.conditions)
            st.session_state.last_where  = where
            st.session_state.last_params = wparams
            # Enrichissement : seulement pour requêtes mono-table
            if len(sel_tables) == 1:
                st.session_state.enrich_opts = enrich_options(
                    sel_tables, where, wparams)
            else:
                st.session_state.enrich_opts = []
            st.session_state.enrich_count = None
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.results is not None:
    df  = st.session_state.results

    st.markdown("---")
    st.markdown("### 📊 Résultats")

    m1, m2, m3 = st.columns(3)
    m1.metric("Lignes", len(df))
    m2.metric("Colonnes", len(df.columns))
    m3.metric("Conditions", len(st.session_state.conditions))

    if len(df) == 0:
        st.info("Aucun résultat ne correspond à vos critères.")
    else:
        # ── column presence flags ──────────────────────────────────────────────
        has_nom        = "nom"         in df.columns
        has_prenom     = "prenom"      in df.columns
        has_dest       = "destination" in df.columns
        has_depart     = "date_depart" in df.columns
        has_budget     = "budget"      in df.columns
        has_note       = "note"        in df.columns
        has_continent  = "continent"   in df.columns
        has_type       = "type_voyage" in df.columns
        has_duree      = "duree_jours" in df.columns
        has_statut_v   = "statut_voyage" in df.columns
        has_client_nom = "client_nom"  in df.columns
        has_ville      = "ville"       in df.columns
        has_client_id  = "client_id"   in df.columns

        # ── continent color palette ────────────────────────────────────────────
        CONT_COLORS = {
            "Asie":"#f59e0b","Europe":"#3b82f6","Amérique":"#10b981",
            "Afrique":"#ef4444","Océanie":"#8b5cf6",
        }
        TYPE_COLORS = {
            "Tourisme":"#3b82f6","Affaires":"#8b5cf6","Détente":"#10b981",
            "Lune de miel":"#f472b6","Safari":"#f59e0b","Aventure":"#ef4444",
            "Luxe":"#fbbf24","City Break":"#06b6d4","Culturel":"#a78bfa",
            "Plage":"#22d3ee","Romantique":"#fb7185",
        }

        # ── Animation clignotante — uniquement les onglets avec nouvelles données ──
        _hl_until   = st.session_state.get("_enrich_hl_until", 0)
        _blink_tabs = st.session_state.get("_blink_tabs", set())
        _do_blink   = time.time() < _hl_until and bool(_blink_tabs)
        if _do_blink:
            # Construire le sélecteur CSS uniquement pour les nth-child ciblés
            selectors = ", ".join(
                f"div[data-testid='stTabsTabList'] button[role='tab']:nth-child({n})"
                for n in sorted(_blink_tabs)
            )
            st.markdown(f"""
<style>
@keyframes tab-pulse {{
    0%   {{ color: inherit; text-shadow: none; }}
    40%  {{ color: #4ade80 !important;
           text-shadow: 0 0 8px #4ade80, 0 0 16px #16a34a; }}
    100% {{ color: inherit; text-shadow: none; }}
}}
{selectors} {{
    animation: tab-pulse 0.9s ease-in-out infinite;
}}
div[data-testid="stTabsTabList"] button[role="tab"][aria-selected="true"] {{
    animation: none !important;
    color: inherit !important;
}}
</style>
""", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📋 Grille", "👤 Fiches", "🗓 Timeline", "📈 Statistiques"]
        )

        # ══════════════════════════════════════════════════════════════════════
        # TAB 1 — Grille
        # ══════════════════════════════════════════════════════════════════════
        with tab1:
            st.caption("💡 Cliquez sur une ligne pour explorer ses valeurs et créer un filtre.")
            event = st.dataframe(df, width="stretch", hide_index=True,
                                 on_select="rerun", selection_mode="single-row",
                                 key="result_df")
            sel    = event.selection if hasattr(event, "selection") else {}
            rows_s = sel.get("rows", [])
            if rows_s:
                st.session_state["_selected_row_idx"] = int(rows_s[0])
            elif not rows_s and st.session_state.get("_selected_row_idx") is not None:
                # L'utilisateur a désélectionné la ligne
                st.session_state["_selected_row_idx"] = None
            st.download_button("⬇ Télécharger CSV",
                df.to_csv(index=False).encode("utf-8"),
                f"resultats_{_.join(sel_tables)}.csv", "text/csv")

        # ── Panel de filtrage — affiché sous les tabs (hors contexte tab) ─────
        row_idx_panel = st.session_state.get("_selected_row_idx")
        if row_idx_panel is not None and row_idx_panel < len(df):
            render_row_panel(df, row_idx_panel)

        # ══════════════════════════════════════════════════════════════════════
        # TAB 2 — Fiches
        # ══════════════════════════════════════════════════════════════════════
        with tab2:
            # ── Case A : données enrichies (clients + voyages) ─────────────
            if has_nom and has_prenom and has_dest:
                key_id = "id"
                client_groups = df.groupby(key_id, sort=False)
                for client_id, group in client_groups:
                    row0 = group.iloc[0]
                    initials = (str(row0.get("prenom","?"))[:1] +
                                str(row0.get("nom","?"))[:1]).upper()
                    ville_txt   = row0.get("ville","")
                    statut_txt  = row0.get("statut","")
                    stat_color  = "#4ade80" if statut_txt == "actif" else "#f87171"
                    n_voyages   = len(group)
                    budget_tot  = group["budget"].sum() if has_budget else 0

                    card_html = (
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-radius:12px;padding:16px 20px;margin-bottom:16px;'>"
                        f"<div style='display:flex;align-items:center;gap:14px;margin-bottom:12px;'>"
                        f"<div style='width:44px;height:44px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;font-size:1rem;color:white;flex-shrink:0;'>{initials}</div>"
                        f"<div>"
                        f"<div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>"
                        f"{row0.get('prenom','')} {row0.get('nom','')}</div>"
                        f"<div style='color:#64748b;font-size:.82rem;'>"
                        f"{ville_txt} &nbsp;·&nbsp; "
                        f"<span style='color:{stat_color};'>{statut_txt}</span></div>"
                        f"</div>"
                        f"<div style='margin-left:auto;text-align:right;'>"
                        f"<div style='color:#a78bfa;font-size:1.1rem;font-weight:700;"
                        f"font-family:JetBrains Mono,monospace;'>{n_voyages}</div>"
                        f"<div style='color:#64748b;font-size:.72rem;'>voyage{'s' if n_voyages>1 else ''}</div>"
                        f"</div></div>"
                    )
                    # voyage rows
                    for _, vrow in group.iterrows():
                        dest     = vrow.get("destination","")
                        cont     = vrow.get("continent","")
                        cont_col = CONT_COLORS.get(cont,"#6b7280")
                        dep      = str(vrow.get("date_depart",""))[:10]
                        ret      = str(vrow.get("date_retour",""))[:10]
                        bgt      = vrow.get("budget",0)
                        note_v   = vrow.get("note",None)
                        stars    = ("⭐" * int(note_v)) if note_v and not pd.isna(note_v) else "—"
                        tv       = vrow.get("type_voyage","")
                        tv_col   = TYPE_COLORS.get(tv,"#6b7280")
                        card_html += (
                            f"<div style='display:flex;align-items:center;gap:10px;"
                            f"padding:7px 0;border-top:1px solid #1e2130;'>"
                            f"<div style='width:3px;height:32px;border-radius:2px;"
                            f"background:{cont_col};flex-shrink:0;'></div>"
                            f"<div style='flex:1;'>"
                            f"<span style='color:#e8eaf0;font-weight:600;font-size:.85rem;'>{dest}</span>"
                            f"<span style='color:#475569;font-size:.75rem;margin-left:8px;'>{dep} → {ret}</span>"
                            f"</div>"
                            f"<span style='background:{tv_col}22;color:{tv_col};"
                            f"font-size:.7rem;padding:2px 8px;border-radius:10px;'>{tv}</span>"
                            f"<span style='color:#fbbf24;font-size:.78rem;font-family:JetBrains Mono,monospace;"
                            f"margin-left:4px;'>{int(bgt):,}€</span>"
                            f"<span style='font-size:.75rem;margin-left:6px;'>{stars}</span>"
                            f"</div>"
                        )
                    card_html += "</div>"
                    st.markdown(card_html, unsafe_allow_html=True)

            # ── Case B : clients seuls ─────────────────────────────────────
            elif has_nom and has_prenom and not has_dest:
                cols_grid = st.columns(2)
                for i, (_, row) in enumerate(df.iterrows()):
                    initials   = (str(row.get("prenom","?"))[:1] +
                                  str(row.get("nom","?"))[:1]).upper()
                    statut_txt = str(row.get("statut",""))
                    stat_color = "#4ade80" if statut_txt == "actif" else "#f87171"
                    date_ins   = str(row.get("date_inscription",""))[:10]
                    ville_txt  = row.get("ville","")
                    card_html  = (
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-radius:12px;padding:16px 18px;margin-bottom:12px;'>"
                        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>"
                        f"<div style='width:40px;height:40px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;color:white;'>{initials}</div>"
                        f"<div><div style='font-weight:700;color:#e8eaf0;'>"
                        f"{row.get('prenom','')} {row.get('nom','')}</div>"
                        f"<div style='font-size:.78rem;color:#64748b;'>{ville_txt} · "
                        f"<span style='color:{stat_color};'>{statut_txt}</span></div></div>"
                        f"</div>"
                        f"<div style='font-size:.78rem;color:#64748b;line-height:1.8;'>"
                        f"📧 {row.get('email','')}<br>"
                        f"📞 {row.get('telephone','')}<br>"
                        f"📅 Membre depuis {date_ins}"
                        f"</div></div>"
                    )
                    cols_grid[i % 2].markdown(card_html, unsafe_allow_html=True)

            # ── Case C : voyages seuls (ou voyages enrichis avec client_nom) ─
            elif has_dest:
                cols_grid = st.columns(2)
                for i, (_, row) in enumerate(df.iterrows()):
                    dest     = row.get("destination","")
                    pays     = row.get("pays_destination","")
                    cont     = row.get("continent","")
                    cont_col = CONT_COLORS.get(cont,"#6b7280")
                    dep      = str(row.get("date_depart",""))[:10]
                    ret      = str(row.get("date_retour",""))[:10]
                    duree    = row.get("duree_jours","")
                    bgt      = row.get("budget",0)
                    hotel    = row.get("hotel","")
                    tv       = row.get("type_voyage","")
                    tv_col   = TYPE_COLORS.get(tv,"#6b7280")
                    note_v   = row.get("note",None)
                    stars    = ("⭐" * int(note_v)) if note_v and not pd.isna(note_v) else "—"
                    stat_v   = row.get("statut","")
                    # client name if enriched
                    cnom     = ""
                    if has_client_nom:
                        cnom = f"{row.get('client_prenom','')} {row.get('client_nom','')}"
                    elif has_client_id:
                        cnom = f"Client #{int(row.get('client_id',0))}"

                    card_html = (
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-top:3px solid {cont_col};"
                        f"border-radius:12px;padding:16px 18px;margin-bottom:12px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:start;'>"
                        f"<div>"
                        f"<div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>{dest}</div>"
                        f"<div style='font-size:.78rem;color:#64748b;'>{pays} · "
                        f"<span style='color:{cont_col};'>{cont}</span></div>"
                        f"</div>"
                        f"<span style='background:{tv_col}22;color:{tv_col};"
                        f"font-size:.7rem;padding:3px 10px;border-radius:10px;white-space:nowrap;'>{tv}</span>"
                        f"</div>"
                        f"<div style='margin:10px 0;font-size:.8rem;color:#94a3b8;'>"
                        f"📅 {dep} → {ret}"
                        f"{'&nbsp;&nbsp;·&nbsp;&nbsp;🕒 ' + str(duree) + 'j' if duree else ''}"
                        f"{'&nbsp;&nbsp;·&nbsp;&nbsp;' + cnom if cnom else ''}"
                        f"</div>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        f"<span style='color:#64748b;font-size:.78rem;'>🏨 {hotel}</span>"
                        f"<div style='text-align:right;'>"
                        f"<div style='color:#4ade80;font-weight:700;font-family:JetBrains Mono,monospace;'>"
                        f"{int(bgt):,}€</div>"
                        f"<div style='font-size:.75rem;'>{stars}</div>"
                        f"</div></div>"
                        f"</div>"
                    )
                    cols_grid[i % 2].markdown(card_html, unsafe_allow_html=True)
            else:
                st.info("Aucune vue fiche disponible pour ces colonnes.")

        # ══════════════════════════════════════════════════════════════════════
        # TAB 3 — Timeline
        # ══════════════════════════════════════════════════════════════════════
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
                    d_min = df_tl["date_depart"].min()
                    d_max = (df_tl["date_retour"].max()
                             if "date_retour" in df_tl.columns
                             else df_tl["date_depart"].max())
                    span  = max((d_max - d_min).days, 1)

                    # group by year-month for section headers
                    current_ym = None
                    for _, row in df_tl.iterrows():
                        ym = row["date_depart"].strftime("%B %Y").capitalize()
                        if ym != current_ym:
                            current_ym = ym
                            st.markdown(
                                f"<div style='color:#6366f1;font-size:.75rem;font-weight:700;"
                                f"text-transform:uppercase;letter-spacing:1px;"
                                f"font-family:JetBrains Mono,monospace;"
                                f"margin:18px 0 6px;'>{ym}</div>",
                                unsafe_allow_html=True)

                        dep      = row["date_depart"]
                        ret      = row.get("date_retour") if has_depart and "date_retour" in df_tl.columns else dep
                        if pd.isna(ret): ret = dep
                        duree    = max((ret - dep).days, 1)
                        left_pct = round((dep - d_min).days / span * 100, 1)
                        width_pct= max(round(duree / span * 100, 1), 1.5)

                        dest     = row.get("destination","")
                        cont     = row.get("continent","")
                        cont_col = CONT_COLORS.get(cont,"#6b7280")
                        tv       = row.get("type_voyage","")
                        tv_col   = TYPE_COLORS.get(tv,"#6b7280")
                        bgt      = row.get("budget","")
                        note_v   = row.get("note",None)
                        stars    = "⭐" * int(note_v) if note_v and not pd.isna(note_v) else ""
                        cnom     = ""
                        if has_client_nom:
                            cnom = f"{row.get('client_prenom','')} {row.get('client_nom','')}".strip()
                        elif has_prenom and has_nom:
                            cnom = f"{row.get('prenom','')} {row.get('nom','')}".strip()

                        dep_str = dep.strftime("%d %b %Y")
                        ret_str = ret.strftime("%d %b %Y")

                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:12px 16px;margin-bottom:8px;'>"
                            # label row
                            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>"
                            f"<span style='width:8px;height:8px;border-radius:50%;"
                            f"background:{cont_col};display:inline-block;flex-shrink:0;'></span>"
                            f"<span style='font-weight:600;color:#e8eaf0;font-size:.9rem;'>{dest}</span>"
                            f"{'<span style=\"color:#94a3b8;font-size:.78rem;\"> · ' + cnom + '</span>' if cnom else ''}"
                            f"<span style='margin-left:auto;color:#64748b;font-size:.75rem;'>"
                            f"{dep_str} → {ret_str} · {duree}j</span>"
                            f"</div>"
                            # bar
                            f"<div style='position:relative;height:10px;background:#1e293b;"
                            f"border-radius:5px;overflow:hidden;'>"
                            f"<div style='position:absolute;left:{left_pct}%;width:{width_pct}%;"
                            f"height:100%;background:linear-gradient(90deg,{cont_col},{tv_col});"
                            f"border-radius:5px;'></div></div>"
                            # chips
                            f"<div style='margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;'>"
                            f"<span style='background:{tv_col}22;color:{tv_col};font-size:.7rem;"
                            f"padding:2px 8px;border-radius:10px;'>{tv}</span>"
                            f"{'<span style=\"font-size:.75rem;color:#4ade80;font-family:JetBrains Mono,monospace;\">' + str(int(bgt)) + '€</span>' if bgt else ''}"
                            f"<span style='font-size:.72rem;'>{stars}</span>"
                            f"</div></div>",
                            unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════════
        # TAB 4 — Statistiques
        # ══════════════════════════════════════════════════════════════════════
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

            if has_dest:  # voyage stats
                sa, sb = st.columns(2)
                with sa:
                    # Key metrics
                    n_total = len(df)
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
                            f"</div>",
                            unsafe_allow_html=True)
                    if has_duree:
                        d_moy = df["duree_jours"].mean()
                        d_max = df["duree_jours"].max()
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                            f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
                            f"letter-spacing:1px;margin-bottom:6px;'>Durée moyenne</div>"
                            f"<div style='color:#60a5fa;font-size:1.6rem;font-weight:800;"
                            f"font-family:JetBrains Mono,monospace;'>{d_moy:.1f}j</div>"
                            f"<div style='color:#64748b;font-size:.8rem;'>max {int(d_max)}j</div>"
                            f"</div>",
                            unsafe_allow_html=True)
                    if has_note:
                        notes = df["note"].dropna()
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
                                f"</div>",
                                unsafe_allow_html=True)
                with sb:
                    if has_continent:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                    "letter-spacing:1px;margin-bottom:8px;'>Par continent</div>",
                                    unsafe_allow_html=True)
                        cont_counts = df["continent"].value_counts()
                        bars = ""
                        for cont, cnt_c in cont_counts.items():
                            bars += _hbar(cont, cnt_c, n_total, CONT_COLORS.get(cont,"#6b7280"))
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                    f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>{bars}</div>",
                                    unsafe_allow_html=True)
                    if has_type:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                    "letter-spacing:1px;margin-bottom:8px;'>Par type</div>",
                                    unsafe_allow_html=True)
                        type_counts = df["type_voyage"].value_counts()
                        bars = ""
                        for tv, cnt_t in type_counts.items():
                            bars += _hbar(tv, cnt_t, n_total, TYPE_COLORS.get(tv,"#6b7280"))
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                    f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                                    unsafe_allow_html=True)

                # Top destinations
                if has_budget:
                    st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                "letter-spacing:1px;margin:14px 0 8px;'>Top destinations — budget</div>",
                                unsafe_allow_html=True)
                    top_dest = (df.groupby("destination")["budget"]
                                .sum().sort_values(ascending=False).head(8))
                    max_b    = top_dest.max()
                    bars     = ""
                    for dest, b in top_dest.items():
                        cont_dest = df[df["destination"]==dest]["continent"].iloc[0] if has_continent else ""
                        col_dest  = CONT_COLORS.get(cont_dest,"#6b7280")
                        bars     += _hbar(dest, int(b), int(max_b), col_dest,
                                          fmt=lambda x: f"{x:,}€")
                    st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                                unsafe_allow_html=True)

            elif has_nom:  # client stats
                sa, sb = st.columns(2)
                with sa:
                    n_total = len(df)
                    if "statut" in df.columns:
                        n_actif = (df["statut"] == "actif").sum()
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
                            f"font-family:JetBrains Mono,monospace;'>{n_total-n_actif}</div>"
                            f"<div style='color:#64748b;font-size:.78rem;'>inactifs</div></div>"
                            f"</div></div>",
                            unsafe_allow_html=True)
                with sb:
                    if has_ville:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                    "letter-spacing:1px;margin-bottom:8px;'>Par ville</div>",
                                    unsafe_allow_html=True)
                        ville_counts = df["ville"].value_counts().head(8)
                        bars = ""
                        for ville, cnt_v in ville_counts.items():
                            bars += _hbar(ville, cnt_v, n_total, "#6366f1")
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                    f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                                    unsafe_allow_html=True)
            else:
                st.info("Statistiques non disponibles pour cette combinaison de colonnes.")

    # ── Enrichissement automatique via FK ──────────────────────────────────────
    st.markdown("---")
    opts = st.session_state.get("enrich_opts", [])

    if len(sel_tables) > 1:
        # Déjà multi-tables : pas d'enrichissement à proposer
        pass
    elif not opts:
        # Mono-table et aucune option détectée
        st.markdown(
            "<div style='background:#1a1d27;border:1px solid #2a2d3e;border-radius:10px;"
            "padding:12px 16px;color:#6b7280;font-size:.85rem;'>"
            "ℹ️ Aucune table liée détectée via clé étrangère.</div>",
            unsafe_allow_html=True)
    else:
        for opt in opts:
            t_other = opt["table"]
            cnt_val = opt["count"]
            fk_lbl  = opt["fk_label"]

            if cnt_val == 0:
                st.markdown(
                    f"<div style='background:#1a1d27;border:1px solid #2a2d3e;"
                    f"border-radius:10px;padding:12px 16px;color:#6b7280;font-size:.85rem;'>"
                    f"ℹ️ Aucune donnée dans <b style='color:#94a3b8'>{t_other}</b> "
                    f"pour ces résultats (<code>{fk_lbl}</code>).</div>",
                    unsafe_allow_html=True)
                continue

            em = f"enrich-btn-{t_other}"
            st.markdown(
                f'<div id="{em}"></div><style>'
                f"div.element-container:has(#{em}) + div.element-container button{{"
                f"background:linear-gradient(135deg,#065f46,#047857)!important;"
                f"border:1px solid #059669!important;box-shadow:0 0 14px #05966966!important;"
                f"font-size:.92rem!important;padding:10px 0!important;}}"
                f"div.element-container:has(#{em}) + div.element-container button:hover{{"
                f"filter:brightness(1.15)!important;transform:translateY(-1px)!important;}}</style>",
                unsafe_allow_html=True)

            btn_label = (f"🔗 Enrichir avec {t_other} — {cnt_val} ligne{'s' if cnt_val>1 else ''} "
                         f"disponible{'s' if cnt_val>1 else ''}  "
                         f"  ({fk_lbl})")
            if st.button(btn_label, width="stretch", key=f"enrich_btn_{t_other}"):
                try:
                    old_cols = set(df.columns)
                    new_tables = sel_tables + [t_other]
                    rels = fk_rels()
                    from_sql, _ = build_join_sql(new_tables, rels)
                    where = st.session_state.last_where
                    params = st.session_state.last_params
                    enriched = run_join_query(new_tables, where, params)
                    new_cols = set(enriched.columns)
                    added    = new_cols - old_cols

                    blink = set()
                    if added & {"destination","client_nom","client_prenom","voyage_id","date_depart","type_voyage"}:
                        blink.add(2)
                    if "date_depart" in added and "date_depart" not in old_cols:
                        blink.add(3)
                    if added & {"budget","continent","type_voyage","ville","note"}:
                        blink.add(4)

                    st.session_state.results             = enriched
                    st.session_state.selected_tables     = new_tables
                    st.session_state.enrich_opts         = []
                    st.session_state["_enrich_hl_until"] = time.time() + 20
                    st.session_state["_blink_tabs"]      = blink
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur enrichissement : {e}")


