import streamlit as st
import pandas as pd
import sqlite3
from collections import OrderedDict

st.set_page_config(page_title="SQL Query Builder", page_icon="🔍",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;}
.stApp{background:#0d0f14;color:#e8eaf0;}
[data-testid="stSidebar"]{background:#13151d;border-right:1px solid #1e2130;}
[data-testid="stSidebar"] *{color:#c8cad6!important;}
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
/* Table selector pills */
div[data-testid="stHorizontalBlock"] .table-pill button{
   border-radius:20px!important;padding:4px 18px!important;}
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
    "employes": ["id","nom","prenom","email","departement","poste","ville","pays","salaire","date_embauche","statut"],
    "produits":  ["id","nom","categorie","marque","prix","stock","description","statut"],
    "clients":   ["id","nom","prenom","email","telephone","ville","pays","date_inscription","statut"],
    "voyages":   ["id","client_id","destination","pays_destination","continent","date_depart","date_retour","duree_jours","type_voyage","transport","hotel","budget","statut","note"],
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

def is_date_col(col_name: str) -> bool:
    return "date" in col_name.lower()

def build_date_value(year: int, month: int, day: int) -> str:
    """Build a partial date string for LIKE matching."""
    if month == 0:
        return f"{year:04d}"
    elif day == 0:
        return f"{year:04d}-{month:02d}"
    else:
        return f"{year:04d}-{month:02d}-{day:02d}"

# ── State ──────────────────────────────────────────────────────────────────────
for k, v in [("conditions",[]),("selected_table","employes"),("results",None),("editing",{})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# BINARY TREE (left-associative)
# ══════════════════════════════════════════════════════════════════════════════
def build_tree(conditions):
    if not conditions:
        return None
    tree = {"type": "leaf", "idx": 0}
    for i in range(1, len(conditions)):
        tree = {"type": "branch", "op": conditions[i]["join_op"],
                "left": tree, "right": {"type": "leaf", "idx": i}}
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
# TREE RENDERER
# ══════════════════════════════════════════════════════════════════════════════
BRANCH_STYLES = {
    "ET": {"color": "#fca5a5", "bg": "#450a0a", "border": "#991b1b"},
    "OU": {"color": "#93c5fd", "bg": "#172554", "border": "#1d4ed8"},
}
NEUTRAL_CONNECTOR = "#475569"

OP_NATURAL = {
    "Contient":     "contient",
    "Commence par": "commence par",
    "Finit par":    "finit par",
    "Égal à":       "est",
    "Différent de": "n'est pas",
    "Supérieur à":  ">",
    "Inférieur à":  "<",
}

def _date_label(val: str) -> str:
    """Human-readable date fragment: '2023' → '2023', '2023-04' → 'avril 2023'."""
    parts = val.split("-")
    if len(parts) == 1:
        return f"année {parts[0]}"
    elif len(parts) == 2:
        try:
            return f"{MONTHS_FR[int(parts[1])]} {parts[0]}"
        except Exception:
            return val
    else:
        try:
            return f"{int(parts[2])} {MONTHS_FR[int(parts[1])]} {parts[0]}"
        except Exception:
            return val

def _leaf_html(conditions, idx):
    c = conditions[idx]
    if c.get("is_date"):
        label = _date_label(c["value"])
        return (f"<span class='t-leaf'>"
                f"<b style='color:#a5f3fc;'>{c['column']}</b> "
                f"<span style='color:#fbbf24;'>en</span> "
                f"<span style='color:#86efac;'>{label}</span>"
                f"</span>")
    op_str = OP_NATURAL[c["operator"]]
    val_str = f"«\u202f{c['value']}\u202f»"
    return (f"<span class='t-leaf'>"
            f"<b style='color:#a5f3fc;'>{c['column']}</b> "
            f"<span style='color:#fbbf24;'>{op_str}</span> "
            f"<span style='color:#86efac;'>{val_str}</span>"
            f"</span>")

def _build_prefix_html(prefix_parts, connector, connector_color):
    spans = "".join(
        f"<span style='font-family:JetBrains Mono,monospace;font-size:.82rem;"
        f"white-space:pre;color:{c};'>{t}</span>"
        for t, c in prefix_parts
    )
    if connector:
        spans += (f"<span style='font-family:JetBrains Mono,monospace;font-size:.82rem;"
                  f"white-space:pre;color:{connector_color};'>{connector}</span>")
    return spans

def _render_node(node, conditions, prefix_parts=None, is_last=True,
                 is_root=False, parent_op=None):
    if prefix_parts is None:
        prefix_parts = []
    connector       = "" if is_root else ("└── " if is_last else "├── ")
    connector_color = BRANCH_STYLES[parent_op]["color"] if parent_op else NEUTRAL_CONNECTOR
    prefix_len      = sum(len(t) for t, _ in prefix_parts) + len(connector)
    prefix_html     = _build_prefix_html(prefix_parts, connector, connector_color)

    if node["type"] == "leaf":
        if prefix_html:
            w = max(prefix_len * 0.135, 0.35)
            ca, cb = st.columns([w, max(9 - w, 1)])
            ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{prefix_html}</div>",
                        unsafe_allow_html=True)
            cb.markdown(f"<div style='padding-top:6px;'>{_leaf_html(conditions, node['idx'])}</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(_leaf_html(conditions, node["idx"]), unsafe_allow_html=True)
    else:
        op        = node["op"]
        right_idx = node["right"]["idx"]
        if prefix_html:
            w = max(prefix_len * 0.135, 0.35)
            ca, cb = st.columns([w, max(9 - w, 1)])
            ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{prefix_html}</div>",
                        unsafe_allow_html=True)
            with cb:
                _branch_button(op, right_idx)
        else:
            _branch_button(op, right_idx)

        if is_root:
            new_prefix = prefix_parts
        elif not is_last:
            new_prefix = prefix_parts + [("│   ", connector_color)]
        else:
            new_prefix = prefix_parts + [("    ", connector_color)]

        _render_node(node["left"],  conditions, new_prefix, is_last=False, parent_op=op)
        _render_node(node["right"], conditions, new_prefix, is_last=True,  parent_op=op)

def _branch_button(op, right_idx):
    s = BRANCH_STYLES[op]
    bg, color, border = s["bg"], s["color"], s["border"]
    marker = f"tbtn-{right_idx}"
    st.markdown(
        f'<div id="{marker}"></div>'
        f"<style>"
        f"div.element-container:has(#{marker}) + div.element-container button{{"
        f"background:{bg}!important;color:{color}!important;"
        f"border:1.5px solid {border}!important;"
        f"font-family:'JetBrains Mono',monospace!important;"
        f"font-size:.82rem!important;font-weight:700!important;"
        f"padding:3px 16px!important;border-radius:5px!important;"
        f"box-shadow:0 0 8px {border}55!important;min-height:0!important;}}"
        f"div.element-container:has(#{marker}) + div.element-container button:hover{{"
        f"filter:brightness(1.3)!important;transform:translateY(-1px)!important;}}"
        f"</style>",
        unsafe_allow_html=True,
    )
    if st.button(op, key=f"treeop_{right_idx}", help="Cliquer pour basculer ET / OU"):
        st.session_state.conditions[right_idx]["join_op"] = "OU" if op == "ET" else "ET"
        st.rerun()

def render_tree(conditions, table):
    st.markdown(
        f"<div class='tree-wrap'>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>Requête</span>"
        f"<div style='margin:6px 0 12px;'>"
        f"<span class='t-root'>SELECT * FROM {table}</span></div>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>WHERE</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    tree = build_tree(conditions)
    if tree is None:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>"
                    "Aucune condition.</p>", unsafe_allow_html=True)
        return
    _render_node(tree, conditions, prefix_parts=[], is_last=True,
                 is_root=True, parent_op=None)

# ══════════════════════════════════════════════════════════════════════════════
# DIALOG
# ══════════════════════════════════════════════════════════════════════════════
@st.dialog("🔎 Explorer cette valeur")
def cell_filter_dialog(col_name, cell_value):
    str_value = str(cell_value)
    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;border-radius:10px;"
        f"padding:12px 16px;margin-bottom:16px;'>"
        f"<span style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
        f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Cellule sélectionnée</span><br>"
        f"<span style='font-family:JetBrains Mono,monospace;font-size:.92rem;'>"
        f"<b style='color:#a5f3fc;'>{col_name}</b>"
        f" <span style='color:#fbbf24;'>=</span>"
        f" <span style='color:#86efac;'>«{str_value}»</span>"
        f"</span></div>",
        unsafe_allow_html=True,
    )
    tables_with_col = [t for t, cols in TABLES.items() if col_name in cols]
    target_table = st.selectbox(
        "Table cible", tables_with_col,
        index=tables_with_col.index(st.session_state.selected_table)
              if st.session_state.selected_table in tables_with_col else 0,
        key="dlg_table",
    )
    op = st.selectbox("Opérateur", OP_LABELS, key="dlg_op")
    sql_sym, value_fn = OPERATORS[op]
    transformed_val   = value_fn(str_value)
    st.markdown(
        f"<div style='background:#0a0c12;border:1px solid #1e2130;border-left:3px solid #6366f1;"
        f"border-radius:8px;padding:8px 14px;font-family:JetBrains Mono,monospace;"
        f"font-size:.8rem;color:#a5f3fc;margin:8px 0 14px;'>"
        f"SELECT * FROM <b>{target_table}</b> WHERE <b>{col_name}</b>"
        f" <span style='color:#fbbf24'>{sql_sym}</span>"
        f" <span style='color:#86efac'>'{transformed_val}'</span></div>",
        unsafe_allow_html=True,
    )
    if st.button("▶ Lancer la requête", use_container_width=True,
                 type="primary", key="dlg_run"):
        conn = get_connection()
        q = f"SELECT * FROM {target_table} WHERE {col_name} {sql_sym} ?"
        try:
            st.session_state.results        = pd.read_sql_query(q, conn, params=[transformed_val])
            st.session_state.selected_table = target_table
            st.session_state.conditions = [{"column": col_name, "operator": op,
                                            "value": str_value, "join_op": "ET"}]
        except Exception as e:
            st.error(f"Erreur SQL : {e}"); return
        st.rerun()

    count_key = f"cnt_{target_table}__{col_name}__{op}__{str_value}"
    if count_key in st.session_state:
        count = st.session_state[count_key]
        st.markdown(
            f"<div style='background:#14532d;border:2px solid #16a34a;border-radius:8px;"
            f"padding:12px;text-align:center;'>"
            f"<span style='color:#86efac;font-size:.72rem;text-transform:uppercase;"
            f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>Résultats estimés</span><br>"
            f"<span style='color:#4ade80;font-size:2.2rem;font-weight:800;"
            f"font-family:JetBrains Mono,monospace;'>{count}</span>"
            f"<span style='color:#86efac;font-size:.85rem;'> ligne(s)</span></div>",
            unsafe_allow_html=True,
        )
    else:
        if st.button("🔢 Estimer le nombre de résultats (COUNT)",
                     use_container_width=True, key="dlg_count"):
            conn = get_connection()
            q = f"SELECT COUNT(*) AS total FROM {target_table} WHERE {col_name} {sql_sym} ?"
            try:
                res   = pd.read_sql_query(q, conn, params=[transformed_val])
                st.session_state[count_key] = int(res["total"].iloc[0])
            except Exception as e:
                st.error(f"Erreur SQL : {e}")
            st.rerun()

    st.divider()
    st.markdown("<span style='color:#94a3b8;font-size:.8rem;'>"
                "Ou ajouter comme condition dans l'arbre :</span>",
                unsafe_allow_html=True)
    if st.session_state.conditions:
        join = st.radio("Lier avec", ["ET","OU"], horizontal=True, key="dlg_join")
    else:
        join = "ET"
    if st.button("➕ Ajouter à l'arbre", use_container_width=True, key="dlg_add"):
        st.session_state.conditions.append(
            {"column": col_name, "operator": op,
             "value": str_value, "join_op": join})
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE LAYOUT
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
for i, (tname, _) in enumerate(TABLES.items()):
    is_active = (st.session_state.selected_table == tname)
    active_bg    = "#3b82f6"
    inactive_bg  = "#1a1d27"
    active_color = "#ffffff"
    inactive_color = "#94a3b8"
    # Style the button to look like a pill/tab
    marker = f"tpill-{tname}"
    t_cols[i].markdown(
        f'<div id="{marker}"></div>'
        f"<style>div.element-container:has(#{marker}) + div.element-container button{{"
        f"background:{'linear-gradient(135deg,#3b82f6,#7c3aed)' if is_active else inactive_bg}!important;"
        f"color:{active_color if is_active else inactive_color}!important;"
        f"border:{'none' if is_active else '1px solid #2a2d3e'}!important;"
        f"border-radius:20px!important;width:100%;font-size:.82rem!important;}}"
        f"</style>",
        unsafe_allow_html=True,
    )
    if t_cols[i].button(tname, key=f"tpill_{tname}", use_container_width=True):
        st.session_state.selected_table = tname
        st.session_state.conditions = []
        st.session_state.results    = None
        st.rerun()

st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

current_table = st.session_state.selected_table
current_cols  = TABLES[current_table]

# ── Add condition form ─────────────────────────────────────────────────────────
st.markdown("### ➕ Ajouter une condition")

with st.container():
    fa, fb, fc, fd = st.columns([2, 2, 3, 1])
    with fa:
        new_col = st.selectbox("Colonne", current_cols, key="new_col",
                               label_visibility="collapsed")
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
            with d1:
                new_year = st.number_input("Année *", min_value=1900, max_value=2100,
                                           value=2023, step=1, key="new_year",
                                           label_visibility="visible")
            with d2:
                new_month = st.number_input("Mois", min_value=0, max_value=12,
                                            value=0, step=1, key="new_month",
                                            help="0 = non précisé",
                                            label_visibility="visible")
            with d3:
                new_day = st.number_input("Jour", min_value=0, max_value=31,
                                          value=0, step=1, key="new_day",
                                          help="0 = non précisé",
                                          label_visibility="visible")
        else:
            new_val_text = st.text_input("Valeur", key="new_val",
                                         placeholder="Valeur…",
                                         label_visibility="collapsed")
    with fd:
        if st.session_state.conditions:
            new_join = st.radio("Lier", ["ET","OU"], horizontal=False, key="new_join",
                                label_visibility="collapsed")
        else:
            new_join = "ET"

    btn_a, btn_b = st.columns([3, 1])
    with btn_a:
        if st.button("➕ Ajouter la condition", use_container_width=True):
            if is_date:
                val = build_date_value(int(new_year), int(new_month), int(new_day))
                st.session_state.conditions.append({
                    "column":   new_col,
                    "operator": "Commence par",
                    "value":    val,
                    "join_op":  new_join,
                    "is_date":  True,
                })
                st.rerun()
            elif new_val_text.strip():
                st.session_state.conditions.append({
                    "column":   new_col,
                    "operator": new_op,
                    "value":    new_val_text.strip(),
                    "join_op":  new_join,
                    "is_date":  False,
                })
                st.rerun()
            else:
                st.warning("Veuillez entrer une valeur.")
    with btn_b:
        if st.button("🗑 Tout effacer", use_container_width=True):
            st.session_state.conditions = []
            st.session_state.results    = None
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
        preview = build_query_display(current_table, st.session_state.conditions)
        st.markdown(f"<div class='sql-display'>{preview}</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    if st.button("▶ Exécuter la requête", use_container_width=True, type="primary"):
        conn = get_connection()
        q, params = build_query(current_table, st.session_state.conditions)
        try:
            st.session_state.results = pd.read_sql_query(q, conn, params=params)
        except Exception as e:
            st.error(f"Erreur SQL : {e}")

# ── Results ────────────────────────────────────────────────────────────────────
if st.session_state.results is not None:
    df = st.session_state.results
    st.markdown("---")
    st.markdown("### 📊 Résultats")
    st.caption("💡 Cliquez sur une cellule pour explorer sa valeur.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Lignes", len(df))
    m2.metric("Colonnes", len(df.columns))
    m3.metric("Conditions", len(st.session_state.conditions))
    if len(df) == 0:
        st.info("Aucun résultat ne correspond à vos critères.")
    else:
        event = st.dataframe(df, use_container_width=True, hide_index=True,
                             on_select="rerun", selection_mode="single-cell")
        sel  = event.selection if hasattr(event, "selection") else {}
        rows = sel.get("rows", [])
        cols = sel.get("columns", [])
        if rows and cols:
            cell_filter_dialog(df.columns[cols[0]], df.iloc[rows[0], cols[0]])
        st.download_button("⬇ Télécharger CSV",
            df.to_csv(index=False).encode("utf-8"),
            f"resultats_{current_table}.csv", "text/csv")
