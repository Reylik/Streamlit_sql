"""
Composants UI réutilisables : résumé de table et dialog filtre de cellule.
"""
import streamlit as st

from utils import OPERATORS, OP_LABELS, is_date_col, _format_date_fr
from db.demo import _get_db, get_table_summary
from query.builder import build_where
from query.joins import compute_enrich_count


def render_table_summary(table_name: str, columns: list, labels_map: dict) -> None:
    date_cols = tuple(c for c in columns if is_date_col(c))
    summary   = get_table_summary(table_name, date_cols)
    row_count = summary["row_count"]
    date_info = summary["date_info"]
    row_count_fmt = f"{row_count:,}".replace(",", " ")

    header_html = (
        "<div style='background:linear-gradient(135deg,#13151d 0%,#161826 100%);"
        "border:1px solid #2a2d3e;border-left:3px solid #a78bfa;"
        "border-radius:10px;padding:14px 18px;margin:8px 0 14px 0;'>"
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


@st.dialog("🔎 Explorer cette valeur")
def cell_filter_dialog(col_name, cell_value):
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
    op     = st.selectbox("Opérateur", OP_LABELS, key="dlg_op")
    sym, fn = OPERATORS[op]
    tv     = fn(str_value)
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
            where, params                   = build_where(st.session_state.conditions)
            st.session_state.last_where     = where
            st.session_state.last_params    = params
            st.session_state.enrich_count   = compute_enrich_count(
                target_table, where, params, enrich)
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
    st.markdown(
        "<span style='color:#94a3b8;font-size:.8rem;'>Ou ajouter comme condition dans l'arbre :</span>",
        unsafe_allow_html=True)
    join = st.radio("Lier avec", ["ET", "OU"], horizontal=True, key="dlg_join") \
        if st.session_state.conditions else "ET"
    if st.button("➕ Ajouter à l'arbre", width="stretch", key="dlg_add"):
        st.session_state.conditions.append({"column": col_name, "operator": op,
                                             "value": str_value, "join_op": join})
        st.rerun()
