import streamlit as st
import pandas as pd
import sqlite3
from collections import OrderedDict

st.set_page_config(page_title="SQL Query Builder", page_icon="🔍",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.stApp{background:#0d0f14;color:#e8eaf0;}
[data-testid="stSidebar"]{background:#13151d;border-right:1px solid #1e2130;}
[data-testid="stSidebar"] *{color:#c8cad6!important;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;font-size:2.4rem!important;
   background:linear-gradient(135deg,#64b5f6,#a78bfa,#f472b6);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px;}
h2,h3{font-family:'Syne',sans-serif!important;font-weight:700!important;color:#c8cad6!important;}
.stButton>button{font-family:'Syne',sans-serif!important;font-weight:600!important;
   background:linear-gradient(135deg,#3b82f6,#7c3aed)!important;color:white!important;
   border:none!important;border-radius:8px!important;transition:all .2s!important;}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(99,102,241,.4)!important;}
.stSelectbox>div>div,.stTextInput>div>div>input{background:#1a1d27!important;border:1px solid #2a2d3e!important;
   border-radius:8px!important;color:#e8eaf0!important;font-family:'Syne',sans-serif!important;}
.stSelectbox>div>div:hover,.stTextInput>div>div>input:focus{border-color:#6366f1!important;
   box-shadow:0 0 0 2px rgba(99,102,241,.2)!important;}
.sql-display{background:#0a0c12;border:1px solid #1e2130;border-left:3px solid #6366f1;
   border-radius:10px;padding:20px 24px;font-family:'JetBrains Mono',monospace;
   font-size:.88rem;color:#a5f3fc;line-height:1.8;white-space:pre-wrap;margin:12px 0;}
.tree-wrap{background:#0f111a;border:1px solid #1e2130;border-radius:12px;
   padding:18px 18px 12px;margin:10px 0;}
.t-root{display:inline-block;background:linear-gradient(135deg,#312e81,#4c1d95);color:#c4b5fd;
   padding:6px 16px;border-radius:6px;font-family:'JetBrains Mono',monospace;
   font-weight:600;font-size:.85rem;}
.t-leaf{background:#1e293b;border:1px solid #334155;border-radius:6px;
   padding:4px 12px;font-family:'JetBrains Mono',monospace;font-size:.8rem;
   display:inline-block;line-height:1.8;}
/* Override gradient for tree branch toggle buttons */
div[data-testid="stHorizontalBlock"] div[data-branch-btn="true"] button,
.branch-btn button {
    background:#172554!important;color:#60a5fa!important;
    border:1px solid #1e3a8a!important;border-radius:5px!important;
    font-family:'JetBrains Mono',monospace!important;font-size:.78rem!important;
    padding:2px 12px!important;min-height:0!important;font-weight:700!important;}
[data-testid="stMetric"]{background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;}
[data-testid="stMetricValue"]{color:#6366f1!important;font-family:'JetBrains Mono',monospace!important;font-weight:700!important;}
[data-testid="stDataFrame"]{border:1px solid #1e2130;border-radius:10px;overflow:hidden;}
hr{border-color:#1e2130!important;}
::-webkit-scrollbar{width:6px;height:6px;}::-webkit-scrollbar-track{background:#0d0f14;}
::-webkit-scrollbar-thumb{background:#2a2d3e;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#6366f1;}
.col-badge{font-family:'JetBrains Mono',monospace;color:#a5f3fc;font-size:.85rem;
   background:#0d2137;border:1px solid #1e4060;padding:3px 12px;border-radius:6px;display:inline-block;}
.tbl-divider{border-top:1px solid #1e2130;margin:3px 0;}
</style>
""", unsafe_allow_html=True)

# ── DB ─────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS employes(id INTEGER PRIMARY KEY,nom TEXT,prenom TEXT,
      email TEXT,departement TEXT,poste TEXT,ville TEXT,pays TEXT,
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
    CREATE TABLE IF NOT EXISTS produits(id INTEGER PRIMARY KEY,nom TEXT,categorie TEXT,
      marque TEXT,prix REAL,stock INTEGER,description TEXT,statut TEXT);
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

# ── Constants ──────────────────────────────────────────────────────────────────
TABLES = {
    "employes": ["id","nom","prenom","email","departement","poste","ville","pays","salaire","date_embauche","statut"],
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

# ── State ──────────────────────────────────────────────────────────────────────
for k, v in [("conditions",[]),("selected_table","employes"),("results",None),("editing",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# LEFT-ASSOCIATIVE BINARY TREE
#
# Conditions are folded left-to-right into a binary tree:
#   C0                          → leaf(C0, idx=0)
#   C0, C1(ET)                  → ET( leaf(C0), leaf(C1) )
#   C0, C1(ET), C2(OU)          → OU( ET(C0,C1), leaf(C2) )
#   C0, C1(ET), C2(OU), C3(ET)  → ET( OU(ET(C0,C1),C2), leaf(C3) )
#
# Every branch node's "right" child is always a leaf whose idx = that
# condition's index in the flat list.  That idx is the key for the button.
# ══════════════════════════════════════════════════════════════════════════════
def build_tree(conditions):
    if not conditions:
        return None
    tree = {"type": "leaf", "idx": 0}
    for i in range(1, len(conditions)):
        tree = {
            "type":  "branch",
            "op":    conditions[i]["join_op"],
            "left":  tree,
            "right": {"type": "leaf", "idx": i},
        }
    return tree

def _sql_from_tree(node, conditions, params, display):
    if node["type"] == "leaf":
        c = conditions[node["idx"]]
        sym, fn = OPERATORS[c["operator"]]
        val = fn(c["value"])
        if display:
            return f"{c['column']} {sym} '{val}'"
        params.append(val)
        return f"{c['column']} {sym} ?"
    sql_op = "AND" if node["op"] == "ET" else "OR"
    L = _sql_from_tree(node["left"],  conditions, params, display)
    R = _sql_from_tree(node["right"], conditions, params, display)
    return f"({L} {sql_op} {R})"

def build_query(table, conditions):
    if not conditions:
        return f"SELECT * FROM {table}", []
    params = []
    where = _sql_from_tree(build_tree(conditions), conditions, params, False)
    return f"SELECT *\nFROM {table}\nWHERE {where}", params

def build_query_display(table, conditions):
    if not conditions:
        return f"SELECT *\nFROM {table}"
    where = _sql_from_tree(build_tree(conditions), conditions, [], True)
    return f"SELECT *\nFROM {table}\nWHERE {where}"

# ══════════════════════════════════════════════════════════════════════════════
# TREE RENDERER — mixes st.markdown (leaves) and st.button (branches)
#
# Each row is rendered using st.columns:
#   [ prefix column ]  |  [ node content ]
#
# The prefix column width scales with indentation depth.
# Branch nodes become real Streamlit buttons → clicking toggles ET/OU.
# ══════════════════════════════════════════════════════════════════════════════
def _leaf_html(conditions, idx):
    c = conditions[idx]
    sym, fn = OPERATORS[c["operator"]]
    dv = fn(c["value"])
    return (
        f"<span class='t-leaf'>"
        f"<b style='color:#a5f3fc;'>{c['column']}</b> "
        f"<span style='color:#fbbf24;'>{sym}</span> "
        f"<span style='color:#86efac;'>'{dv}'</span>"
        f"</span>"
    )

def _prefix_html(prefix, connector):
    """Monospace tree-connector text."""
    txt = prefix + connector
    if not txt:
        return ""
    return (
        f"<div style='padding-top:8px;font-family:JetBrains Mono,monospace;"
        f"color:#334155;white-space:pre;font-size:.82rem;line-height:1;'>{txt}</div>"
    )

def _render_node(node, conditions, prefix="", is_last=True, is_root=False):
    """Recursively render one tree node."""
    connector    = "" if is_root else ("└── " if is_last else "├── ")
    child_prefix = prefix + ("    " if is_last else "│   ")

    if node["type"] == "leaf":
        # Pure HTML row — no interactivity needed
        full_pre = prefix + connector
        if full_pre:
            # split: [narrow prefix col] | [leaf content]
            w = max(len(full_pre) * 0.14, 0.4)
            ca, cb = st.columns([w, max(9 - w, 1)])
            ca.markdown(_prefix_html("", full_pre), unsafe_allow_html=True)
            cb.markdown(
                f"<div style='padding-top:6px;'>{_leaf_html(conditions, node['idx'])}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(_leaf_html(conditions, node["idx"]), unsafe_allow_html=True)

    else:
        # Branch node — Streamlit button
        op        = node["op"]
        right_idx = node["right"]["idx"]   # unique per branch in a left-leaning tree
        full_pre  = prefix + connector
        is_et     = (op == "ET")
        btn_label = op

        if full_pre:
            w = max(len(full_pre) * 0.14, 0.4)
            ca, cb = st.columns([w, max(9 - w, 1)])
            ca.markdown(_prefix_html("", full_pre), unsafe_allow_html=True)
            with cb:
                _branch_button(btn_label, right_idx, is_et)
        else:
            _branch_button(btn_label, right_idx, is_et)

        # Recurse: left first (is_last=False), then right (is_last=True)
        _render_node(node["left"],  conditions, child_prefix, is_last=False)
        _render_node(node["right"], conditions, child_prefix, is_last=True)


def _branch_button(label, right_idx, is_et):
    """Render a styled ET/OU toggle button."""
    # Inject per-button CSS via a wrapper div trick
    bg     = "#172554" if is_et else "#4a044e"
    color  = "#60a5fa" if is_et else "#f472b6"
    border = "#1e3a8a" if is_et else "#831843"
    st.markdown(
        f"<style>"
        f"div[data-testid='stButton']:has(button[kind][id$='treeop_{right_idx}']) button{{"
        f"background:{bg}!important;color:{color}!important;"
        f"border:1px solid {border}!important;"
        f"font-family:'JetBrains Mono',monospace!important;"
        f"font-size:.8rem!important;font-weight:700!important;"
        f"padding:2px 14px!important;border-radius:5px!important;}}"
        f"</style>",
        unsafe_allow_html=True,
    )
    if st.button(label, key=f"treeop_{right_idx}", help="Cliquer pour basculer ET / OU"):
        st.session_state.conditions[right_idx]["join_op"] = "OU" if label == "ET" else "ET"
        st.rerun()


def render_tree(conditions, table):
    # Header card (pure HTML — static)
    st.markdown(
        f"<div class='tree-wrap'>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>Requête</span>"
        f"<div style='margin:6px 0 12px;'><span class='t-root'>SELECT * FROM {table}</span></div>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>WHERE</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    tree = build_tree(conditions)
    if tree is None:
        st.markdown(
            "<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>"
            "Aucune condition.</p>",
            unsafe_allow_html=True,
        )
        return
    _render_node(tree, conditions, prefix="", is_last=True, is_root=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
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

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("# 🔍 SQL Query Builder")
st.markdown(
    "<p style='color:#6b7280;margin-top:-12px;margin-bottom:24px;'>"
    "Construisez vos requêtes SQL visuellement, sans écrire une ligne de code.</p>",
    unsafe_allow_html=True,
)
col_left, col_right = st.columns([1, 1], gap="large")

# ══ LEFT — add + editable table ══════════════════════════════════════════════
with col_left:
    st.markdown("### ➕ Ajouter une condition")
    c1, c2 = st.columns(2)
    with c1: new_col = st.selectbox("Colonne", TABLES[st.session_state.selected_table], key="new_col")
    with c2: new_op  = st.selectbox("Opérateur", OP_LABELS, key="new_op")
    new_val = st.text_input("Valeur", key="new_val", placeholder="Entrez une valeur…")

    if st.session_state.conditions:
        new_join = st.radio("Lier avec", ["ET", "OU"], horizontal=True, key="new_join")
    else:
        new_join = "ET"

    ba, bc = st.columns(2)
    with ba:
        if st.button("➕ Ajouter", use_container_width=True):
            if new_val.strip():
                st.session_state.conditions.append(
                    {"column": new_col, "operator": new_op,
                     "value": new_val.strip(), "join_op": new_join}
                )
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
        st.markdown(
            "<p style='color:#4a5170;font-style:italic;font-size:.9rem;'>Aucune condition.</p>",
            unsafe_allow_html=True,
        )
    else:
        # Flat table grouped by column
        groups = OrderedDict()
        for i, cond in enumerate(st.session_state.conditions):
            groups.setdefault(cond["column"], []).append((i, cond))

        for col_name, entries in groups.items():
            st.markdown(
                f"<div class='col-badge'>📌 {col_name}</div>"
                f"<span style='color:#4a5170;font-size:.75rem;margin-left:8px;'>"
                f"{len(entries)} filtre(s)</span>",
                unsafe_allow_html=True,
            )
            h1, h2, h3 = st.columns([3, 3, 1])
            for h, lbl in zip([h1,h2,h3], ["Opérateur","Valeur",""]):
                h.markdown(
                    f"<span style='color:#6366f1;font-size:.72rem;font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:1px;"
                    f"font-family:JetBrains Mono,monospace;'>{lbl}</span>",
                    unsafe_allow_html=True,
                )
            st.markdown("<div class='tbl-divider'></div>", unsafe_allow_html=True)

            for row_idx, (gi, cond) in enumerate(entries):
                ef = st.session_state.editing.get(gi)

                # Join-op toggle between conditions
                if gi > 0:
                    jop = cond["join_op"]
                    jc, _ = st.columns([4, 7])
                    with jc:
                        if st.button(f"⇅ {jop}", key=f"join_{gi}",
                                     help="Basculer ET / OU"):
                            st.session_state.conditions[gi]["join_op"] = \
                                "OU" if jop == "ET" else "ET"
                            st.rerun()

                rc1, rc2, rc3 = st.columns([3, 3, 1])

                with rc1:   # operator
                    if ef == "operator":
                        sel = st.selectbox("op", OP_LABELS,
                            index=OP_LABELS.index(cond["operator"]),
                            key=f"eop_{gi}", label_visibility="collapsed")
                        st.session_state.conditions[gi]["operator"] = sel
                        if st.button("✓", key=f"cop_{gi}"):
                            st.session_state.editing.pop(gi, None); st.rerun()
                    else:
                        st.markdown(
                            f"<span style='color:#fbbf24;font-size:.83rem;'>{cond['operator']}</span>",
                            unsafe_allow_html=True,
                        )
                        if st.button("✏️", key=f"bop_{gi}", help="Modifier"):
                            st.session_state.editing[gi] = "operator"; st.rerun()

                with rc2:   # value
                    if ef == "value":
                        nv = st.text_input("val", value=cond["value"],
                            key=f"eval_{gi}", label_visibility="collapsed")
                        st.session_state.conditions[gi]["value"] = nv
                        if st.button("✓", key=f"cval_{gi}"):
                            st.session_state.editing.pop(gi, None); st.rerun()
                    else:
                        st.markdown(
                            f"<span style='color:#86efac;font-size:.83rem;"
                            f"font-family:JetBrains Mono,monospace;'>«{cond['value']}»</span>",
                            unsafe_allow_html=True,
                        )
                        if st.button("✏️", key=f"bval_{gi}", help="Modifier"):
                            st.session_state.editing[gi] = "value"; st.rerun()

                with rc3:   # delete
                    if st.button("✕", key=f"del_{gi}"):
                        st.session_state.conditions.pop(gi)
                        st.session_state.editing.pop(gi, None)
                        st.rerun()

                if row_idx < len(entries) - 1:
                    st.markdown("<div class='tbl-divider'></div>", unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)

    if st.button("▶ Exécuter la requête", use_container_width=True, type="primary"):
        conn = get_connection()
        q, params = build_query(st.session_state.selected_table, st.session_state.conditions)
        try:
            st.session_state.results = pd.read_sql_query(q, conn, params=params)
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

# ══ RIGHT — tree + SQL ════════════════════════════════════════════════════════
with col_right:
    st.markdown("### 🌳 Arbre de décision")
    st.caption("Cliquez sur un nœud ET / OU pour le basculer directement dans l'arbre.")
    render_tree(st.session_state.conditions, st.session_state.selected_table)

    st.markdown("### 🧾 Requête SQL générée")
    st.caption("Les parenthèses reflètent l'imbrication de l'arbre.")
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
