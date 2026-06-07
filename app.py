"""
Point d'entrée de l'application SQL Query Builder.
"""
import os
import re
import uuid

import pandas as pd
import streamlit as st

from utils import OPERATORS, OP_LABELS, CONT_COLORS, TYPE_COLORS, is_date_col, _find_col
from db.demo import get_connection, _get_db
from query.builder import build_where, build_query, build_query_display
from query.joins import (get_available_joins, get_all_columns, get_column_labels,
                         compute_enrich_count, run_enrich_query)
from config.loader import load_config, CONFIG_PATH
from ui.styles import apply_styles
from ui.tree import render_tree
from ui.cards import render_client_profile_card, render_voyage_profile_card
from ui.components import render_table_summary, cell_filter_dialog
from modules.map import render_map_module
from modules.personnel import render_personnel_module
from modules.history import (_init_history_table, _db_push_history,
                              _render_history_popover)
from reports.search import _rapport_dialog


def run_app(schema: dict, enrich: dict):
    tables = {t: d["columns"] for t, d in schema.items()}
    st.session_state._app_tables = tables
    st.session_state._app_enrich = enrich

    default_table = next(iter(tables))
    for k, v in [("conditions", []), ("selected_table", default_table),
                 ("results", None), ("enrich_count", None),
                 ("last_where", ""), ("last_params", []), ("editing", {}),
                 ("joins", []), ("fiches_page", 0)]:
        if k not in st.session_state:
            st.session_state[k] = v

    conn    = get_connection()
    user_id = st.session_state.setdefault("user_id", str(uuid.uuid4())[:8])
    _init_history_table(conn)

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

    # ── En-tête + popover historique ─────────────────────────────────────────
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

    # ── Navigation principale ─────────────────────────────────────────────────
    app_mode   = st.session_state.get("app_mode", "query")
    _nav_pills = {"query": "🔍  Requêtes", "map": "🗺️  Carte", "personnel": "👥  Personnel"}
    nav_cols   = st.columns(len(_nav_pills) + 5)
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

    _summary_labels = schema.get(current_table, {}).get("labels", {}) or {}
    render_table_summary(current_table, tables[current_table], _summary_labels)

    available_joins = get_available_joins(schema, current_table, st.session_state.joins)

    if st.session_state.joins or available_joins:
        st.markdown(
            "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
            "letter-spacing:1px;font-family:JetBrains Mono,monospace;"
            "margin-bottom:6px;'>Sources de données</div>",
            unsafe_allow_html=True)

        n_active   = len(st.session_state.joins)
        n_avail    = len(available_joins)
        _pill_cols = st.columns([2] + [1.5] * n_active + [1.5] * n_avail + [4])

        _pill_cols[0].markdown(
            f"<div style='background:#1d4ed822;color:#93c5fd;"
            f"border:0.5px solid #1d4ed8;border-radius:20px;"
            f"padding:4px 12px;font-size:.8rem;text-align:center;"
            f"white-space:nowrap;'>🔒 {current_table}</div>",
            unsafe_allow_html=True)

        for _i, _j in enumerate(list(st.session_state.joins)):
            if _pill_cols[1 + _i].button(
                f"✕ {_j['table']}", key=f"del_join_{_i}",
                use_container_width=True, help=f"Retirer {_j['table']}",
            ):
                st.session_state.joins.pop(_i)
                st.session_state.conditions = []
                st.session_state.results    = None
                st.rerun()

        _off = 1 + n_active
        for _i, _aj in enumerate(available_joins):
            if _pill_cols[_off + _i].button(
                f"＋ {_aj['table']}", key=f"add_join_{_aj['table']}",
                use_container_width=True, help=f"Joindre {_aj['table']}  —  {_aj['on']}",
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

    if st.session_state.joins:
        current_cols = get_all_columns(schema, current_table, st.session_state.joins)
    else:
        current_cols = tables[current_table]

    col_labels_map = get_column_labels(schema, current_table, st.session_state.joins)

    if "pair_text_nonce" not in st.session_state:
        st.session_state.pair_text_nonce = 0

    st.markdown("### ➕ Ajouter un critère")

    crit_type = st.radio(
        "Type de critère",
        ["🔍 Simple", "🔗 Couples (col1, col2)"],
        horizontal=True, key="crit_type", label_visibility="collapsed",
    )
    is_pair_mode = crit_type.startswith("🔗")

    # ── Mode Simple ──────────────────────────────────────────────────────────
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
                    "Mode de date", ["📅 Date unique", "📆 Plage de dates"],
                    key="new_date_mode", horizontal=False, label_visibility="collapsed",
                )
            else:
                new_op = st.selectbox("Opérateur", OP_LABELS, key="new_op",
                                      label_visibility="collapsed")
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

    # ── Mode Couples ─────────────────────────────────────────────────────────
    else:
        pa, pb, pj = st.columns([2, 2, 1])
        with pa:
            _pair_col1 = st.selectbox(
                "1ère colonne", current_cols, key="pair_col1",
                format_func=lambda c: col_labels_map.get(c, c),
            )
        with pb:
            _other     = [c for c in current_cols if c != _pair_col1]
            _pair_col2 = st.selectbox(
                "2ème colonne", _other, key="pair_col2",
                format_func=lambda c: col_labels_map.get(c, c),
            )
        with pj:
            new_join = (st.radio("Lier", ["ET", "OU"], horizontal=False,
                                 key="new_join_pair", label_visibility="collapsed")
                        if st.session_state.conditions else "ET")

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
                f"Valeurs pour « {_label1} »", key=_key1, height=180,
                placeholder=f"Une valeur de {_label1} par ligne\nDupont\nMartin\nDurand",
            )
        with ta2:
            _pair_text2 = st.text_area(
                f"Valeurs pour « {_label2} »", key=_key2, height=180,
                placeholder=(f"Une valeur de {_label2} par ligne\n"
                             f"1985-03-15\n1990-07-22\n2001-12-04"
                             if is_date_col(_pair_col2)
                             else f"Une valeur de {_label2} par ligne"),
            )

        _lines1 = [ln.strip() for ln in _pair_text1.splitlines() if ln.strip()]
        _lines2 = [ln.strip() for ln in _pair_text2.splitlines() if ln.strip()]
        _n1, _n2 = len(_lines1), len(_lines2)

        if _n1 == 0 and _n2 == 0:
            st.markdown(
                "<div style='color:#475569;font-size:.78rem;font-style:italic;"
                "font-family:JetBrains Mono,monospace;margin:6px 0;'>"
                "En attente de valeurs dans les deux zones.</div>",
                unsafe_allow_html=True)
        elif _n1 != _n2:
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
                unsafe_allow_html=True)
        else:
            _preview_html = (
                f"<div style='background:#0f1e14;border:1px solid #14532d;"
                f"border-left:3px solid #4ade80;border-radius:8px;"
                f"padding:8px 14px;margin:6px 0;"
                f"font-family:JetBrains Mono,monospace;font-size:.78rem;color:#86efac;'>"
                f"✓ <b>{_n1} couple{'s' if _n1 > 1 else ''} prêt{'s' if _n1 > 1 else ''}</b> "
                f"à être ajouté{'s' if _n1 > 1 else ''}"
            )
            if _n1 > 0:
                _show   = list(zip(_lines1, _lines2))[:3]
                _items  = " · ".join(f"«{v1}»+«{v2}»" for v1, v2 in _show)
                _suffix = f" +{_n1 - 3} autres" if _n1 > 3 else ""
                _preview_html += f"&nbsp;&nbsp;<span style='color:#94a3b8;'>[{_items}{_suffix}]</span>"
            _preview_html += "</div>"
            st.markdown(_preview_html, unsafe_allow_html=True)

    btn_a, btn_b = st.columns([3, 1])
    with btn_a:
        if st.button("➕ Ajouter le critère", width="stretch", type="primary"):
            _cond = None

            if is_pair_mode:
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
                        f"Les deux zones doivent contenir le même nombre de lignes.")
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
                    print(_cond)
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
                                _s = _ds.strftime("%Y-%m-%d"); _e = _de.strftime("%Y-%m-%d")
                                _cond = {"column": new_col, "label": _new_label,
                                         "operator": "Entre", "value": (_s, _e),
                                         "is_date": True, "is_bulk": False, "is_range": True}
                        else:
                            st.warning("Veuillez sélectionner une date de début et une date de fin.")
                    else:
                        _bulk_raw = st.session_state.get("new_bulk_dates", "")
                        _single   = st.session_state.get("new_date")
                        if _bulk_raw:
                            _vals = [d.strip() for d in re.split(r"[,\n]", _bulk_raw) if d.strip()]
                            _dts  = []
                            for v in _vals:
                                if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
                                    _dts.append(v)
                                else:
                                    st.warning(f"Format de date invalide : {v}")
                            if _dts:
                                _cond = {"column": new_col, "label": _new_label,
                                         "operator": "Commence par",
                                         "value": ", ".join(_dts), "values": _dts,
                                         "is_date": True, "is_bulk": True}
                            else:
                                st.warning("Aucune date valide")
                        elif _single is not None:
                            _cond = {"column": new_col, "label": _new_label,
                                     "operator": "Commence par",
                                     "value": _single.strftime("%Y-%m-%d"),
                                     "is_date": True, "is_bulk": False}
                        else:
                            st.warning("Veuillez sélectionner une date.")
                else:
                    raw    = st.session_state.get("new_val", "")
                    values = [v.strip() for v in re.split(r"[,\n]", raw) if v.strip()]
                    if not values:
                        st.warning("Veuillez entrer au moins une valeur.")
                    elif len(values) == 1:
                        _cond = {"column": new_col, "label": _new_label, "operator": new_op,
                                 "value": values[0], "is_date": False, "is_bulk": False}
                    else:
                        _cond = {"column": new_col, "label": _new_label, "operator": new_op,
                                 "value": ", ".join(values), "values": values,
                                 "is_date": False, "is_bulk": True}

            if _cond is not None:
                if not st.session_state.conditions:
                    _cond["join_op"]   = "ET"
                    _cond["or_target"] = "leaf"
                    st.session_state.conditions.append(_cond)
                else:
                    _cond["join_op"] = new_join
                    if(len(st.session_state.conditions) > 1):
                        st.session_state._pending_cond = _cond
                    else :
                        st.session_state.conditions.append(_cond)
                if is_pair_mode:
                    st.session_state.pair_text_nonce += 1
                st.rerun()
    with btn_b:
        if st.button("🗑 Effacer", width="stretch"):
            st.session_state.conditions   = []
            st.session_state.results      = None
            st.session_state.enrich_count = None
            st.session_state.pair_text_nonce += 1
            st.session_state.pop("_pending_cond", None)
            st.rerun()

    st.markdown("---")

    col_tree, col_sql = st.columns([3, 2], gap="large")
    with col_tree:
        st.markdown("### 🌳 Arbre de décision")
        st.caption("Cliquez sur un nœud ET / OU pour le basculer.")
        render_tree(st.session_state.conditions, current_table)
    with col_sql:
        with st.expander("🧾 Voir la requête SQL générée", expanded=False):
            st.markdown(
                f"<div class='sql-display'>"
                f"{build_query_display(current_table, st.session_state.conditions, st.session_state.joins, schema)}"
                f"</div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        if st.button("▶ Exécuter la requête", width="stretch", type="primary"):
            q, params = build_query(current_table, st.session_state.conditions,
                                    st.session_state.joins, schema)
            try:
                results = _get_db().read_sql(q, params)
                st.session_state.results     = results
                st.session_state.fiches_page = 0
                where, wparams = build_where(st.session_state.conditions)
                st.session_state.last_where   = where
                st.session_state.last_params  = wparams
                st.session_state.enrich_count = compute_enrich_count(
                    current_table, where, wparams, enrich)
                st.session_state["_last_cell_click"] = None
                _db_push_history(conn, user_id, current_table,
                                 st.session_state.conditions, len(results),
                                 joins=st.session_state.joins)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur SQL : {e}")

    # ── Résultats ─────────────────────────────────────────────────────────────
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
        has_nom       = "nom"           in df.columns
        has_prenom    = "prenom"        in df.columns
        has_dest      = "destination"   in df.columns
        has_depart    = "date_depart"   in df.columns
        has_budget    = "budget"        in df.columns
        has_note      = "note"          in df.columns
        has_continent = "continent"     in df.columns
        has_type      = "type_voyage"   in df.columns
        has_duree     = "duree_jours"   in df.columns
        has_client_nom = "client_nom"   in df.columns
        has_ville      = "ville"        in df.columns
        has_client_id  = "client_id"    in df.columns

        tab1, tab2, tab3, tab4 = st.tabs(["📋 Grille", "👤 Fiches", "🗓 Timeline", "📈 Statistiques"])

        # ── TAB 1 — Grille ────────────────────────────────────────────────────
        with tab1:
            st.caption("💡 Cliquez sur une cellule pour explorer sa valeur.")
            event  = st.dataframe(df, width="stretch", hide_index=True,
                                  on_select="rerun",
                                  selection_mode=["single-row", "single-column"],
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

            _FICHES_PER_PAGE = 3

            def _page_bounds(total: int):
                n = max(1, (total + _FICHES_PER_PAGE - 1) // _FICHES_PER_PAGE)
                p = min(max(st.session_state.get("fiches_page", 0), 0), n - 1)
                st.session_state.fiches_page = p
                return p * _FICHES_PER_PAGE, min((p + 1) * _FICHES_PER_PAGE, total), p, n

            def _render_pagination(total, key, start, end, page, n_pages):
                pc1, pc2, pc3 = st.columns([1, 3, 1])
                with pc1:
                    if page > 0 and st.button(
                        "← Préc.", key=f"pag_prev_{key}", use_container_width=True,
                    ):
                        st.session_state.fiches_page = page - 1
                        st.rerun()
                with pc2:
                    suffix = f" · page <b>{page+1}</b>/{n_pages}" if n_pages > 1 else ""
                    st.markdown(
                        f"<div style='text-align:center;color:#94a3b8;font-size:.82rem;"
                        f"font-family:JetBrains Mono,monospace;padding:8px 0;'>"
                        f"<b style='color:#a5f3fc;'>{start+1}–{end}</b>"
                        f" / <b style='color:#86efac;'>{total}</b>{suffix}</div>",
                        unsafe_allow_html=True)
                with pc3:
                    if page < n_pages - 1 and st.button(
                        "Suiv. →", key=f"pag_next_{key}", use_container_width=True,
                    ):
                        st.session_state.fiches_page = page + 1
                        st.rerun()

            _prev_view = st.session_state.get("_tab2_view_prev", "client")
            _sel = st.radio(
                "Vue", ["👤  Client", "✈️  Voyage"],
                horizontal=True, label_visibility="collapsed", key="tab2_view_radio",
            )
            _view = "voyage" if "Voyage" in _sel else "client"
            if _view != _prev_view:
                st.session_state.fiches_page = 0
                st.session_state["_tab2_view_prev"] = _view

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

            if _view == "client":
                if has_nom and has_prenom and has_dest and _id_col:
                    _groups = list(df.groupby(_id_col, sort=False))
                    _total  = len(_groups)
                    _start, _end, _page, _npages = _page_bounds(_total)
                    for client_id, group in _groups[_start:_end]:
                        if _all_pp is not None:
                            try:
                                _cid = str(int(float(group.iloc[0].get(_id_col) or 0)))
                                _pp  = _all_pp[_all_pp["client_id"].astype(str) == _cid]
                            except Exception:
                                _pp = None
                        else:
                            _pp = None
                        render_client_profile_card(
                            client_row=group.iloc[0], voyages_df=group,
                            all_voyages_df=_all_voy, passeports_df=_pp,
                        )
                    _render_pagination(_total, "client_grouped", _start, _end, _page, _npages)

                elif has_nom and has_prenom:
                    _total  = len(df)
                    _start, _end, _page, _npages = _page_bounds(_total)
                    cols_grid = st.columns(2)
                    for i, (_, row) in enumerate(df.iloc[_start:_end].iterrows()):
                        _s_val     = row.get(_statut_col) if _statut_col else None
                        stat_color = "#4ade80" if str(_s_val or "") == "actif" else "#f87171"
                        initials   = (str(row.get("prenom","?"))[:1] + str(row.get("nom","?"))[:1]).upper()
                        cols_grid[i % 2].markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:12px;padding:16px 18px;margin-bottom:12px;'>"
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
                    _render_pagination(_total, "client_simple", _start, _end, _page, _npages)

                elif has_dest:
                    _total  = len(df)
                    _start, _end, _page, _npages = _page_bounds(_total)
                    cols_grid = st.columns(2)
                    for i, (_, row) in enumerate(df.iloc[_start:_end].iterrows()):
                        cont     = row.get("continent", ""); tv = row.get("type_voyage", "")
                        cont_col = CONT_COLORS.get(cont, "#6b7280")
                        tv_col   = TYPE_COLORS.get(tv, "#6b7280")
                        note_v   = row.get("note", None)
                        stars    = ("⭐" * int(note_v)) if note_v and not pd.isna(note_v) else "—"
                        cnom = ""
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
                    _render_pagination(_total, "client_dest", _start, _end, _page, _npages)
                else:
                    st.info("Aucune vue fiche disponible pour ces colonnes.")

            else:
                if has_dest:
                    _total  = len(df)
                    _start, _end, _page, _npages = _page_bounds(_total)
                    for _, vrow in df.iloc[_start:_end].iterrows():
                        render_voyage_profile_card(
                            voyage_row=vrow, all_voyages_df=_all_voy,
                            col_statut_client=_statut_col or "statut",
                            show_client_info=False,
                        )
                    _render_pagination(_total, "voyage", _start, _end, _page, _npages)
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
                    d_min = df_tl["date_depart"].min()
                    d_max = (df_tl["date_retour"].max()
                             if "date_retour" in df_tl.columns
                             else df_tl["date_depart"].max())
                    span  = max((d_max - d_min).days, 1)
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
                        cont     = row.get("continent", ""); tv = row.get("type_voyage", "")
                        cont_col = CONT_COLORS.get(cont, "#6b7280")
                        tv_col   = TYPE_COLORS.get(tv, "#6b7280")
                        note_v   = row.get("note", None)
                        stars    = "⭐" * int(note_v) if note_v and not pd.isna(note_v) else ""
                        cnom = ""
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
                        bgt_total = df["budget"].sum(); bgt_moy = df["budget"].mean()
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
                        d_moy = df["duree_jours"].mean(); d_max_v = df["duree_jours"].max()
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
                        st.markdown(
                            "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                            "letter-spacing:1px;margin-bottom:8px;'>Par continent</div>",
                            unsafe_allow_html=True)
                        bars = "".join(_hbar(c, v, n_total, CONT_COLORS.get(c, "#6b7280"))
                                       for c, v in df["continent"].value_counts().items())
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>{bars}</div>",
                            unsafe_allow_html=True)
                    if has_type:
                        st.markdown(
                            "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                            "letter-spacing:1px;margin-bottom:8px;'>Par type</div>",
                            unsafe_allow_html=True)
                        bars = "".join(_hbar(tv, v, n_total, TYPE_COLORS.get(tv, "#6b7280"))
                                       for tv, v in df["type_voyage"].value_counts().items())
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
                            f"border-radius:10px;padding:14px 18px;'>{bars}</div>",
                            unsafe_allow_html=True)
                if has_budget:
                    st.markdown(
                        "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                        "letter-spacing:1px;margin:14px 0 8px;'>Top destinations — budget</div>",
                        unsafe_allow_html=True)
                    top_dest = df.groupby("destination")["budget"].sum().sort_values(ascending=False).head(8)
                    max_b    = top_dest.max()
                    bars = "".join(
                        _hbar(dest, int(b), int(max_b),
                              CONT_COLORS.get(
                                  df[df["destination"]==dest]["continent"].iloc[0]
                                  if has_continent else "", "#6b7280"),
                              fmt=lambda x: f"{x:,}€")
                        for dest, b in top_dest.items()
                    )
                    st.markdown(
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
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
                        st.markdown(
                            "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                            "letter-spacing:1px;margin-bottom:8px;'>Par ville</div>",
                            unsafe_allow_html=True)
                        bars = "".join(_hbar(v, c, n_total, "#6366f1")
                                       for v, c in df[_ville_col].value_counts().head(8).items())
                        st.markdown(
                            f"<div style='background:#13151d;border:1px solid #1e2130;"
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

    # ── Enrichir ──────────────────────────────────────────────────────────────
    joined_tables = {j["table"] for j in st.session_state.joins}
    if enrich.get(current_table) and enrich[current_table]["other"] in joined_tables:
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
            width="stretch", key="enrich_btn",
        ):
            try:
                enriched = run_enrich_query(current_table,
                                            st.session_state.last_where,
                                            st.session_state.last_params, enrich)
                st.session_state.results      = enriched
                st.session_state.fiches_page  = 0
                st.session_state.enrich_count = "done"
                st.session_state["_last_cell_click"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Erreur enrichissement : {e}")


# ── Lancement ─────────────────────────────────────────────────────────────────
apply_styles()

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
