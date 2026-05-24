import streamlit as st
import pandas as pd
import sqlite3
import json
from typing import Optional

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SQL Query Builder",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');

/* ---- Base ---- */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: #0d0f14;
    color: #e8eaf0;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: #13151d;
    border-right: 1px solid #1e2130;
}
[data-testid="stSidebar"] * {
    color: #c8cad6 !important;
}

/* ---- Titles ---- */
h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2.4rem !important;
    background: linear-gradient(135deg, #64b5f6, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}
h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    color: #c8cad6 !important;
}

/* ---- Buttons ---- */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    background: linear-gradient(135deg, #3b82f6, #7c3aed) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.3px;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
}

/* ---- Inputs / Selects ---- */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea textarea {
    background: #1a1d27 !important;
    border: 1px solid #2a2d3e !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
    font-family: 'Syne', sans-serif !important;
}
.stSelectbox > div > div:hover,
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}

/* ---- Code / Query blocks ---- */
.sql-display {
    background: #0a0c12;
    border: 1px solid #1e2130;
    border-left: 3px solid #6366f1;
    border-radius: 10px;
    padding: 20px 24px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    color: #a5f3fc;
    line-height: 1.7;
    white-space: pre-wrap;
    margin: 12px 0;
}

/* ---- Tree ---- */
.tree-container {
    background: #0f111a;
    border: 1px solid #1e2130;
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
}
.tree-node-root {
    display: inline-block;
    background: linear-gradient(135deg, #312e81, #4c1d95);
    color: #c4b5fd;
    padding: 6px 16px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 4px;
}
.tree-node-cond {
    display: inline-block;
    background: #1e293b;
    color: #7dd3fc;
    padding: 4px 12px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    border: 1px solid #334155;
}
.tree-op {
    display: inline-block;
    background: #172554;
    color: #93c5fd;
    padding: 2px 10px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 2px 4px;
}
.tree-line {
    border-left: 2px solid #334155;
    margin-left: 20px;
    padding-left: 20px;
}

/* ---- Condition cards ---- */
.cond-card {
    background: #13151d;
    border: 1px solid #1e2130;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.cond-index {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #6366f1;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}

/* ---- Metrics ---- */
[data-testid="stMetric"] {
    background: #13151d;
    border: 1px solid #1e2130;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] {
    color: #6366f1 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
}

/* ---- Dataframe ---- */
[data-testid="stDataFrame"] {
    border: 1px solid #1e2130;
    border-radius: 10px;
    overflow: hidden;
}

/* ---- Divider ---- */
hr {
    border-color: #1e2130 !important;
}

/* ---- Expander ---- */
[data-testid="stExpander"] {
    background: #13151d;
    border: 1px solid #1e2130;
    border-radius: 10px;
}

/* ---- Scrollbar ---- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d0f14; }
::-webkit-scrollbar-thumb { background: #2a2d3e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #6366f1; }
</style>
""", unsafe_allow_html=True)

# ─── Sample DB ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS employes (
        id INTEGER PRIMARY KEY,
        nom TEXT,
        prenom TEXT,
        email TEXT,
        departement TEXT,
        poste TEXT,
        ville TEXT,
        pays TEXT,
        salaire REAL,
        date_embauche TEXT,
        statut TEXT
    );

    INSERT INTO employes VALUES
    (1,'Martin','Alice','alice.martin@corp.fr','Informatique','Développeur Senior','Paris','France',72000,'2019-03-15','actif'),
    (2,'Dupont','Bruno','b.dupont@corp.fr','Marketing','Chef de Projet','Lyon','France',58000,'2020-07-01','actif'),
    (3,'Bernard','Clara','clara.b@corp.fr','RH','Responsable RH','Marseille','France',61000,'2018-01-20','actif'),
    (4,'Petit','David','d.petit@corp.fr','Informatique','DevOps','Paris','France',68000,'2021-05-10','actif'),
    (5,'Robert','Emma','emma.robert@corp.fr','Finance','Analyste','Bordeaux','France',55000,'2022-02-28','inactif'),
    (6,'Richard','Félix','felix.r@corp.fr','Ventes','Commercial','Paris','France',49000,'2020-11-03','actif'),
    (7,'Durand','Gina','gina.durand@corp.fr','Informatique','Architecte','Toulouse','France',85000,'2017-09-01','actif'),
    (8,'Moreau','Hugo','h.moreau@corp.fr','Marketing','Designer UX','Nantes','France',52000,'2023-01-15','actif'),
    (9,'Simon','Iris','iris.simon@corp.fr','Finance','Comptable','Paris','France',47000,'2021-08-20','actif'),
    (10,'Michel','Jules','jules.m@corp.fr','RH','Assistant RH','Lille','France',39000,'2023-06-05','actif'),
    (11,'Lefevre','Karla','karla.l@corp.fr','Informatique','Développeur Junior','Paris','France',42000,'2023-09-01','actif'),
    (12,'Leroy','Luc','luc.leroy@corp.fr','Ventes','Directeur Commercial','Lyon','France',92000,'2015-04-12','actif'),
    (13,'Roux','Marie','marie.roux@corp.fr','Marketing','Responsable Marketing','Paris','France',74000,'2016-03-22','inactif'),
    (14,'Fournier','Noé','noe.f@corp.fr','Informatique','Data Scientist','Grenoble','France',78000,'2020-01-07','actif'),
    (15,'Girard','Olivia','o.girard@corp.fr','RH','DRH','Paris','France',105000,'2013-10-30','actif');

    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY,
        nom TEXT,
        categorie TEXT,
        marque TEXT,
        prix REAL,
        stock INTEGER,
        description TEXT,
        statut TEXT
    );

    INSERT INTO produits VALUES
    (1,'Laptop Pro 15','Informatique','TechBrand',1299.99,42,'Laptop haute performance','disponible'),
    (2,'Souris Ergonomique','Informatique','ClickMaster',49.99,150,'Souris sans fil ergonomique','disponible'),
    (3,'Clavier Mécanique','Informatique','TypePro',129.99,80,'Clavier mécanique RGB','disponible'),
    (4,'Écran 27" 4K','Informatique','ViewClear',549.99,25,'Moniteur 4K IPS','rupture'),
    (5,'Casque Bluetooth','Audio','SoundWave',199.99,60,'Casque réducteur de bruit','disponible'),
    (6,'Enceinte Portable','Audio','BoomBox',89.99,95,'Enceinte Bluetooth waterproof','disponible'),
    (7,'Smartphone X12','Mobile','PhoneCo',799.99,30,'Smartphone 5G 128Go','disponible'),
    (8,'Tablette Tab10','Mobile','PhoneCo',449.99,18,'Tablette Android 10"','rupture'),
    (9,'Câble USB-C','Accessoires','CablePro',12.99,300,'Câble USB-C 2m','disponible'),
    (10,'Batterie Externe','Accessoires','PowerBank',39.99,120,'Batterie 20000mAh','disponible');
    """)
    conn.commit()
    return conn

# ─── State init ────────────────────────────────────────────────────────────────
def init_state():
    if "conditions" not in st.session_state:
        st.session_state.conditions = []
    if "global_op" not in st.session_state:
        st.session_state.global_op = "ET"
    if "selected_table" not in st.session_state:
        st.session_state.selected_table = "employes"
    if "results" not in st.session_state:
        st.session_state.results = None
    if "query_str" not in st.session_state:
        st.session_state.query_str = ""

init_state()

# ─── Helpers ───────────────────────────────────────────────────────────────────
TABLES = {
    "employes": ["id", "nom", "prenom", "email", "departement", "poste", "ville", "pays", "salaire", "date_embauche", "statut"],
    "produits": ["id", "nom", "categorie", "marque", "prix", "stock", "description", "statut"],
}

OPERATORS = {
    "Contient": ("LIKE", lambda v: f"%{v}%"),
    "Commence par": ("LIKE", lambda v: f"{v}%"),
    "Finit par": ("LIKE", lambda v: f"%{v}"),
    "Égal à": ("=", lambda v: v),
    "Différent de": ("!=", lambda v: v),
    "Supérieur à": (">", lambda v: v),
    "Inférieur à": ("<", lambda v: v),
}

def build_query_display(table: str, conditions: list, global_op: str) -> str:
    """Build SQL query with values inlined for display (no placeholders)."""
    if not conditions:
        return f"SELECT *\nFROM {table}"
    sql_op = "AND" if global_op == "ET" else "OR"
    clauses = []
    for cond in conditions:
        sql_sym, value_fn = OPERATORS[cond["operator"]]
        transformed = value_fn(cond["value"])
        clauses.append(f"{cond['column']} {sql_sym} '{transformed}'")
    where = f"\n  {sql_op} ".join(clauses)
    return f"SELECT *\nFROM {table}\nWHERE {where}"


def build_query(table: str, conditions: list, global_op: str) -> tuple[str, list]:
    """Build SQL query string and params list."""
    if not conditions:
        return f"SELECT * FROM {table}", []

    clauses, params = [], []
    sql_op = "AND" if global_op == "ET" else "OR"

    for cond in conditions:
        col = cond["column"]
        op_label = cond["operator"]
        value = cond["value"]

        sql_sym, value_fn = OPERATORS[op_label]
        transformed = value_fn(value)

        clauses.append(f"{col} {sql_sym} ?")
        params.append(transformed)

    where = f"\n  {sql_op} ".join(clauses)
    query = f"SELECT *\nFROM {table}\nWHERE {where}"
    return query, params

def build_tree_html(conditions: list, global_op: str) -> str:
    """Render a visual tree representation."""
    if not conditions:
        return "<p style='color:#4a5170;font-style:italic;'>Aucune condition ajoutée.</p>"

    op_color = "#60a5fa" if global_op == "ET" else "#f472b6"
    op_bg = "#172554" if global_op == "ET" else "#4a044e"

    html = f"""
    <div class='tree-container'>
      <div style='margin-bottom:12px;'>
        <span style='color:#94a3b8;font-size:0.8rem;font-family:JetBrains Mono,monospace;'>REQUÊTE</span>
        <div style='margin-top:4px;'>
          <span class='tree-node-root'>SELECT * FROM {st.session_state.selected_table}</span>
        </div>
      </div>
      <div class='tree-line'>
        <div style='margin-bottom:8px;'>
          <span style='color:#94a3b8;font-size:0.78rem;font-family:JetBrains Mono,monospace;'>WHERE</span>
        </div>
    """

    for i, cond in enumerate(conditions):
        col = cond["column"]
        op_label = cond["operator"]
        val = cond["value"]
        sql_sym, value_fn = OPERATORS[op_label]
        display_val = value_fn(val)

        node = f'<span style="color:#a5f3fc">{col}</span> <span style="color:#fbbf24">{sql_sym}</span> <span style="color:#86efac">"{display_val}"</span>'

        if i > 0:
            html += f"""
            <div style='margin: 4px 0;'>
              <span style='background:{op_bg};color:{op_color};padding:2px 10px;border-radius:4px;
                           font-family:JetBrains Mono,monospace;font-size:0.75rem;font-weight:700;'>
                {global_op}
              </span>
            </div>"""

        html += f"""
        <div style='margin: 4px 0;'>
          <div class='tree-line' style='margin-left:12px;padding-left:14px;border-left-color:#334155;'>
            <span class='tree-node-cond'>{node}</span>
          </div>
        </div>
        """

    html += "</div></div>"
    return html

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    st.markdown("**Table source**")
    table = st.selectbox(
        "Table",
        list(TABLES.keys()),
        key="selected_table",
        label_visibility="collapsed",
    )

    st.markdown("**Opérateur global**")
    global_op = st.radio(
        "Opérateur",
        ["ET", "OU"],
        horizontal=True,
        key="global_op",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Colonnes disponibles**")
    for col in TABLES[st.session_state.selected_table]:
        st.markdown(f"<span style='font-family:JetBrains Mono,monospace;font-size:0.78rem;color:#6366f1;'>› </span><span style='font-size:0.85rem;'>{col}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Données de démonstration embarquées en SQLite en mémoire.")

# ─── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# 🔍 SQL Query Builder")
st.markdown("<p style='color:#6b7280;margin-top:-12px;margin-bottom:24px;'>Construisez vos requêtes SQL visuellement, sans écrire une ligne de code.</p>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

# ── Left: condition builder ────────────────────────────────────────────────────
with col_left:
    st.markdown("### ➕ Ajouter une condition")

    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            new_col = st.selectbox("Colonne", TABLES[st.session_state.selected_table], key="new_col")
        with c2:
            new_op = st.selectbox("Opérateur", list(OPERATORS.keys()), key="new_op")

        new_val = st.text_input("Valeur recherchée", key="new_val", placeholder="Entrez une valeur…")

        col_add, col_clear = st.columns([1, 1])
        with col_add:
            if st.button("➕ Ajouter la condition", use_container_width=True):
                if new_val.strip():
                    st.session_state.conditions.append({
                        "column": new_col,
                        "operator": new_op,
                        "value": new_val.strip(),
                    })
                    st.rerun()
                else:
                    st.warning("Veuillez entrer une valeur.")
        with col_clear:
            if st.button("🗑 Tout effacer", use_container_width=True):
                st.session_state.conditions = []
                st.session_state.results = None
                st.rerun()

    st.markdown("---")
    st.markdown(f"### 📋 Conditions ({len(st.session_state.conditions)})")

    if not st.session_state.conditions:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:0.9rem;'>Aucune condition. Ajoutez des filtres ci-dessus.</p>", unsafe_allow_html=True)
    else:
        # Group conditions by column, preserving insertion order
        from collections import OrderedDict
        groups = OrderedDict()
        for i, cond in enumerate(st.session_state.conditions):
            col_name = cond["column"]
            if col_name not in groups:
                groups[col_name] = []
            groups[col_name].append((i, cond))

        for col_name, entries in groups.items():
            # Column header
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'>"
                f"<span style='font-family:JetBrains Mono,monospace;color:#a5f3fc;font-size:0.85rem;"
                f"background:#0d2137;border:1px solid #1e4060;padding:3px 12px;border-radius:6px;'>"
                f"📌 {col_name}</span>"
                f"<span style='color:#4a5170;font-size:0.75rem;'>{len(entries)} filtre(s)</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Table header
            h1, h2, h3 = st.columns([2, 2, 1])
            with h1:
                st.markdown("<span style='color:#6366f1;font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Opérateur</span>", unsafe_allow_html=True)
            with h2:
                st.markdown("<span style='color:#6366f1;font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Valeur</span>", unsafe_allow_html=True)
            with h3:
                st.markdown("<span style='color:#6366f1;font-size:0.73rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;font-family:JetBrains Mono,monospace;'></span>", unsafe_allow_html=True)

            st.markdown("<div style='border-top:1px solid #1e2130;margin:4px 0 2px 0;'></div>", unsafe_allow_html=True)

            # One row per condition
            for row_idx, (global_i, cond) in enumerate(entries):
                rc1, rc2, rc3 = st.columns([2, 2, 1])
                with rc1:
                    st.markdown(f"<span style='color:#fbbf24;font-size:0.83rem;'>{cond['operator']}</span>", unsafe_allow_html=True)
                with rc2:
                    st.markdown(f"<span style='color:#86efac;font-size:0.83rem;font-family:JetBrains Mono,monospace;'>«{cond['value']}»</span>", unsafe_allow_html=True)
                with rc3:
                    if st.button("✕", key=f"del_{global_i}", help=f"Supprimer cette condition"):
                        st.session_state.conditions.pop(global_i)
                        st.rerun()

                if row_idx < len(entries) - 1:
                    st.markdown("<div style='border-top:1px solid #1a1d27;margin:0;'></div>", unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    if st.button("▶ Exécuter la requête", use_container_width=True, type="primary"):
        conn = get_connection()
        query, params = build_query(
            st.session_state.selected_table,
            st.session_state.conditions,
            st.session_state.global_op,
        )
        st.session_state.query_str = query
        try:
            df = pd.read_sql_query(query, conn, params=params)
            st.session_state.results = df
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

# ── Right: tree + SQL ─────────────────────────────────────────────────────────
with col_right:
    st.markdown("### 🌳 Arbre de recherche")
    tree_html = build_tree_html(st.session_state.conditions, st.session_state.global_op)
    st.markdown(tree_html, unsafe_allow_html=True)

    st.markdown("### 🧾 Requête SQL générée")
    query_preview = build_query_display(
        st.session_state.selected_table,
        st.session_state.conditions,
        st.session_state.global_op,
    )
    st.markdown(f"<div class='sql-display'>{query_preview}</div>", unsafe_allow_html=True)

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.results is not None:
    df = st.session_state.results
    st.markdown("---")
    st.markdown("### 📊 Résultats")

    m1, m2, m3 = st.columns(3)
    m1.metric("Lignes retournées", len(df))
    m2.metric("Colonnes", len(df.columns))
    m3.metric("Conditions actives", len(st.session_state.conditions))

    if len(df) == 0:
        st.info("Aucun résultat ne correspond à vos critères.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ Télécharger les résultats (CSV)",
            data=csv,
            file_name=f"resultats_{st.session_state.selected_table}.csv",
            mime="text/csv",
        )
