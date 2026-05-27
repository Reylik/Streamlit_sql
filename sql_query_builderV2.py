import streamlit as st
import pandas as pd
import sqlite3
import re
import copy
from datetime import datetime

st.set_page_config(page_title="SQL Query Builder", page_icon="🔍",
                   layout="wide", initial_sidebar_state="expanded")

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


# ══════════════════════════════════════════════════════════════════════════════
# OPÉRATEURS & UTILITAIRES PURS
# ══════════════════════════════════════════════════════════════════════════════
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
    if not conditions: return None
    tree = {"type": "leaf", "idx": 0}
    for i in range(1, len(conditions)):
        tree = {"type": "branch", "op": conditions[i]["join_op"],
                "left": tree, "right": {"type": "leaf", "idx": i}}
    return tree


def _sql_from_tree(node, conditions, params, display):
    if node["type"] == "leaf":
        c = conditions[node["idx"]]
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
        sym, fn = OPERATORS[c["operator"]]
        val = fn(c["value"])
        if display: return f"{c['column']} {sym} '{val}'"
        params.append(val)
        return f"{c['column']} {sym} ?"
    sql_op = "AND" if node["op"] == "ET" else "OR"
    L = _sql_from_tree(node["left"],  conditions, params, display)
    R = _sql_from_tree(node["right"], conditions, params, display)
    return f"({L} {sql_op} {R})"


def build_where(conditions, display=False):
    if not conditions: return "1=1", []
    params = []
    where = _sql_from_tree(build_tree(conditions), conditions, params, display)
    return where, params


def build_query(table, conditions):
    where, params = build_where(conditions)
    return f"SELECT *\nFROM {table}\nWHERE {where}", params


def build_query_display(table, conditions):
    where, _ = build_where(conditions, display=True)
    if where == "1=1": return f"SELECT *\nFROM {table}"
    return f"SELECT *\nFROM {table}\nWHERE {where}"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS ENRICH  (enrich passé en paramètre pour éviter le global)
# ══════════════════════════════════════════════════════════════════════════════
def compute_enrich_count(table, where_clause, params, enrich):
    sql = enrich[table]["count_sql"].format(where=where_clause)
    try:
        res = pd.read_sql_query(sql, get_connection(), params=params)
        return int(res["total"].iloc[0])
    except Exception:
        return None


def run_enrich_query(table, where_clause, params, enrich):
    sql = enrich[table]["select_sql"].format(where=where_clause)
    return pd.read_sql_query(sql, get_connection(), params=params)


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
    c = conditions[idx]
    if c.get("is_date"):
        return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{c['column']}</b> "
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
                f"<b style='color:#a5f3fc;'>{c['column']}</b> "
                f"<span style='color:#fbbf24;'>{op_str}</span> "
                f"<span style='color:#86efac;'>[{preview}{suffix}]</span>"
                f"</span>")
    op_str = OP_NATURAL.get(c["operator"], c["operator"])
    return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{c['column']}</b> "
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
    else:
        op, right_idx = node["op"], node["right"]["idx"]
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
    tree = build_tree(conditions)
    if tree is None:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>Aucune condition.</p>",
                    unsafe_allow_html=True)
        return
    _render_node(tree, conditions, prefix_parts=[], is_last=True, is_root=True, parent_op=None)


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
            st.session_state.results        = pd.read_sql_query(q, get_connection(), params=[tv])
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
                r2 = pd.read_sql_query(q2, get_connection(), params=[tv])
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


