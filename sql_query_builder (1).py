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
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.stApp{background:#0d0f14;color:#e8eaf0;}
h1{font-family:'Syne',sans-serif!important;font-weight:800!important;font-size:2.2rem!important;
   background:linear-gradient(135deg,#64b5f6,#a78bfa,#f472b6);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px;}
h2,h3{font-family:'Syne',sans-serif!important;font-weight:700!important;color:#c8cad6!important;}
.stButton>button{font-family:'Syne',sans-serif!important;font-weight:600!important;
   background:linear-gradient(135deg,#3b82f6,#7c3aed)!important;color:white!important;
   border:none!important;border-radius:8px!important;transition:all .2s!important;}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 6px 20px rgba(99,102,241,.4)!important;}
.stSelectbox>div>div,.stTextInput>div>div>input,
.stNumberInput>div>div>input{background:#1a1d27!important;border:1px solid #2a2d3e!important;
   border-radius:8px!important;color:#e8eaf0!important;font-family:'Syne',sans-serif!important;}
.sql-display{background:#0a0c12;border:1px solid #1e2130;border-left:3px solid #6366f1;
   border-radius:10px;padding:18px 22px;font-family:'JetBrains Mono',monospace;
   font-size:.85rem;color:#a5f3fc;line-height:1.8;white-space:pre-wrap;margin:8px 0;}
.tree-wrap{background:#0f111a;border:1px solid #1e2130;border-radius:12px;padding:18px 18px 12px;margin:10px 0;}
.t-root{display:inline-block;background:linear-gradient(135deg,#312e81,#4c1d95);color:#c4b5fd;
   padding:6px 16px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-weight:600;font-size:.85rem;}
.t-leaf{background:#1e293b;border:1px solid #334155;border-radius:6px;
   padding:4px 12px;font-family:'JetBrains Mono',monospace;font-size:.8rem;display:inline-block;line-height:1.8;}
[data-testid="stMetric"]{background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;}
[data-testid="stMetricValue"]{color:#6366f1!important;font-family:'JetBrains Mono',monospace!important;font-weight:700!important;}
[data-testid="stDataFrame"]{border:1px solid #1e2130;border-radius:10px;overflow:hidden;}
[data-testid="stExpander"]{background:#13151d!important;border:1px solid #1e2130!important;border-radius:10px!important;}
hr{border-color:#1e2130!important;}
::-webkit-scrollbar{width:6px;height:6px;}
::-webkit-scrollbar-track{background:#0d0f14;}
::-webkit-scrollbar-thumb{background:#2a2d3e;border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#6366f1;}
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

ENRICH = {
    "clients": {
        "other": "voyages",
        "count_sql": "SELECT COUNT(*) AS total FROM voyages v WHERE v.client_id IN (SELECT id FROM clients WHERE {where})",
        "select_sql": """
            SELECT c.id, c.nom, c.prenom, c.email, c.telephone, c.ville, c.pays,
                   c.date_inscription, c.statut,
                   v.id AS voyage_id, v.destination, v.pays_destination, v.continent,
                   v.date_depart, v.date_retour, v.duree_jours, v.type_voyage,
                   v.transport, v.hotel, v.budget, v.statut AS statut_voyage, v.note
            FROM clients c JOIN voyages v ON c.id = v.client_id
            WHERE c.id IN (SELECT id FROM clients WHERE {where})""",
    },
    "voyages": {
        "other": "clients",
        "count_sql": "SELECT COUNT(*) AS total FROM clients c WHERE c.id IN (SELECT client_id FROM voyages WHERE {where})",
        "select_sql": """
            SELECT v.id, v.client_id, v.destination, v.pays_destination, v.continent,
                   v.date_depart, v.date_retour, v.duree_jours, v.type_voyage,
                   v.transport, v.hotel, v.budget, v.statut, v.note,
                   c.nom AS client_nom, c.prenom AS client_prenom, c.email AS client_email,
                   c.telephone AS client_telephone, c.ville AS client_ville,
                   c.pays AS client_pays, c.date_inscription, c.statut AS client_statut
            FROM voyages v JOIN clients c ON v.client_id = c.id
            WHERE v.id IN (SELECT id FROM voyages WHERE {where})""",
    },
}

SIMPLIFIED_COLS = {
    "clients": [
        ("nom","Nom de famille"),("prenom","Prénom"),("email","Email"),
        ("ville","Ville"),("pays","Pays"),
        ("date_inscription","Date d'inscription"),("statut","Statut (actif / inactif)"),
    ],
    "voyages": [
        ("destination","Destination"),("pays_destination","Pays de destination"),
        ("continent","Continent"),("date_depart","Date de départ"),
        ("date_retour","Date de retour"),("type_voyage","Type de voyage"),
        ("transport","Moyen de transport"),("budget","Budget (€)"),
        ("statut","Statut du voyage"),("note","Note (1 – 5)"),
    ],
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

MONTHS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin",
             "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]

def is_date_col(col: str) -> bool:  return "date" in col.lower()
def build_date_value(y, m, d) -> str:
    if m == 0:  return f"{y:04d}"
    if d == 0:  return f"{y:04d}-{m:02d}"
    return f"{y:04d}-{m:02d}-{d:02d}"

# ── State ──────────────────────────────────────────────────────────────────────
for k, v in [("conditions",[]),("selected_table","clients"),
             ("results",None),("enrich_count",None),
             ("last_where",""),("last_params",[]),("editing",{}),
             ("_selected_row_idx",None),("expert_mode",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# ENRICH HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def compute_enrich_count(table, where, params):
    sql = ENRICH[table]["count_sql"].format(where=where)
    try:
        r = pd.read_sql_query(sql, get_connection(), params=params)
        return int(r["total"].iloc[0])
    except Exception: return None

def run_enrich_query(table, where, params):
    sql = ENRICH[table]["select_sql"].format(where=where)
    return pd.read_sql_query(sql, get_connection(), params=params)

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

def _sql_from_tree(node, conditions, params, display):
    if node["type"] == "leaf":
        c = conditions[node["idx"]]
        if c.get("is_bulk"):
            sym, fn = OPERATORS[c["operator"]]
            if display: clauses = [f"{c['column']} {sym} '{fn(v)}'" for v in c["values"]]
            else:
                clauses = []
                for v in c["values"]:
                    clauses.append(f"{c['column']} {sym} ?"); params.append(fn(v))
            return "(" + " OR ".join(clauses) + ")"
        sym, fn = OPERATORS[c["operator"]]; val = fn(c["value"])
        if display: return f"{c['column']} {sym} '{val}'"
        params.append(val); return f"{c['column']} {sym} ?"
    sql_op = "AND" if node["op"] == "ET" else "OR"
    L = _sql_from_tree(node["left"],  conditions, params, display)
    R = _sql_from_tree(node["right"], conditions, params, display)
    return f"({L} {sql_op} {R})"

def build_where(conditions, display=False):
    if not conditions: return "1=1", []
    params = []
    where  = _sql_from_tree(build_tree(conditions), conditions, params, display)
    return where, params

def build_query(table, conditions):
    where, params = build_where(conditions)
    if where == "1=1": return f"SELECT *\nFROM {table}", params
    return f"SELECT *\nFROM {table}\nWHERE {where}", params

def build_query_display(table, conditions):
    where, _ = build_where(conditions, display=True)
    if where == "1=1": return f"SELECT *\nFROM {table}"
    return f"SELECT *\nFROM {table}\nWHERE {where}"

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

def _leaf_html(conditions, idx):
    c = conditions[idx]
    display_col = c.get("label") or c["column"]
    if c.get("is_date"):
        return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{display_col}</b> "
                f"<span style='color:#fbbf24;'>en</span> "
                f"<span style='color:#86efac;'>{_date_label(c['value'])}</span></span>")
    if c.get("is_bulk"):
        values  = c["values"]; n = len(values)
        op_str  = OP_NATURAL.get(c["operator"], c["operator"])
        preview = " · ".join(f"«{v}»" for v in values[:3])
        suffix  = f" <span style='color:#64748b;font-size:.75rem;'>+{n-3} autres</span>" if n > 3 else ""
        return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{display_col}</b> "
                f"<span style='color:#fbbf24;'>{op_str}</span> "
                f"<span style='color:#86efac;'>[{preview}{suffix}]</span></span>")
    op_str = OP_NATURAL.get(c["operator"], c["operator"])
    return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{display_col}</b> "
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
            if ph:
                w = max(prefix_len * 0.135, 0.35)
                ca, cb = st.columns([w, max(9 - w, 1)])
                ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>", unsafe_allow_html=True)
                with cb: _render_leaf_editor(conditions, idx)
            else: _render_leaf_editor(conditions, idx)
        else:
            leaf_h = _leaf_html(conditions, idx)
            if ph:
                w = max(prefix_len * 0.135, 0.35)
                ca, cb, cc = st.columns([w, max(8.4 - w, 1), 0.6])
                ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>", unsafe_allow_html=True)
                cb.markdown(f"<div style='padding-top:6px;'>{leaf_h}</div>", unsafe_allow_html=True)
                with cc: _small_edit_button(idx)
            else:
                c1, c2 = st.columns([9.4, 0.6])
                c1.markdown(f"<div style='padding-top:2px;'>{leaf_h}</div>", unsafe_allow_html=True)
                with c2: _small_edit_button(idx)
    else:
        op, right_idx = node["op"], node["right"]["idx"]
        if ph:
            w = max(prefix_len * 0.135, 0.35)
            ca, cb = st.columns([w, max(9 - w, 1)])
            ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>", unsafe_allow_html=True)
            with cb: _branch_button(op, right_idx)
        else: _branch_button(op, right_idx)
        new_pfx = (prefix_parts if is_root else
                   prefix_parts + [("│   ", connector_color)] if not is_last else
                   prefix_parts + [("    ", connector_color)])
        _render_node(node["left"],  conditions, new_pfx, is_last=False, parent_op=op)
        _render_node(node["right"], conditions, new_pfx, is_last=True,  parent_op=op)

def _small_edit_button(idx):
    m = f"editbtn-{idx}"
    st.markdown(
        f'<div id="{m}"></div><style>'
        f"div.element-container:has(#{m}) + div.element-container button{{"
        f"background:transparent!important;color:#475569!important;"
        f"border:1px solid #2a2d3e!important;border-radius:4px!important;"
        f"font-size:.7rem!important;padding:2px 6px!important;min-height:0!important;width:100%!important;}}"
        f"div.element-container:has(#{m}) + div.element-container button:hover{{"
        f"color:#94a3b8!important;border-color:#475569!important;background:#1a1d27!important;"
        f"transform:none!important;box-shadow:none!important;}}</style>", unsafe_allow_html=True)
    if st.button("✏️", key=f"editbtn_{idx}", help="Modifier ou supprimer"):
        st.session_state.editing[idx] = "leaf"; st.rerun()

def _render_leaf_editor(conditions, idx):
    cond = conditions[idx]
    is_date = cond.get("is_date", False)
    is_bulk = cond.get("is_bulk", False)
    if is_bulk:
        current_text = "\n".join(cond["values"])
        st.text_area("Valeurs", value=current_text, key=f"ev_{idx}", height=110,
                     label_visibility="collapsed")
        e1, e2, e3 = st.columns([2, 1, 1])
        with e1:
            st.selectbox("Op", OP_LABELS, index=OP_LABELS.index(cond["operator"]),
                         key=f"eop_{idx}", label_visibility="collapsed")
        with e2:
            if st.button("✓", key=f"eok_{idx}", use_container_width=True):
                raw = st.session_state.get(f"ev_{idx}", current_text)
                values = [v.strip() for v in re.split(r"[,\n]", raw) if v.strip()]
                if values:
                    conditions[idx]["values"]   = values
                    conditions[idx]["value"]    = ", ".join(values)
                    conditions[idx]["operator"] = st.session_state.get(f"eop_{idx}", cond["operator"])
                    st.session_state.editing.pop(idx, None); st.rerun()
                else: st.warning("Entrez au moins une valeur.")
        with e3:
            if st.button("🗑", key=f"edel_{idx}", use_container_width=True):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx, None); st.rerun()
    elif is_date:
        parts = cond["value"].split("-")
        cur_y = int(parts[0]) if len(parts)>=1 else 2023
        cur_m = int(parts[1]) if len(parts)>=2 else 0
        cur_d = int(parts[2]) if len(parts)>=3 else 0
        e1,e2,e3,e4,e5 = st.columns([1.5,1,1,0.5,0.5])
        e1.number_input("Année",1900,2100,cur_y,key=f"ey_{idx}",label_visibility="collapsed")
        e2.number_input("Mois",0,12,cur_m,key=f"em_{idx}",label_visibility="collapsed")
        e3.number_input("Jour",0,31,cur_d,key=f"ed_{idx}",label_visibility="collapsed")
        with e4:
            if st.button("✓",key=f"eok_{idx}",help="Valider"):
                conditions[idx]["value"] = build_date_value(
                    int(st.session_state.get(f"ey_{idx}",cur_y)),
                    int(st.session_state.get(f"em_{idx}",cur_m)),
                    int(st.session_state.get(f"ed_{idx}",cur_d)))
                st.session_state.editing.pop(idx,None); st.rerun()
        with e5:
            if st.button("🗑",key=f"edel_{idx}",help="Supprimer"):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx,None); st.rerun()
    else:
        e1,e2,e3,e4,e5 = st.columns([2.2,1.8,0.45,0.45,0.45])
        e1.text_input("Valeur",value=cond["value"],key=f"ev_{idx}",label_visibility="collapsed")
        e2.selectbox("Op",OP_LABELS,index=OP_LABELS.index(cond["operator"]),
                     key=f"eop_{idx}",label_visibility="collapsed")
        with e3:
            if st.button("✓",key=f"eok_{idx}",help="Valider"):
                conditions[idx]["value"]    = st.session_state.get(f"ev_{idx}",  cond["value"])
                conditions[idx]["operator"] = st.session_state.get(f"eop_{idx}", cond["operator"])
                st.session_state.editing.pop(idx,None); st.rerun()
        with e4:
            if st.button("🗑",key=f"edel_{idx}",help="Supprimer"):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx,None); st.rerun()
        with e5:
            if st.button("✗",key=f"ecancel_{idx}",help="Annuler"):
                st.session_state.editing.pop(idx,None); st.rerun()

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
        f"filter:brightness(1.3)!important;transform:translateY(-1px)!important;}}</style>",
        unsafe_allow_html=True)
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
    tree = build_tree(conditions)
    if tree is None:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>Aucune condition.</p>",
                    unsafe_allow_html=True); return
    _render_node(tree, conditions, prefix_parts=[], is_last=True, is_root=True, parent_op=None)

# ══════════════════════════════════════════════════════════════════════════════
# PANEL INLINE — sélection de ligne → filtrage
# BUG FIX : fermer le panel nettoie aussi la sélection du dataframe (result_df)
# pour éviter que le panel ne se rouvre lors du prochain "Exécuter la requête"
# ══════════════════════════════════════════════════════════════════════════════
def _clear_row_selection():
    """Efface la sélection du dataframe ET l'index de ligne sélectionnée."""
    st.session_state["_selected_row_idx"] = None
    # Nettoie la sélection persistée dans le widget dataframe
    st.session_state["result_df"] = {"selection": {"rows": [], "columns": []}}

def render_row_panel(df, row_idx):
    row  = df.iloc[row_idx]
    cols = list(df.columns)
    col_key = f"panel_col_{row_idx}"
    if col_key not in st.session_state:
        st.session_state[col_key] = cols[0]

    st.markdown(
        "<div style='background:#13151d;border:1px solid #6366f1;"
        "border-radius:12px;padding:16px 20px;margin-top:12px;'>",
        unsafe_allow_html=True)

    h1, h2 = st.columns([8, 1])
    with h1:
        st.markdown(f"<span style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                    f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Ligne {row_idx} sélectionnée</span>",
                    unsafe_allow_html=True)
    with h2:
        if st.button("✕", key="panel_close", help="Fermer"):
            _clear_row_selection()   # ← BUG FIX
            st.rerun()

    # Badges des valeurs
    badge_html = ""
    for c in cols:
        val = row[c]
        is_active = (c == st.session_state.get(col_key))
        bg = "#1e3a5f" if is_active else "#1e293b"
        brd = "#6366f1" if is_active else "#334155"
        clr = "#a5f3fc" if is_active else "#94a3b8"
        badge_html += (f"<span style='background:{bg};border:1px solid {brd};border-radius:6px;"
                       f"padding:3px 10px;font-size:.75rem;font-family:JetBrains Mono,monospace;'>"
                       f"<span style='color:{clr};font-weight:600;'>{c}</span>"
                       f"<span style='color:#64748b;'> : </span>"
                       f"<span style='color:#e2e8f0;'>{val}</span></span> ")
    st.markdown(badge_html, unsafe_allow_html=True)

    pc1, pc2, pc3 = st.columns([2, 2, 3])
    with pc1:
        col_options = [f"{c} : {row[c]}" for c in cols]
        cur_label   = f"{st.session_state[col_key]} : {row[st.session_state[col_key]]}"
        sel_label   = st.selectbox("Colonne", col_options,
                                   index=col_options.index(cur_label) if cur_label in col_options else 0,
                                   key=f"panel_col_sel_{row_idx}", label_visibility="collapsed")
        sel_col = sel_label.split(" : ")[0]
        st.session_state[col_key] = sel_col
    with pc2:
        sel_op = st.selectbox("Opérateur", OP_LABELS, key=f"panel_op_{row_idx}",
                              label_visibility="collapsed")
    with pc3:
        tables_with_col = [t for t, tc in TABLES.items() if sel_col in tc]
        sel_table = st.selectbox("Table", tables_with_col,
                                 index=tables_with_col.index(st.session_state.selected_table)
                                       if st.session_state.selected_table in tables_with_col else 0,
                                 key=f"panel_tbl_{row_idx}", label_visibility="collapsed")

    sel_val = str(row[sel_col])
    sym, fn = OPERATORS[sel_op]; tv = fn(sel_val)
    st.markdown(
        f"<div style='background:#0a0c12;border-left:3px solid #6366f1;"
        f"border-radius:6px;padding:7px 12px;font-family:JetBrains Mono,monospace;"
        f"font-size:.78rem;color:#a5f3fc;margin:8px 0;'>"
        f"SELECT * FROM <b>{sel_table}</b> WHERE <b>{sel_col}</b>"
        f" <span style='color:#fbbf24'>{sym}</span>"
        f" <span style='color:#86efac'>'{tv}'</span></div>",
        unsafe_allow_html=True)

    pb1, pb2, pb3 = st.columns(3)
    with pb1:
        if st.button("▶ Lancer la requête", key="panel_run", width="stretch", type="primary"):
            conn = get_connection()
            q    = f"SELECT * FROM {sel_table} WHERE {sel_col} {sym} ?"
            try:
                st.session_state.results        = pd.read_sql_query(q, conn, params=[tv])
                st.session_state.selected_table = sel_table
                st.session_state.conditions     = [{"column":sel_col,"operator":sel_op,
                                                    "value":sel_val,"join_op":"ET",
                                                    "is_date":False,"is_bulk":False}]
                where, params = build_where(st.session_state.conditions)
                st.session_state.last_where    = where
                st.session_state.last_params   = params
                st.session_state.enrich_count  = compute_enrich_count(sel_table, where, params)
                _clear_row_selection()
            except Exception as e: st.error(f"Erreur SQL : {e}")
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
                unsafe_allow_html=True)
        else:
            if st.button("🔢 Compter", key="panel_count", width="stretch"):
                conn = get_connection()
                q    = f"SELECT COUNT(*) AS total FROM {sel_table} WHERE {sel_col} {sym} ?"
                try:
                    r = pd.read_sql_query(q, conn, params=[tv])
                    st.session_state[count_key] = int(r["total"].iloc[0])
                except Exception as e: st.error(f"Erreur : {e}")
                st.rerun()
    with pb3:
        join = "ET"
        if st.session_state.conditions:
            join = st.radio("Lier", ["ET","OU"], horizontal=True,
                            key=f"panel_join_{row_idx}", label_visibility="collapsed")
        if st.button("➕ Ajouter à l'arbre", key="panel_add", width="stretch"):
            st.session_state.conditions.append({
                "column":sel_col,"operator":sel_op,"value":sel_val,
                "join_op":join,"is_date":False,"is_bulk":False})
            _clear_row_selection()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# 🔍 SQL Query Builder")
st.markdown("<p style='color:#6b7280;margin-top:-14px;margin-bottom:20px;'>"
            "Construisez vos requêtes SQL visuellement, sans écrire une ligne de code.</p>",
            unsafe_allow_html=True)

# ── Table selector ─────────────────────────────────────────────────────────────
st.markdown("<span style='color:#94a3b8;font-size:.78rem;text-transform:uppercase;"
            "letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Table source</span>",
            unsafe_allow_html=True)
t_cols = st.columns(len(TABLES))
for i, tname in enumerate(TABLES):
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
        st.rerun()

st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
current_table = st.session_state.selected_table
current_cols  = TABLES[current_table]

# ── Add condition ──────────────────────────────────────────────────────────────
hdr_l, hdr_r = st.columns([5, 3])
with hdr_l: st.markdown("### ➕ Ajouter une condition")
with hdr_r:
    st.markdown("<div style='padding-top:18px;'>", unsafe_allow_html=True)
    expert_mode = st.toggle("🔧 Mode expert", key="expert_mode",
        help="**Mode simplifié** : colonnes essentielles avec libellés clairs\n\n"
             "**Mode expert** : toutes les colonnes techniques disponibles")
    st.markdown("</div>", unsafe_allow_html=True)

if expert_mode:
    col_options = current_cols
    col_key     = f"new_col_expert_{current_table}"
else:
    simp        = SIMPLIFIED_COLS.get(current_table, [(c,c) for c in current_cols])
    col_options = [label for _, label in simp]
    col_map     = {label: col for col, label in simp}
    col_key     = f"new_col_simple_{current_table}"

fa, fb, fc, fd = st.columns([2, 2, 3, 1])
with fa:
    selected = st.selectbox("Colonne", col_options, key=col_key, label_visibility="collapsed")
    new_col       = selected if expert_mode else col_map.get(selected, selected)
    new_col_label = selected
with fb:
    is_date = is_date_col(new_col)
    if is_date:
        st.markdown("<span style='color:#a78bfa;font-size:.78rem;'>📅 Colonne date</span>",
                    unsafe_allow_html=True)
    else:
        new_op = st.selectbox("Opérateur", OP_LABELS, key="new_op", label_visibility="collapsed")
with fc:
    if is_date:
        d1,d2,d3 = st.columns(3)
        new_year  = d1.number_input("Année *",1900,2100,2023,1,key="new_year")
        new_month = d2.number_input("Mois",0,12,0,1,key="new_month",help="0 = non précisé")
        new_day   = d3.number_input("Jour",0,31,0,1,key="new_day",help="0 = non précisé")
    else:
        st.text_area("Valeur(s)", key="new_val",
                     placeholder="Une valeur, ou plusieurs séparées par des virgules / sauts de ligne",
                     height=80, label_visibility="collapsed")
with fd:
    new_join = (st.radio("Lier",["ET","OU"],horizontal=False,key="new_join",label_visibility="collapsed")
                if st.session_state.conditions else "ET")

btn_a, btn_b = st.columns([3, 1])
with btn_a:
    if st.button("➕ Ajouter la condition", width="stretch"):
        base = {"column":new_col,"label":new_col_label,"join_op":new_join,
                "is_date":is_date,"is_bulk":False}
        if is_date:
            st.session_state.conditions.append({**base,"operator":"Commence par",
                "value":build_date_value(int(new_year),int(new_month),int(new_day))})
            st.rerun()
        else:
            raw    = st.session_state.get("new_val","")
            values = [v.strip() for v in re.split(r"[,\n]",raw) if v.strip()]
            if not values: st.warning("Veuillez entrer au moins une valeur.")
            elif len(values)==1:
                st.session_state.conditions.append({**base,"operator":new_op,"value":values[0]})
                st.rerun()
            else:
                st.session_state.conditions.append({**base,"operator":new_op,"is_bulk":True,
                    "value":", ".join(values),"values":values})
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
    render_tree(st.session_state.conditions, current_table)
with col_sql:
    with st.expander("🧾 Voir la requête SQL générée", expanded=False):
        st.markdown(f"<div class='sql-display'>"
                    f"{build_query_display(current_table, st.session_state.conditions)}"
                    f"</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    if st.button("▶ Exécuter la requête", width="stretch", type="primary"):
        # BUG FIX : fermer le panel ouvert avant d'exécuter une nouvelle requête
        _clear_row_selection()
        conn = get_connection()
        q, params = build_query(current_table, st.session_state.conditions)
        try:
            st.session_state.results = pd.read_sql_query(q, conn, params=params)
            where, wparams = build_where(st.session_state.conditions)
            st.session_state.last_where   = where
            st.session_state.last_params  = wparams
            st.session_state.enrich_count = compute_enrich_count(current_table, where, wparams)
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.results is not None:
    df  = st.session_state.results
    cnt = st.session_state.enrich_count

    st.markdown("---")
    st.markdown("### 📊 Résultats")

    m1, m2, m3 = st.columns(3)
    m1.metric("Lignes", len(df))
    m2.metric("Colonnes", len(df.columns))
    m3.metric("Conditions", len(st.session_state.conditions))

    if len(df) == 0:
        st.info("Aucun résultat ne correspond à vos critères.")
    else:
        has_nom       = "nom"         in df.columns
        has_prenom    = "prenom"      in df.columns
        has_dest      = "destination" in df.columns
        has_depart    = "date_depart" in df.columns
        has_budget    = "budget"      in df.columns
        has_note      = "note"        in df.columns
        has_continent = "continent"   in df.columns
        has_type      = "type_voyage" in df.columns
        has_duree     = "duree_jours" in df.columns
        has_statut_v  = "statut_voyage" in df.columns
        has_client_nom= "client_nom"  in df.columns
        has_ville     = "ville"       in df.columns
        has_client_id = "client_id"   in df.columns

        CONT_COLORS = {"Asie":"#f59e0b","Europe":"#3b82f6","Amérique":"#10b981",
                       "Afrique":"#ef4444","Océanie":"#8b5cf6"}
        TYPE_COLORS = {"Tourisme":"#3b82f6","Affaires":"#8b5cf6","Détente":"#10b981",
                       "Lune de miel":"#f472b6","Safari":"#f59e0b","Aventure":"#ef4444",
                       "Luxe":"#fbbf24","City Break":"#06b6d4","Culturel":"#a78bfa",
                       "Plage":"#22d3ee","Romantique":"#fb7185"}

        # ── Blink animation ────────────────────────────────────────────────────
        _hl_until   = st.session_state.get("_enrich_hl_until", 0)
        _blink_tabs = st.session_state.get("_blink_tabs", set())
        if time.time() < _hl_until and _blink_tabs:
            selectors = ", ".join(
                f"div[data-testid='stTabsTabList'] button[role='tab']:nth-child({n})"
                for n in sorted(_blink_tabs))
            st.markdown(f"""<style>
@keyframes tab-pulse {{
    0%,100% {{ color:inherit; text-shadow:none; }}
    40% {{ color:#4ade80!important; text-shadow:0 0 8px #4ade80,0 0 16px #16a34a; }}
}}
{selectors} {{ animation:tab-pulse 0.9s ease-in-out infinite; }}
div[data-testid="stTabsTabList"] button[role="tab"][aria-selected="true"] {{
    animation:none!important; color:inherit!important; }}
</style>""", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs(["📋 Grille","👤 Fiches","🗓 Timeline","📈 Statistiques"])

        # ── TAB 1 ──────────────────────────────────────────────────────────────
        with tab1:
            st.caption("💡 Cliquez sur une ligne pour explorer ses valeurs et créer un filtre.")
            event = st.dataframe(df, width="stretch", hide_index=True,
                                 on_select="rerun", selection_mode="single-row", key="result_df")
            sel    = event.selection if hasattr(event, "selection") else {}
            rows_s = sel.get("rows", [])
            if rows_s:
                st.session_state["_selected_row_idx"] = int(rows_s[0])
            elif not rows_s and st.session_state.get("_selected_row_idx") is not None:
                st.session_state["_selected_row_idx"] = None
            st.download_button("⬇ Télécharger CSV",
                df.to_csv(index=False).encode("utf-8"),
                f"resultats_{current_table}.csv", "text/csv")

        # Panel — hors contexte tab
        row_idx_panel = st.session_state.get("_selected_row_idx")
        if row_idx_panel is not None and row_idx_panel < len(df):
            render_row_panel(df, row_idx_panel)

        # ── TAB 2 : Fiches ─────────────────────────────────────────────────────
        with tab2:
            if has_nom and has_prenom and has_dest:
                for client_id, group in df.groupby("id", sort=False):
                    row0 = group.iloc[0]
                    initials = (str(row0.get("prenom","?"))[:1]+str(row0.get("nom","?"))[:1]).upper()
                    ville_txt  = row0.get("ville",""); stat_txt = row0.get("statut","")
                    stat_color = "#4ade80" if stat_txt=="actif" else "#f87171"
                    n_v = len(group); bgt_tot = group["budget"].sum() if has_budget else 0
                    card = (f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:12px;"
                            f"padding:16px 20px;margin-bottom:16px;'>"
                            f"<div style='display:flex;align-items:center;gap:14px;margin-bottom:12px;'>"
                            f"<div style='width:44px;height:44px;border-radius:50%;"
                            f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                            f"display:flex;align-items:center;justify-content:center;"
                            f"font-weight:700;font-size:1rem;color:white;flex-shrink:0;'>{initials}</div>"
                            f"<div><div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>"
                            f"{row0.get('prenom','')} {row0.get('nom','')}</div>"
                            f"<div style='color:#64748b;font-size:.82rem;'>{ville_txt} · "
                            f"<span style='color:{stat_color};'>{stat_txt}</span></div></div>"
                            f"<div style='margin-left:auto;text-align:right;'>"
                            f"<div style='color:#a78bfa;font-size:1.1rem;font-weight:700;font-family:JetBrains Mono,monospace;'>{n_v}</div>"
                            f"<div style='color:#64748b;font-size:.72rem;'>voyage{'s' if n_v>1 else ''}</div></div></div>")
                    for _, vrow in group.iterrows():
                        dest = vrow.get("destination",""); cont = vrow.get("continent","")
                        cont_col = CONT_COLORS.get(cont,"#6b7280"); dep = str(vrow.get("date_depart",""))[:10]
                        ret = str(vrow.get("date_retour",""))[:10]; bgt = vrow.get("budget",0)
                        note_v = vrow.get("note",None); stars = ("⭐"*int(note_v)) if note_v and not pd.isna(note_v) else "—"
                        tv = vrow.get("type_voyage",""); tv_col = TYPE_COLORS.get(tv,"#6b7280")
                        card += (f"<div style='display:flex;align-items:center;gap:10px;padding:7px 0;border-top:1px solid #1e2130;'>"
                                 f"<div style='width:3px;height:32px;border-radius:2px;background:{cont_col};flex-shrink:0;'></div>"
                                 f"<div style='flex:1;'><span style='color:#e8eaf0;font-weight:600;font-size:.85rem;'>{dest}</span>"
                                 f"<span style='color:#475569;font-size:.75rem;margin-left:8px;'>{dep} → {ret}</span></div>"
                                 f"<span style='background:{tv_col}22;color:{tv_col};font-size:.7rem;padding:2px 8px;border-radius:10px;'>{tv}</span>"
                                 f"<span style='color:#fbbf24;font-size:.78rem;font-family:JetBrains Mono,monospace;margin-left:4px;'>{int(bgt):,}€</span>"
                                 f"<span style='font-size:.75rem;margin-left:6px;'>{stars}</span></div>")
                    card += "</div>"
                    st.markdown(card, unsafe_allow_html=True)
            elif has_nom and has_prenom:
                cols_g = st.columns(2)
                for i,(_, row) in enumerate(df.iterrows()):
                    initials = (str(row.get("prenom","?"))[:1]+str(row.get("nom","?"))[:1]).upper()
                    stat_txt = str(row.get("statut","")); stat_color="#4ade80" if stat_txt=="actif" else "#f87171"
                    cols_g[i%2].markdown(
                        f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:12px;"
                        f"padding:16px 18px;margin-bottom:12px;'>"
                        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>"
                        f"<div style='width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;font-weight:700;color:white;'>{initials}</div>"
                        f"<div><div style='font-weight:700;color:#e8eaf0;'>{row.get('prenom','')} {row.get('nom','')}</div>"
                        f"<div style='font-size:.78rem;color:#64748b;'>{row.get('ville','')} · <span style='color:{stat_color};'>{stat_txt}</span></div></div></div>"
                        f"<div style='font-size:.78rem;color:#64748b;line-height:1.8;'>"
                        f"📧 {row.get('email','')}<br>📞 {row.get('telephone','')}<br>"
                        f"📅 Membre depuis {str(row.get('date_inscription',''))[:10]}</div></div>",
                        unsafe_allow_html=True)
            elif has_dest:
                cols_g = st.columns(2)
                for i,(_, row) in enumerate(df.iterrows()):
                    dest=row.get("destination",""); pays=row.get("pays_destination","")
                    cont=row.get("continent",""); cont_col=CONT_COLORS.get(cont,"#6b7280")
                    dep=str(row.get("date_depart",""))[:10]; ret=str(row.get("date_retour",""))[:10]
                    duree=row.get("duree_jours",""); bgt=row.get("budget",0)
                    hotel=row.get("hotel",""); tv=row.get("type_voyage",""); tv_col=TYPE_COLORS.get(tv,"#6b7280")
                    note_v=row.get("note",None); stars=("⭐"*int(note_v)) if note_v and not pd.isna(note_v) else "—"
                    cnom=""
                    if has_client_nom: cnom=f"{row.get('client_prenom','')} {row.get('client_nom','')}".strip()
                    elif has_client_id: cnom=f"Client #{int(row.get('client_id',0))}"
                    cols_g[i%2].markdown(
                        f"<div style='background:#13151d;border:1px solid #1e2130;border-top:3px solid {cont_col};"
                        f"border-radius:12px;padding:16px 18px;margin-bottom:12px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:start;'>"
                        f"<div><div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>{dest}</div>"
                        f"<div style='font-size:.78rem;color:#64748b;'>{pays} · <span style='color:{cont_col};'>{cont}</span></div></div>"
                        f"<span style='background:{tv_col}22;color:{tv_col};font-size:.7rem;padding:3px 10px;border-radius:10px;'>{tv}</span></div>"
                        f"<div style='margin:10px 0;font-size:.8rem;color:#94a3b8;'>"
                        f"📅 {dep} → {ret}{'  ·  🕒 '+str(duree)+'j' if duree else ''}{'  ·  '+cnom if cnom else ''}</div>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        f"<span style='color:#64748b;font-size:.78rem;'>🏨 {hotel}</span>"
                        f"<div style='text-align:right;'><div style='color:#4ade80;font-weight:700;font-family:JetBrains Mono,monospace;'>{int(bgt):,}€</div>"
                        f"<div style='font-size:.75rem;'>{stars}</div></div></div></div>",
                        unsafe_allow_html=True)
            else: st.info("Aucune vue fiche disponible pour ces colonnes.")

        # ── TAB 3 : Timeline ───────────────────────────────────────────────────
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
                    d_max = (df_tl["date_retour"].max() if "date_retour" in df_tl.columns
                             else df_tl["date_depart"].max())
                    span  = max((d_max - d_min).days, 1)
                    cur_ym = None
                    for _, row in df_tl.iterrows():
                        ym = row["date_depart"].strftime("%B %Y").capitalize()
                        if ym != cur_ym:
                            cur_ym = ym
                            st.markdown(f"<div style='color:#6366f1;font-size:.75rem;font-weight:700;"
                                        f"text-transform:uppercase;letter-spacing:1px;"
                                        f"font-family:JetBrains Mono,monospace;margin:18px 0 6px;'>{ym}</div>",
                                        unsafe_allow_html=True)
                        dep = row["date_depart"]
                        ret = row.get("date_retour", dep)
                        if pd.isna(ret): ret = dep
                        duree    = max((ret-dep).days,1)
                        left_pct = round((dep-d_min).days/span*100,1)
                        wid_pct  = max(round(duree/span*100,1),1.5)
                        dest = row.get("destination",""); cont = row.get("continent","")
                        cont_col = CONT_COLORS.get(cont,"#6b7280")
                        tv = row.get("type_voyage",""); tv_col = TYPE_COLORS.get(tv,"#6b7280")
                        bgt = row.get("budget","")
                        note_v = row.get("note",None); stars = "⭐"*int(note_v) if note_v and not pd.isna(note_v) else ""
                        cnom = ""
                        if has_client_nom: cnom=f"{row.get('client_prenom','')} {row.get('client_nom','')}".strip()
                        elif has_prenom and has_nom: cnom=f"{row.get('prenom','')} {row.get('nom','')}".strip()
                        dep_str=dep.strftime("%d %b %Y"); ret_str=ret.strftime("%d %b %Y")
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:12px 16px;margin-bottom:8px;'>"
                            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:8px;'>"
                            f"<span style='width:8px;height:8px;border-radius:50%;background:{cont_col};display:inline-block;flex-shrink:0;'></span>"
                            f"<span style='font-weight:600;color:#e8eaf0;font-size:.9rem;'>{dest}</span>"
                            f"{'<span style=\"color:#94a3b8;font-size:.78rem;\"> · '+cnom+'</span>' if cnom else ''}"
                            f"<span style='margin-left:auto;color:#64748b;font-size:.75rem;'>{dep_str} → {ret_str} · {duree}j</span></div>"
                            f"<div style='position:relative;height:10px;background:#1e293b;border-radius:5px;overflow:hidden;'>"
                            f"<div style='position:absolute;left:{left_pct}%;width:{wid_pct}%;height:100%;"
                            f"background:linear-gradient(90deg,{cont_col},{tv_col});border-radius:5px;'></div></div>"
                            f"<div style='margin-top:7px;display:flex;gap:6px;flex-wrap:wrap;'>"
                            f"<span style='background:{tv_col}22;color:{tv_col};font-size:.7rem;padding:2px 8px;border-radius:10px;'>{tv}</span>"
                            f"{'<span style=\"font-size:.75rem;color:#4ade80;font-family:JetBrains Mono,monospace;\">'+str(int(bgt))+'€</span>' if bgt else ''}"
                            f"<span style='font-size:.72rem;'>{stars}</span></div></div>",
                            unsafe_allow_html=True)

        # ── TAB 4 : Statistiques ───────────────────────────────────────────────
        with tab4:
            def _hbar(label, value, total, color, fmt=None):
                pct   = round(value/total*100) if total else 0
                v_str = fmt(value) if fmt else str(value)
                return (f"<div style='margin-bottom:10px;'>"
                        f"<div style='display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:3px;'>"
                        f"<span style='color:#c8cad6;'>{label}</span>"
                        f"<span style='color:#94a3b8;font-family:JetBrains Mono,monospace;'>{v_str}</span></div>"
                        f"<div style='background:#1e293b;border-radius:4px;height:8px;'>"
                        f"<div style='width:{pct}%;height:100%;border-radius:4px;background:{color};'></div></div></div>")

            if has_dest:
                sa, sb = st.columns(2)
                with sa:
                    n_total = len(df)
                    if has_budget:
                        bgt_total=df["budget"].sum(); bgt_moy=df["budget"].mean()
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                            f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Budget total</div>"
                            f"<div style='color:#4ade80;font-size:1.6rem;font-weight:800;font-family:JetBrains Mono,monospace;'>{int(bgt_total):,}€</div>"
                            f"<div style='color:#64748b;font-size:.8rem;'>moy. {int(bgt_moy):,}€ / voyage</div></div>",
                            unsafe_allow_html=True)
                    if has_duree:
                        d_moy=df["duree_jours"].mean(); d_max=df["duree_jours"].max()
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                            f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Durée moyenne</div>"
                            f"<div style='color:#60a5fa;font-size:1.6rem;font-weight:800;font-family:JetBrains Mono,monospace;'>{d_moy:.1f}j</div>"
                            f"<div style='color:#64748b;font-size:.8rem;'>max {int(d_max)}j</div></div>",
                            unsafe_allow_html=True)
                    if has_note:
                        notes=df["note"].dropna()
                        if len(notes):
                            note_moy=notes.mean()
                            st.markdown(
                                f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                                f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Note moyenne</div>"
                                f"<div style='color:#fbbf24;font-size:1.6rem;font-weight:800;'>{'⭐'*round(note_moy)} <span style='font-size:.9rem;font-family:JetBrains Mono,monospace;'>{note_moy:.1f}/5</span></div>"
                                f"<div style='color:#64748b;font-size:.8rem;'>{len(notes)} avis</div></div>",
                                unsafe_allow_html=True)
                with sb:
                    if has_continent:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>Par continent</div>", unsafe_allow_html=True)
                        bars = "".join(_hbar(k,v,n_total,CONT_COLORS.get(k,"#6b7280"))
                                       for k,v in df["continent"].value_counts().items())
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>{bars}</div>", unsafe_allow_html=True)
                    if has_type:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>Par type</div>", unsafe_allow_html=True)
                        bars = "".join(_hbar(k,v,n_total,TYPE_COLORS.get(k,"#6b7280"))
                                       for k,v in df["type_voyage"].value_counts().items())
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;'>{bars}</div>", unsafe_allow_html=True)
                if has_budget:
                    st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;margin:14px 0 8px;'>Top destinations — budget</div>", unsafe_allow_html=True)
                    top_dest = df.groupby("destination")["budget"].sum().sort_values(ascending=False).head(8)
                    max_b    = top_dest.max()
                    bars     = "".join(
                        _hbar(d,int(b),int(max_b),
                              CONT_COLORS.get(df[df["destination"]==d]["continent"].iloc[0],"#6b7280") if has_continent else "#6b7280",
                              fmt=lambda x:f"{x:,}€") for d,b in top_dest.items())
                    st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;'>{bars}</div>", unsafe_allow_html=True)
            elif has_nom:
                sa, sb = st.columns(2)
                with sa:
                    n_total=len(df)
                    if "statut" in df.columns:
                        n_actif=(df["statut"]=="actif").sum()
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
                            f"<div style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Statut</div>"
                            f"<div style='display:flex;gap:14px;'>"
                            f"<div><div style='color:#4ade80;font-size:1.4rem;font-weight:800;font-family:JetBrains Mono,monospace;'>{n_actif}</div><div style='color:#64748b;font-size:.78rem;'>actifs</div></div>"
                            f"<div><div style='color:#f87171;font-size:1.4rem;font-weight:800;font-family:JetBrains Mono,monospace;'>{n_total-n_actif}</div><div style='color:#64748b;font-size:.78rem;'>inactifs</div></div>"
                            f"</div></div>", unsafe_allow_html=True)
                with sb:
                    if has_ville:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>Par ville</div>", unsafe_allow_html=True)
                        bars = "".join(_hbar(k,v,n_total,"#6366f1")
                                       for k,v in df["ville"].value_counts().head(8).items())
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;padding:14px 18px;'>{bars}</div>", unsafe_allow_html=True)
            else:
                st.info("Statistiques non disponibles pour cette combinaison de colonnes.")

    # ── Enrichissement ─────────────────────────────────────────────────────────
    st.markdown("---")
    other_table = ENRICH[current_table]["other"]

    if cnt is None:
        pass  # pas encore calculé
    elif cnt == "done":
        pass
    elif cnt == 0:
        st.markdown(
            f"<div style='background:#1a1d27;border:1px solid #2a2d3e;border-radius:10px;"
            f"padding:14px 18px;color:#6b7280;font-size:.9rem;'>"
            f"ℹ️ Aucune information supplémentaire dans <b style='color:#94a3b8'>{other_table}</b> "
            f"pour ces résultats.</div>", unsafe_allow_html=True)
    else:
        em = "enrich-btn-marker"
        st.markdown(
            f'<div id="{em}"></div><style>'
            f"div.element-container:has(#{em}) + div.element-container button{{"
            f"background:linear-gradient(135deg,#065f46,#047857)!important;"
            f"border:1px solid #059669!important;box-shadow:0 0 14px #05966966!important;"
            f"font-size:.92rem!important;padding:10px 0!important;}}"
            f"div.element-container:has(#{em}) + div.element-container button:hover{{"
            f"filter:brightness(1.15)!important;transform:translateY(-1px)!important;}}</style>",
            unsafe_allow_html=True)
        if st.button(
            f"🔗 Enrichir avec {other_table} — {cnt} ligne{'s' if cnt>1 else ''} disponible{'s' if cnt>1 else ''}",
            width="stretch", key="enrich_btn"):
            try:
                old_cols = set(df.columns)
                enriched = run_enrich_query(current_table, st.session_state.last_where,
                                            st.session_state.last_params)
                new_cols = set(enriched.columns); added = new_cols - old_cols
                blink = set()
                if added & {"destination","client_nom","client_prenom","voyage_id","date_depart","type_voyage"}:
                    blink.add(2)
                if "date_depart" in added and "date_depart" not in old_cols:
                    blink.add(3)
                if added & {"budget","continent","type_voyage","ville","note"}:
                    blink.add(4)
                st.session_state.results             = enriched
                st.session_state.enrich_count        = "done"
                st.session_state["_enrich_hl_until"] = time.time() + 20
                st.session_state["_blink_tabs"]      = blink
                st.rerun()
            except Exception as e:
                st.error(f"Erreur enrichissement : {e}")
