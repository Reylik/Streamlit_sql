"""
Constantes partagées et helpers purs (sans dépendance à Streamlit ni à la DB).
"""

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

OP_NATURAL = {
    "Contient":     "contient",
    "Commence par": "commence par",
    "Finit par":    "finit par",
    "Égal à":       "est",
    "Différent de": "n'est pas",
    "Supérieur à":  ">",
    "Inférieur à":  "<",
}

MONTHS_FR = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
             "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

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


def is_date_col(col: str) -> bool:
    return "date" in col.lower()


def build_date_value(year: int, month: int, day: int) -> str:
    if month == 0:  return f"{year:04d}"
    elif day == 0:  return f"{year:04d}-{month:02d}"
    else:           return f"{year:04d}-{month:02d}-{day:02d}"


def _find_col(df, *candidates: str):
    """Retourne le premier nom de colonne présent dans df parmi les candidats."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _format_date_fr(date_str: str) -> str:
    """Convertit '2023-04-10' en '10/04/2023'."""
    if not date_str:
        return "—"
    try:
        parts = str(date_str).split(" ")[0].split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        pass
    return str(date_str)


def _date_label(val: str) -> str:
    p = val.split("-")
    try:
        if len(p) == 1: return f"année {p[0]}"
        if len(p) == 2: return f"{MONTHS_FR[int(p[1])]} {p[0]}"
        return f"{int(p[2])} {MONTHS_FR[int(p[1])]} {p[0]}"
    except Exception:
        return val