def _push_history(table: str, conditions: list, row_count: int) -> None:
    """Ajoute (ou met à jour) une entrée dans l'historique des requêtes."""
    query_display = build_query_display(table, conditions)
    # Extrait uniquement la clause WHERE pour le résumé affiché
    if "\nWHERE " in query_display:
        summary = query_display.split("\nWHERE ", 1)[1]
    else:
        summary = "Tous les enregistrements"

    entry = {
        "ts":         datetime.now().strftime("%d/%m %H:%M"),
        "table":      table,
        "conditions": copy.deepcopy(conditions),
        "summary":    summary,
        "row_count":  row_count,
    }
    history = st.session_state.setdefault("query_history", [])
    # Dédoublonnage : si même requête que la précédente, on met juste à jour
    if history and history[0]["table"] == table and history[0]["summary"] == summary:
        history[0].update(ts=entry["ts"], row_count=row_count)
        return
    history.insert(0, entry)
    del history[MAX_HISTORY:]   # borne max


def _render_history_sidebar(enrich: dict) -> None:
    """Panneau latéral : liste des requêtes passées avec relance en un clic."""
    history = st.session_state.get("query_history", [])

    with st.sidebar:
        st.markdown(
            "<span style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
            "letter-spacing:1px;font-family:JetBrains Mono,monospace;'>"
            f"🕐 Historique ({len(history)} / {MAX_HISTORY})</span>",
            unsafe_allow_html=True)

        if not history:
            st.markdown(
                "<p style='color:#4a5170;font-style:italic;font-size:.82rem;"
                "margin-top:8px;'>Aucune requête exécutée.</p>",
                unsafe_allow_html=True)
            return

        for i, entry in enumerate(history):
            n      = entry["row_count"]
            tbl    = entry["table"]
            ts     = entry["ts"]
            summ   = entry["summary"]
            # Troncature de l'affichage pour éviter les entrées trop longues
            summ_display = (summ[:120] + "…") if len(summ) > 120 else summ

            st.markdown(
                f"<div style='background:#13151d;border:1px solid #1e2130;"
                f"border-radius:10px;padding:10px 12px;margin-bottom:8px;'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;margin-bottom:5px;'>"
                f"<span style='font-family:JetBrains Mono,monospace;"
                f"font-size:.72rem;color:#6366f1;font-weight:600;'>{tbl}</span>"
                f"<span style='font-size:.7rem;color:#475569;'>{ts}</span>"
                f"</div>"
                f"<div style='font-family:JetBrains Mono,monospace;font-size:.72rem;"
                f"color:#a5f3fc;white-space:pre-wrap;word-break:break-word;"
                f"line-height:1.55;margin-bottom:7px;'>{summ_display}</div>"
                f"<span style='font-size:.7rem;color:#4ade80;'>"
                f"{n} ligne{'s' if n != 1 else ''}</span>"
                f"</div>",
                unsafe_allow_html=True)

            if st.button("↩ Relancer", key=f"hist_replay_{i}", use_container_width=True):
                st.session_state.selected_table      = entry["table"]
                st.session_state.conditions          = copy.deepcopy(entry["conditions"])
                st.session_state.results             = None
                st.session_state.enrich_count        = None
                st.session_state["_last_cell_click"] = None
                st.session_state["_auto_execute"]    = True
                st.rerun()

        st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
        if st.button("🗑 Vider l'historique", key="hist_clear", use_container_width=True):
            st.session_state.query_history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE UNIQUE
