import streamlit as st
import pandas as pd
import sqlite3
from collections import OrderedDict

st.set_page_config(page_title="SQL Query Builder", page_icon="🔍", layout="wide")

# ─── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.stApp{background:#0d0f14;color:#e8eaf0;}
[data-testid="stSidebar"]{background:#13151d;border-right:1px solid #1e2130;}
[data-testid="stSidebar"] *{color:#c8cad6 !important;}
h1{font-family:'Syne',sans-serif !important;font-weight:800 !important;font-size:2.4rem !important;
   background:linear-gradient(135deg,#64b5f6,#a78bfa,#f472b6);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px;}
h2,h3{font-family:'Syne',sans-serif !important;font-weight:700 !important;color:#c8cad6 !important;}
.stButton>button{font-family:'Syne',sans-serif !important;font-weight:600 !important;
  background:linear-gradient(135deg,#3b82f6,#7c3aed) !important;
  color:white !important;border:none !important;border-radius:8px !important;transition:all .2s ease !important;}
.stButton>button:hover{transform:translateY(-1px) !important;box-shadow:0 6px 20px rgba(99,102,241,.4) !important;}
.stSelectbox>div>div,.stTextInput>div>div>input{
  background:#1a1d27 !important;border:1px solid #2a2d3e !important;
  border-radius:8px !important;color:#e8eaf0 !important;font-family:'Syne',sans-serif !important;}
.stSelectbox>div>div:hover,.stTextInput>div>div>input:focus{
  border-color:#6366f1 !important;box-shadow:0 0 0 2px rgba(99,102,241,.2) !important;}
.sql-display{background:#0a0c12;border:1px solid #1e2130;border-left:3px solid #6366f1;
  border-radius:10px;padding:20px 24px;font-family:'JetBrains Mono',monospace;
  font-size:.9rem;color:#a5f3fc;line-height:1.7;white-space:pre-wrap;margin:12px 0;}
[data-testid="stMetric"]{background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;}
[data-testid="stMetricValue"]{color:#6366f1 !important;font-family:'JetBrains Mono',monospace !important;font-weight:700 !important;}
[data-testid="stDataFrame"]{border:1px solid #1e2130;border-radius:10px;overflow:hidden;}
hr{border-color:#1e2130 !important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#0d0f14;}
::-webkit-scrollbar-thumb{background:#2a2d3e;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#6366f1;}
.col-badge{font-family:'JetBrains Mono',monospace;color:#a5f3fc;font-size:.85rem;
  background:#0d2137;border:1px solid #1e4060;padding:3px 12px;border-radius:6px;display:inline-block;margin-bottom:6px;}
.tbl-divider{border-top:1px solid #1e2130;margin:3px 0;}
.section-gap{margin-bottom:18px;}
/* Tree nodes */
.tree-wrap{background:#0f111a;border:1px solid #1e2130;border-radius:12px;padding:20px 24px;margin:12px 0;font-family:'JetBrains Mono',monospace;}
.tree-root{display:inline-block;background:linear-gradient(135deg,#312e81,#4c1d95);color:#c4b5fd;
  padding:6px 16px;border-radius:6px;font-weight:600;font-size:.85rem;margin-bottom:8px;}
.tree-op-or{display:inline-flex;align-items:center;justify-content:center;
  background:#4a044e;color:#f472b6;padding:3px 14px;border-radius:5px;
  font-size:.78rem;font-weight:700;letter-spacing:.5px;min-width:44px;}
.tree-op-et{display:inline-flex;align-items:center;justify-content:center;
  background:#172554;color:#60a5fa;padding:3px 14px;border-radius:5px;
  font-size:.78rem;font-weight:700;letter-spacing:.5px;min-width:44px;}
.tree-leaf{display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:6px;
  padding:5px 12px;font-size:.82rem;color:#e2e8f0;}
.tree-branch{border-left:2px solid #334155;margin-left:14px;padding-left:14px;}
.tree-branch-or{border-left:2px solid #4a044e;margin-left:14px;padding-left:14px;}
.tree-branch-et{border-left:2px solid #172554;margin-left:14px;padding-left:14px;}
</style>
""", unsafe_allow_html=True)

# ─── Sample DB ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS employes(
        id INTEGER PRIMARY KEY,nom TEXT,prenom TEXT,email TEXT,
        departement TEXT,poste TEXT,ville TEXT,pays TEXT,
        salaire REAL,date_embauche TEXT,statut TEXT);
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
    CREATE TABLE IF NOT EXISTS produits(
        id INTEGER PRIMARY KEY,nom TEXT,categorie TEXT,marque TEXT,
        prix REAL,stock INTEGER,description TEXT,statut TEXT);
    INSERT INTO produits VALUES
    (1,'Laptop Pro 15','Informatique','TechBrand',1299.99,42,'Laptop haute performance','disponible'),
    (2,'Souris Ergonomique','Informatique','ClickMaster',49.99,150,'Souris sans fil ergonomique','disponible'),
    (3,'Clavier Mécanique','Informatique','TypePro',129.99,80,'Clavier mécanique RGB','disponible'),
    (4,'Écran 27po 4K','Informatique','ViewClear',549.99,25,'Moniteur 4K IPS','rupture'),
    (5,'Casque Bluetooth','Audio','SoundWave',199.99,60,'Casque réducteur de bruit','disponible'),
    (6,'Enceinte Portable','Audio','BoomBox',89.99,95,'Enceinte Bluetooth waterproof','disponible'),
    (7,'Smartphone X12','Mobile','PhoneCo',799.99,30,'Smartphone 5G 128Go','disponible'),
    (8,'Tablette Tab10','Mobile','PhoneCo',449.99,18,'Tablette Android 10po','rupture'),
    (9,'Câble USB-C','Accessoires','CablePro',12.99,300,'Câble USB-C 2m','disponible'),
    (10,'Batterie Externe','Accessoires','PowerBank',39.99,120,'Batterie 20000mAh','disponible');
    """)
    conn.commit()
    return conn

# ─── Constants ─────────────────────────────────────────────────────────────────
TABLES = {
    "employes":  ["id","nom","prenom","email","departement","poste","ville","pays","salaire","date_embauche","statut"],
    "produits":  ["id","nom","categorie","marque","prix","stock","description","statut"],
}
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

# ─── State ─────────────────────────────────────────────────────────────────────
for k, v in [("conditions",[]),("selected_table","employes"),("results",None),("editing",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Tree parser ───────────────────────────────────────────────────────────────
def parse_tree(conditions):
    """
    Parse flat condition list into a tree respecting AND > OR precedence.

    Returns a list of OR-level groups.
    Each group is a list of condition indices that are AND-connected.

    Example:  [A, B(ET), C(OU), D(ET), E(OU), F]
    →  OR-groups: [ [A,B], [C,D], [E,F(ET? no, F is OU)] ]

    join_op on index i means "how i links to i-1".
    """
    if not conditions:
        return []
    or_groups = []
    current = [0]
    for i in range(1, len(conditions)):
        if conditions[i]["join_op"] == "ET":
            current.append(i)
        else:
            or_groups.append(current)
            current = [i]
    or_groups.append(current)
    return or_groups   # list of lists of indices

# ─── Query builders ────────────────────────────────────────────────────────────
def _leaf_sql(cond, placeholder=True):
    sql_sym, value_fn = OPERATORS[cond["operator"]]
    val = value_fn(cond["value"])
    if placeholder:
        return f"{cond['column']} {sql_sym} ?", val
    return f"{cond['column']} {sql_sym} '{val}'"

def build_query(table, conditions):
    """Parameterized query — uses parse_tree for correct AND/OR grouping."""
    if not conditions:
        return f"SELECT * FROM {table}", []
    or_groups = parse_tree(conditions)
    group_sql, params = [], []
    for group in or_groups:
        and_parts = []
        for idx in group:
            clause, val = _leaf_sql(conditions[idx], placeholder=True)
            and_parts.append(clause)
            params.append(val)
        if len(and_parts) == 1:
            group_sql.append(and_parts[0])
        else:
            inner = "\n      AND ".join(and_parts)
            group_sql.append(f"(\n      {inner}\n    )")
    where = "\n  OR  ".join(group_sql)
    return f"SELECT *\nFROM {table}\nWHERE {where}", params

def build_query_display(table, conditions):
    """Same but with inlined values for display."""
    if not conditions:
        return f"SELECT *\nFROM {table}"
    or_groups = parse_tree(conditions)
    group_sql = []
    for group in or_groups:
        and_parts = [_leaf_sql(conditions[idx], placeholder=False) for idx in group]
        if len(and_parts) == 1:
            group_sql.append(and_parts[0])
        else:
            inner = "\n      AND ".join(and_parts)
            group_sql.append(f"(\n      {inner}\n    )")
    where = "\n  OR  ".join(group_sql)
    return f"SELECT *\nFROM {table}\nWHERE {where}"

# ─── Tree renderer ─────────────────────────────────────────────────────────────
def render_tree(conditions, table):
    """
    Render a proper decision tree:
      SELECT * FROM t
        WHERE
          OR ──┬── AND ─┬── A
               │        └── B
               └── AND ─┬── C
                        └── D
    Uses pure HTML (no Streamlit buttons in the tree — editing is on the left panel).
    """
    or_groups = parse_tree(conditions)

    def leaf_html(idx):
        cond = conditions[idx]
        sql_sym, value_fn = OPERATORS[cond["operator"]]
        dv = value_fn(cond["value"])
        return (
            f"<span class='tree-leaf'>"
            f"<b style='color:#a5f3fc'>{cond['column']}</b>"
            f"&nbsp;<span style='color:#fbbf24'>{sql_sym}</span>&nbsp;"
            f"<span style='color:#86efac'>'{dv}'</span>"
            f"</span>"
        )

    # Build inner HTML
    body = ""

    if not or_groups:
        body = "<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>Aucune condition.</p>"

    elif len(or_groups) == 1 and len(or_groups[0]) == 1:
        # Single condition — no operator node needed
        body = f"<div style='margin:4px 0 0 0'>{leaf_html(or_groups[0][0])}</div>"

    elif len(or_groups) == 1:
        # Only AND group
        group = or_groups[0]
        and_children = ""
        for k, idx in enumerate(group):
            connector = "┣━" if k < len(group)-1 else "┗━"
            and_children += (
                f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0;'>"
                f"<span style='color:#334155;font-size:.9rem;'>{connector}</span>"
                f"{leaf_html(idx)}"
                f"</div>"
            )
        body = (
            f"<div style='display:flex;align-items:flex-start;gap:8px;margin:4px 0;'>"
            f"<span class='tree-op-et'>ET</span>"
            f"<div class='tree-branch-et'>{and_children}</div>"
            f"</div>"
        )

    else:
        # Multiple OR groups
        or_children = ""
        for g, group in enumerate(or_groups):
            connector = "┣━" if g < len(or_groups)-1 else "┗━"

            if len(group) == 1:
                # Single leaf under OR
                node_html = (
                    f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0;'>"
                    f"<span style='color:#4a044e;font-size:.9rem;'>{connector}</span>"
                    f"{leaf_html(group[0])}"
                    f"</div>"
                )
            else:
                # AND sub-group
                and_children = ""
                for k, idx in enumerate(group):
                    sub_conn = "┣━" if k < len(group)-1 else "┗━"
                    and_children += (
                        f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0;'>"
                        f"<span style='color:#334155;font-size:.9rem;'>{sub_conn}</span>"
                        f"{leaf_html(idx)}"
                        f"</div>"
                    )
                node_html = (
                    f"<div style='display:flex;align-items:flex-start;gap:8px;margin:4px 0;'>"
                    f"<span style='color:#4a044e;font-size:.9rem;'>{connector}</span>"
                    f"<span class='tree-op-et' style='margin-top:2px;'>ET</span>"
                    f"<div class='tree-branch-et'>{and_children}</div>"
                    f"</div>"
                )
            or_children += node_html

        body = (
            f"<div style='display:flex;align-items:flex-start;gap:8px;margin:4px 0;'>"
            f"<span class='tree-op-or'>OU</span>"
            f"<div class='tree-branch-or'>{or_children}</div>"
            f"</div>"
        )

    html = (
        f"<div class='tree-wrap'>"
        f"<div style='margin-bottom:10px;'>"
        f"<span style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;'>Requête</span>"
        f"<div style='margin-top:6px;'><span class='tree-root'>SELECT * FROM {table}</span></div>"
        f"</div>"
        f"<div style='padding-left:16px;border-left:2px solid #1e2130;'>"
        f"<span style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;'>WHERE</span>"
        f"<div style='margin-top:8px;'>{body}</div>"
        f"</div>"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    st.markdown("**Table source**")
    st.selectbox("Table", list(TABLES.keys()), key="selected_table", label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Colonnes disponibles**")
    for col in TABLES[st.session_state.selected_table]:
        st.markdown(
            f"<span style='font-family:JetBrains Mono,monospace;font-size:.78rem;color:#6366f1;'>› </span>"
            f"<span style='font-size:.85rem;'>{col}</span>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.caption("SQLite en mémoire — données de démonstration.")

# ─── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# 🔍 SQL Query Builder")
st.markdown("<p style='color:#6b7280;margin-top:-12px;margin-bottom:24px;'>Construisez vos requêtes SQL visuellement, sans écrire une ligne de code.</p>", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

# ══ LEFT ══════════════════════════════════════════════════════════════════════
with col_left:

    # ── Add condition ──────────────────────────────────────────────────────────
    st.markdown("### ➕ Ajouter une condition")
    c1, c2 = st.columns(2)
    with c1:
        new_col = st.selectbox("Colonne", TABLES[st.session_state.selected_table], key="new_col")
    with c2:
        new_op = st.selectbox("Opérateur", OP_LABELS, key="new_op")
    new_val = st.text_input("Valeur", key="new_val", placeholder="Entrez une valeur…")

    ba, bc = st.columns(2)
    with ba:
        if st.button("➕ Ajouter", use_container_width=True):
            if new_val.strip():
                st.session_state.conditions.append({
                    "column":   new_col,
                    "operator": new_op,
                    "value":    new_val.strip(),
                    "join_op":  "ET",   # default, user can toggle
                })
                st.rerun()
            else:
                st.warning("Veuillez entrer une valeur.")
    with bc:
        if st.button("🗑 Tout effacer", use_container_width=True):
            st.session_state.conditions = []
            st.session_state.editing    = {}
            st.session_state.results    = None
            st.rerun()

    st.markdown("---")
    st.markdown(f"### 📋 Conditions ({len(st.session_state.conditions)})")

    if not st.session_state.conditions:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:.9rem;'>Aucune condition.</p>", unsafe_allow_html=True)
    else:
        groups = OrderedDict()
        for i, cond in enumerate(st.session_state.conditions):
            groups.setdefault(cond["column"], []).append((i, cond))

        for col_name, entries in groups.items():
            st.markdown(
                f"<div class='col-badge'>📌 {col_name}</div>"
                f"<span style='color:#4a5170;font-size:.75rem;margin-left:8px;'>{len(entries)} filtre(s)</span>",
                unsafe_allow_html=True,
            )
            # Header
            th1, th2, th3 = st.columns([3, 3, 1])
            with th1: st.markdown("<span style='color:#6366f1;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Opérateur</span>", unsafe_allow_html=True)
            with th2: st.markdown("<span style='color:#6366f1;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Valeur</span>", unsafe_allow_html=True)
            with th3: st.markdown("", unsafe_allow_html=True)
            st.markdown("<div class='tbl-divider'></div>", unsafe_allow_html=True)

            for row_idx, (global_i, cond) in enumerate(entries):
                editing_field = st.session_state.editing.get(global_i)

                # Join op toggle — shown for every condition except the very first overall
                if global_i > 0:
                    jp1, _jp2, _jp3 = st.columns([3, 3, 1])
                    with jp1:
                        join_label = st.session_state.conditions[global_i]["join_op"]
                        btn_color  = "#172554" if join_label == "ET" else "#4a044e"
                        txt_color  = "#60a5fa" if join_label == "ET" else "#f472b6"
                        if st.button(
                            f"⇅ {join_label}",
                            key=f"join_{global_i}",
                            help="Basculer ET / OU",
                        ):
                            st.session_state.conditions[global_i]["join_op"] = \
                                "OU" if join_label == "ET" else "ET"
                            st.rerun()

                rc1, rc2, rc3 = st.columns([3, 3, 1])

                # Operator cell
                with rc1:
                    if editing_field == "operator":
                        sel = st.selectbox("op", OP_LABELS,
                            index=OP_LABELS.index(cond["operator"]),
                            key=f"eop_{global_i}", label_visibility="collapsed")
                        st.session_state.conditions[global_i]["operator"] = sel
                        if st.button("✓", key=f"cop_{global_i}"):
                            st.session_state.editing.pop(global_i, None); st.rerun()
                    else:
                        st.markdown(f"<span style='color:#fbbf24;font-size:.83rem;'>{cond['operator']}</span>", unsafe_allow_html=True)
                        if st.button("✏️", key=f"bop_{global_i}", help="Modifier"):
                            st.session_state.editing[global_i] = "operator"; st.rerun()

                # Value cell
                with rc2:
                    if editing_field == "value":
                        nv = st.text_input("val", value=cond["value"],
                            key=f"eval_{global_i}", label_visibility="collapsed")
                        st.session_state.conditions[global_i]["value"] = nv
                        if st.button("✓", key=f"cval_{global_i}"):
                            st.session_state.editing.pop(global_i, None); st.rerun()
                    else:
                        st.markdown(f"<span style='color:#86efac;font-size:.83rem;font-family:JetBrains Mono,monospace;'>«{cond['value']}»</span>", unsafe_allow_html=True)
                        if st.button("✏️", key=f"bval_{global_i}", help="Modifier"):
                            st.session_state.editing[global_i] = "value"; st.rerun()

                # Delete cell
                with rc3:
                    if st.button("✕", key=f"del_{global_i}"):
                        st.session_state.conditions.pop(global_i)
                        st.session_state.editing.pop(global_i, None)
                        st.rerun()

                if row_idx < len(entries) - 1:
                    st.markdown("<div class='tbl-divider'></div>", unsafe_allow_html=True)

            st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    if st.button("▶ Exécuter la requête", use_container_width=True, type="primary"):
        conn = get_connection()
        q, params = build_query(st.session_state.selected_table, st.session_state.conditions)
        try:
            st.session_state.results = pd.read_sql_query(q, conn, params=params)
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

# ══ RIGHT ═════════════════════════════════════════════════════════════════════
with col_right:
    st.markdown("### 🌳 Arbre de décision")
    st.caption("ET est prioritaire sur OU (précédence SQL standard). Les badges ⇅ ET/OU dans le tableau permettent de changer l'opérateur.")
    render_tree(st.session_state.conditions, st.session_state.selected_table)

    st.markdown("### 🧾 Requête SQL générée")
    preview = build_query_display(st.session_state.selected_table, st.session_state.conditions)
    st.markdown(f"<div class='sql-display'>{preview}</div>", unsafe_allow_html=True)

# ══ RESULTS ═══════════════════════════════════════════════════════════════════
if st.session_state.results is not None:
    df = st.session_state.results
    st.markdown("---")
    st.markdown("### 📊 Résultats")
    m1, m2, m3 = st.columns(3)
    m1.metric("Lignes", len(df))
    m2.metric("Colonnes", len(df.columns))
    m3.metric("Conditions", len(st.session_state.conditions))
    if len(df) == 0:
        st.info("Aucun résultat ne correspond à vos critères.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("⬇ Télécharger CSV",
            df.to_csv(index=False).encode("utf-8"),
            f"resultats_{st.session_state.selected_table}.csv", "text/csv")