# ══════════════════════════════════════════════════════════════════════════════
def run_app(tables: dict, enrich: dict):
    """
    Lance l'application SQL Query Builder.

    Paramètres
    ----------
    tables : dict
        Dictionnaire  { nom_table: [col1, col2, ...] }
        Exemple : {"clients": ["id", "nom", "email"], "voyages": ["id", "destination"]}

    enrich : dict
        Dictionnaire de jointure inter-tables.
        Chaque entrée : { nom_table: {"other": ..., "label": ...,
                                      "count_sql": ..., "select_sql": ...} }
    """
    # ── Injection de la config pour le dialog ─────────────────────────────────
    st.session_state._app_tables = tables
    st.session_state._app_enrich = enrich

    # ── Initialisation de l'état ──────────────────────────────────────────────
    default_table = next(iter(tables))
    for k, v in [("conditions", []), ("selected_table", default_table),
                 ("results", None), ("enrich_count", None),
                 ("last_where", ""), ("last_params", []), ("editing", {}),
                 ("query_history", [])]:          # ← historique initialisé ici
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Panneau historique (sidebar) ──────────────────────────────────────────
    _render_history_sidebar(enrich)

    # ── Auto-exécution : relance depuis l'historique ──────────────────────────
    if st.session_state.pop("_auto_execute", False):
        _q, _p = build_query(st.session_state.selected_table, st.session_state.conditions)
        try:
            _res = pd.read_sql_query(_q, get_connection(), params=_p)
            st.session_state.results = _res
            _w, _wp = build_where(st.session_state.conditions)
            st.session_state.last_where   = _w
            st.session_state.last_params  = _wp
            st.session_state.enrich_count = compute_enrich_count(
                st.session_state.selected_table, _w, _wp, enrich)
            _push_history(st.session_state.selected_table,
                          st.session_state.conditions, len(_res))
        except Exception as _e:
            st.error(f"Erreur SQL (relance) : {_e}")

    # ── En-tête ───────────────────────────────────────────────────────────────
    st.markdown("# 🔍 SQL Query Builder")
    st.markdown("<p style='color:#6b7280;margin-top:-14px;margin-bottom:20px;'>"
                "Construisez vos requêtes SQL visuellement, sans écrire une ligne de code.</p>",
                unsafe_allow_html=True)

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
            st.rerun()

    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
    current_table = st.session_state.selected_table
    current_cols  = tables[current_table]

    # ── Ajout de condition ────────────────────────────────────────────────────
    st.markdown("### ➕ Ajouter une condition")
    fa, fb, fc, fd = st.columns([2, 2, 3, 1])
    with fa:
        new_col = st.selectbox("Colonne", current_cols, key="new_col", label_visibility="collapsed")
    with fb:
        is_date = is_date_col(new_col)
        if is_date:
            st.markdown("<span style='color:#a78bfa;font-size:.78rem;'>📅 Colonne date</span>",
                        unsafe_allow_html=True)
        else:
            new_op = st.selectbox("Opérateur", OP_LABELS, key="new_op", label_visibility="collapsed")
    with fc:
        if is_date:
            d1, d2, d3 = st.columns(3)
            new_year  = d1.number_input("Année *", 1900, 2100, 2023, 1, key="new_year")
            new_month = d2.number_input("Mois",    0,    12,   0,    1, key="new_month", help="0 = non précisé")
            new_day   = d3.number_input("Jour",    0,    31,   0,    1, key="new_day",   help="0 = non précisé")
        else:
            st.text_area("Valeur(s)", key="new_val",
                         placeholder="Une valeur, ou plusieurs séparées par des virgules / sauts de ligne",
                         height=80, label_visibility="collapsed")
    with fd:
        new_join = (st.radio("Lier", ["ET", "OU"], horizontal=False, key="new_join",
                             label_visibility="collapsed")
                    if st.session_state.conditions else "ET")

    btn_a, btn_b = st.columns([3, 1])
    with btn_a:
        if st.button("➕ Ajouter la condition", width="stretch"):
            if is_date:
                st.session_state.conditions.append({
                    "column": new_col, "operator": "Commence par",
                    "value":  build_date_value(int(new_year), int(new_month), int(new_day)),
                    "join_op": new_join, "is_date": True,
                })
                st.rerun()
            else:
                raw    = st.session_state.get("new_val", "")
                values = [v.strip() for v in re.split(r"[,\n]", raw) if v.strip()]
                if not values:
                    st.warning("Veuillez entrer au moins une valeur.")
                elif len(values) == 1:
                    st.session_state.conditions.append({
                        "column": new_col, "operator": new_op,
                        "value": values[0], "join_op": new_join,
                        "is_date": False, "is_bulk": False,
                    })
                    st.rerun()
                else:
                    st.session_state.conditions.append({
                        "column": new_col, "operator": new_op,
                        "value": ", ".join(values), "values": values,
                        "join_op": new_join, "is_date": False, "is_bulk": True,
                    })
                    st.rerun()
    with btn_b:
        if st.button("🗑 Effacer", width="stretch"):
            st.session_state.conditions   = []
            st.session_state.results      = None
            st.session_state.enrich_count = None
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
                        f"{build_query_display(current_table, st.session_state.conditions)}"
                        f"</div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        if st.button("▶ Exécuter la requête", width="stretch", type="primary"):
            q, params = build_query(current_table, st.session_state.conditions)
            try:
                results = pd.read_sql_query(q, get_connection(), params=params)
                st.session_state.results = results
                where, wparams = build_where(st.session_state.conditions)
                st.session_state.last_where   = where
                st.session_state.last_params  = wparams
                st.session_state.enrich_count = compute_enrich_count(current_table, where, wparams, enrich)
                st.session_state["_last_cell_click"] = None
                _push_history(current_table, st.session_state.conditions, len(results))
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

        CONT_COLORS = {
            "Asie": "#f59e0b", "Europe": "#3b82f6", "Amérique": "#10b981",
            "Afrique": "#ef4444", "Océanie": "#8b5cf6",
        }
        TYPE_COLORS = {
            "Tourisme": "#3b82f6", "Affaires": "#8b5cf6", "Détente": "#10b981",
            "Lune de miel": "#f472b6", "Safari": "#f59e0b", "Aventure": "#ef4444",
            "Luxe": "#fbbf24", "City Break": "#06b6d4", "Culturel": "#a78bfa",
            "Plage": "#22d3ee", "Romantique": "#fb7185",
        }

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
            if has_nom and has_prenom and has_dest:
                for client_id, group in df.groupby("id", sort=False):
                    row0       = group.iloc[0]
                    initials   = (str(row0.get("prenom", "?"))[:1] + str(row0.get("nom", "?"))[:1]).upper()
                    stat_color = "#4ade80" if row0.get("statut") == "actif" else "#f87171"
                    n_voyages  = len(group)
                    card_html  = (
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-radius:12px;padding:16px 20px;margin-bottom:16px;'>"
                        f"<div style='display:flex;align-items:center;gap:14px;margin-bottom:12px;'>"
                        f"<div style='width:44px;height:44px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;font-size:1rem;color:white;flex-shrink:0;'>{initials}</div>"
                        f"<div><div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>"
                        f"{row0.get('prenom','')} {row0.get('nom','')}</div>"
                        f"<div style='color:#64748b;font-size:.82rem;'>"
                        f"{row0.get('ville','')} &nbsp;·&nbsp; "
                        f"<span style='color:{stat_color};'>{row0.get('statut','')}</span></div></div>"
                        f"<div style='margin-left:auto;text-align:right;'>"
                        f"<div style='color:#a78bfa;font-size:1.1rem;font-weight:700;"
                        f"font-family:JetBrains Mono,monospace;'>{n_voyages}</div>"
                        f"<div style='color:#64748b;font-size:.72rem;'>voyage{'s' if n_voyages>1 else ''}</div>"
                        f"</div></div>"
                    )
                    for _, vrow in group.iterrows():
                        cont    = vrow.get("continent", "")
                        tv      = vrow.get("type_voyage", "")
                        note_v  = vrow.get("note", None)
                        stars   = ("⭐" * int(note_v)) if note_v and not pd.isna(note_v) else "—"
                        card_html += (
                            f"<div style='display:flex;align-items:center;gap:10px;"
                            f"padding:7px 0;border-top:1px solid #1e2130;'>"
                            f"<div style='width:3px;height:32px;border-radius:2px;"
                            f"background:{CONT_COLORS.get(cont,'#6b7280')};flex-shrink:0;'></div>"
                            f"<div style='flex:1;'>"
                            f"<span style='color:#e8eaf0;font-weight:600;font-size:.85rem;'>{vrow.get('destination','')}</span>"
                            f"<span style='color:#475569;font-size:.75rem;margin-left:8px;'>"
                            f"{str(vrow.get('date_depart',''))[:10]} → {str(vrow.get('date_retour',''))[:10]}</span></div>"
                            f"<span style='background:{TYPE_COLORS.get(tv,'#6b7280')}22;color:{TYPE_COLORS.get(tv,'#6b7280')};"
                            f"font-size:.7rem;padding:2px 8px;border-radius:10px;'>{tv}</span>"
                            f"<span style='color:#fbbf24;font-size:.78rem;font-family:JetBrains Mono,monospace;"
                            f"margin-left:4px;'>{int(vrow.get('budget',0)):,}€</span>"
                            f"<span style='font-size:.75rem;margin-left:6px;'>{stars}</span></div>"
                        )
                    st.markdown(card_html + "</div>", unsafe_allow_html=True)

            elif has_nom and has_prenom:
                cols_grid = st.columns(2)
                for i, (_, row) in enumerate(df.iterrows()):
                    stat_color = "#4ade80" if str(row.get("statut", "")) == "actif" else "#f87171"
                    initials   = (str(row.get("prenom", "?"))[:1] + str(row.get("nom", "?"))[:1]).upper()
                    cols_grid[i % 2].markdown(
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-radius:12px;padding:16px 18px;margin-bottom:12px;'>"
                        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:10px;'>"
                        f"<div style='width:40px;height:40px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;color:white;'>{initials}</div>"
                        f"<div><div style='font-weight:700;color:#e8eaf0;'>"
                        f"{row.get('prenom','')} {row.get('nom','')}</div>"
                        f"<div style='font-size:.78rem;color:#64748b;'>{row.get('ville','')} · "
                        f"<span style='color:{stat_color};'>{row.get('statut','')}</span></div></div></div>"
                        f"<div style='font-size:.78rem;color:#64748b;line-height:1.8;'>"
                        f"📧 {row.get('email','')}<br>"
                        f"📞 {row.get('telephone','')}<br>"
                        f"📅 Membre depuis {str(row.get('date_inscription',''))[:10]}"
                        f"</div></div>",
                        unsafe_allow_html=True)

            elif has_dest:
                cols_grid = st.columns(2)
                for i, (_, row) in enumerate(df.iterrows()):
                    cont      = row.get("continent", "")
                    tv        = row.get("type_voyage", "")
                    cont_col  = CONT_COLORS.get(cont, "#6b7280")
                    tv_col    = TYPE_COLORS.get(tv, "#6b7280")
                    note_v    = row.get("note", None)
                    stars     = ("⭐" * int(note_v)) if note_v and not pd.isna(note_v) else "—"
                    cnom      = ""
                    if has_client_nom:
                        cnom = f"{row.get('client_prenom','')} {row.get('client_nom','')}".strip()
                    elif has_client_id:
                        cnom = f"Client #{int(row.get('client_id', 0))}"
                    cols_grid[i % 2].markdown(
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-top:3px solid {cont_col};"
                        f"border-radius:12px;padding:16px 18px;margin-bottom:12px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:start;'>"
                        f"<div><div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>{row.get('destination','')}</div>"
                        f"<div style='font-size:.78rem;color:#64748b;'>{row.get('pays_destination','')} · "
                        f"<span style='color:{cont_col};'>{cont}</span></div></div>"
                        f"<span style='background:{tv_col}22;color:{tv_col};"
                        f"font-size:.7rem;padding:3px 10px;border-radius:10px;white-space:nowrap;'>{tv}</span></div>"
                        f"<div style='margin:10px 0;font-size:.8rem;color:#94a3b8;'>"
                        f"📅 {str(row.get('date_depart',''))[:10]} → {str(row.get('date_retour',''))[:10]}"
                        f"{'&nbsp;&nbsp;·&nbsp;&nbsp;🕒 ' + str(row.get('duree_jours','')) + 'j' if row.get('duree_jours') else ''}"
                        f"{'&nbsp;&nbsp;·&nbsp;&nbsp;' + cnom if cnom else ''}</div>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        f"<span style='color:#64748b;font-size:.78rem;'>🏨 {row.get('hotel','')}</span>"
                        f"<div style='text-align:right;'>"
                        f"<div style='color:#4ade80;font-weight:700;font-family:JetBrains Mono,monospace;'>"
                        f"{int(row.get('budget', 0)):,}€</div>"
                        f"<div style='font-size:.75rem;'>{stars}</div></div></div></div>",
                        unsafe_allow_html=True)
            else:
                st.info("Aucune vue fiche disponible pour ces colonnes.")

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
                            f"font-family:JetBrains Mono,monospace;'>{n_total - n_actif}</div>"
                            f"<div style='color:#64748b;font-size:.78rem;'>inactifs</div></div>"
                            f"</div></div>", unsafe_allow_html=True)
                with sb:
                    if has_ville:
                        st.markdown("<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                                    "letter-spacing:1px;margin-bottom:8px;'>Par ville</div>",
                                    unsafe_allow_html=True)
                        bars = "".join(_hbar(v, c, n_total, "#6366f1")
                                       for v, c in df["ville"].value_counts().head(8).items())
                        st.markdown(f"<div style='background:#13151d;border:1px solid #1e2130;"
                                    f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                                    unsafe_allow_html=True)
            else:
                st.info("Statistiques non disponibles pour cette combinaison de colonnes.")

    # ── Dialog cellule ─────────────────────────────────────────────────────────
    if st.session_state.get("_cell_dialog_pending"):
        col_n, val_n = st.session_state.pop("_cell_dialog_pending")
        cell_filter_dialog(col_n, val_n)

    # ── Bouton Enrichir ────────────────────────────────────────────────────────
    if st.session_state.results is None:
        return

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
TABLES = {
    "clients": ["id", "nom", "prenom", "email", "telephone", "ville", "pays",
                "date_inscription", "statut"],
    "voyages": ["id", "client_id", "destination", "pays_destination", "continent",
                "date_depart", "date_retour", "duree_jours", "type_voyage",
                "transport", "hotel", "budget", "statut", "note"],
}

ENRICH = {
    "clients": {
        "other": "voyages",
        "label": "voyages",
        "count_sql": "SELECT COUNT(*) AS total FROM voyages v WHERE v.client_id IN (SELECT id FROM clients WHERE {where})",
        "select_sql": """
            SELECT
                c.id, c.nom, c.prenom, c.email, c.telephone, c.ville, c.pays,
                c.date_inscription, c.statut,
                v.id          AS voyage_id,
                v.destination, v.pays_destination, v.continent,
                v.date_depart, v.date_retour, v.duree_jours, v.type_voyage,
                v.transport, v.hotel, v.budget,
                v.statut      AS statut_voyage,
                v.note
            FROM clients c
            JOIN voyages v ON c.id = v.client_id
            WHERE c.id IN (SELECT id FROM clients WHERE {where})
        """,
    },
    "voyages": {
        "other": "clients",
        "label": "clients",
        "count_sql": "SELECT COUNT(*) AS total FROM clients c WHERE c.id IN (SELECT client_id FROM voyages WHERE {where})",
        "select_sql": """
            SELECT
                v.id, v.client_id, v.destination, v.pays_destination, v.continent,
                v.date_depart, v.date_retour, v.duree_jours, v.type_voyage,
                v.transport, v.hotel, v.budget, v.statut, v.note,
                c.nom         AS client_nom,
                c.prenom      AS client_prenom,
                c.email       AS client_email,
                c.telephone   AS client_telephone,
                c.ville       AS client_ville,
                c.pays        AS client_pays,
                c.date_inscription AS client_date_inscription,
                c.statut      AS client_statut
            FROM voyages v
            JOIN clients c ON v.client_id = c.id
            WHERE v.id IN (SELECT id FROM voyages WHERE {where})
        """,
    },
}

# ── Lancement ──────────────────────────────────────────────────────────────────
run_app(TABLES, ENRICH)
