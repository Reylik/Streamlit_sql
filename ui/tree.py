"""
Rendu de l'arbre de conditions (composants Streamlit).
"""
import re
import streamlit as st

from utils import OP_LABELS, OP_NATURAL, _format_date_fr, _date_label, build_date_value
from query.builder import build_tree, build_preview_tree
from datetime import datetime

BRANCH_STYLES = {
    "ET": {"color": "#fca5a5", "bg": "#450a0a", "border": "#991b1b"},
    "OU": {"color": "#93c5fd", "bg": "#172554", "border": "#1d4ed8"},
}
NEUTRAL = "#475569"


def _leaf_html(conditions, idx):
    c           = conditions[idx]
    col_display = c.get("label", c["column"])

    if c.get("is_pair"):
        pairs = c.get("pairs", [])
        n     = len(pairs)
        col_labels = c.get("col_labels") or c["columns"]
        shown = pairs[:2]
        preview_items = [f"«{v1}·{v2}»" for v1, v2 in shown]
        preview = " · ".join(preview_items)
        suffix  = (f" <span style='color:#64748b;font-size:.75rem;'>+{n-2} autres</span>"
                   if n > 2 else "")
        return (f"<span class='t-leaf'>"
                f"<b style='color:#a5f3fc;'>{col_labels[0]} + {col_labels[1]}</b> "
                f"<span style='color:#fbbf24;'>parmi {n} couple{'s' if n > 1 else ''}</span> "
                f"<span style='color:#86efac;'>[{preview}{suffix}]</span>"
                f"</span>")

    if c.get("is_date"):
        if isinstance(c["value"], (tuple, list)) and len(c["value"]) == 2:
            date1, date2 = c["value"]
            return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{col_display}</b> "
                    f"<span style='color:#fbbf24;'>entre le</span> "
                    f"<span style='color:#86efac;'>{_format_date_fr(date1)}</span> "
                    f"<span style='color:#fbbf24;'>et le</span> "
                    f"<span style='color:#86efac;'>{_format_date_fr(date2)}</span></span>")
        else:
            return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{col_display}</b> "
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
                f"<b style='color:#a5f3fc;'>{col_display}</b> "
                f"<span style='color:#fbbf24;'>{op_str}</span> "
                f"<span style='color:#86efac;'>[{preview}{suffix}]</span>"
                f"</span>")

    op_str = OP_NATURAL.get(c["operator"], c["operator"])
    return (f"<span class='t-leaf'><b style='color:#a5f3fc;'>{col_display}</b> "
            f"<span style='color:#fbbf24;'>{op_str}</span> "
            f"<span style='color:#86efac;'>« {c['value']} »</span></span>")


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
    is_pair = cond.get("is_pair", False)

    if is_pair:
        pairs        = cond.get("pairs", [])
        col_labels   = cond.get("col_labels") or cond["columns"]
        current_text = "\n".join(f"{v1}, {v2}" for v1, v2 in pairs)
        st.text_area(
            f"Couples ({col_labels[0]}, {col_labels[1]})",
            value=current_text, key=f"epair_{idx}",
            height=140, label_visibility="visible",
            placeholder="Un couple par ligne, séparé par une virgule\nExemple :\nDupont, 1985-03-15\nMartin, 1990-07-22",
        )
        e1, e2 = st.columns([1, 1])
        with e1:
            if st.button("✓ Valider", key=f"eok_{idx}", width="stretch"):
                raw   = st.session_state.get(f"epair_{idx}", "")
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                new_pairs = []
                for ln in lines:
                    parts = [p.strip() for p in re.split(r"[,\t]", ln, maxsplit=1) if p.strip()]
                    if len(parts) == 2:
                        new_pairs.append((parts[0], parts[1]))
                if new_pairs:
                    st.session_state.conditions[idx]["pairs"] = new_pairs
                    st.session_state.editing.pop(idx, None)
                    st.rerun()
                else:
                    st.warning("Entrez au moins un couple valide « valeur1, valeur2 ».")
        with e2:
            if st.button("🗑 Supprimer", key=f"edel_{idx}", width="stretch"):
                st.session_state.conditions.pop(idx)
                st.session_state.editing.pop(idx, None)
                st.rerun()
        return

    if is_bulk:
        current_text = "\n".join(cond["values"])
        st.text_area("Valeurs", value=current_text, key=f"ev_{idx}",
                     height=110, label_visibility="collapsed",
                     placeholder="Une valeur par ligne, ou séparées par des virgules")
        e1, e2, e3 = st.columns([2, 1, 1])
        with e1:
            st.selectbox("Op", OP_LABELS,
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
        _val_is_range = (
            isinstance(cond["value"], (tuple, list)) and len(cond["value"]) == 2
        )

        def _date_str(v):
            if v is None:
                return "2023-01-01"
            if hasattr(v, "strftime"):
                return v.strftime("%Y-%m-%d")
            return str(v)

        if _val_is_range:
            _ref_start = _date_str(cond["value"][0])
            _ref_end   = _date_str(cond["value"][1])
        else:
            _ref_start = _date_str(cond["value"])
            _ref_end   = _ref_start

        em, ec1, ec2, ec3, ec4, ec5 = st.columns([1.6, 1.4, 1.0, 1.0, 0.45, 0.45])
        with em:
            date_mode = st.selectbox(
                "Mode", ["📅 Date unique", "📆 Plage de dates"],
                index=1 if _val_is_range else 0,
                key=f"date_mode_{idx}",
                label_visibility="collapsed",
            )
        is_range = date_mode == "📆 Plage de dates"

        if is_range:
            try:
                _ds = datetime.strptime(_ref_start, "%Y-%m-%d").date()
            except Exception:
                _ds = datetime(2023, 1, 1).date()
            try:
                _de = datetime.strptime(_ref_end, "%Y-%m-%d").date()
            except Exception:
                _de = _ds
            with ec1:
                st.date_input("Début", value=_ds, key=f"estart_{idx}",
                              label_visibility="collapsed")
            with ec2:
                st.date_input("Fin", value=_de, key=f"eend_{idx}",
                              label_visibility="collapsed")
        else:
            parts = _ref_start.split("-")
            cur_year  = int(parts[0]) if len(parts) >= 1 and parts[0].isdigit() else 2023
            cur_month = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
            cur_day   = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 0
            ec1.number_input("Année", 1900, 2100, cur_year, key=f"ey_{idx}",
                             label_visibility="collapsed")
            ec2.number_input("Mois", 0, 12, cur_month, key=f"em_{idx}",
                             label_visibility="collapsed")
            ec3.number_input("Jour", 0, 31, cur_day, key=f"ed_{idx}",
                             label_visibility="collapsed")

        with ec4:
            if st.button("✓", key=f"eok_{idx}", help="Valider"):
                if is_range:
                    _s = st.session_state.get(f"estart_{idx}")
                    _e = st.session_state.get(f"eend_{idx}")
                    if _s and _e and _s > _e:
                        st.warning("Date de début > date de fin.")
                    else:
                        st.session_state.conditions[idx]["value"] = (
                            _s.strftime("%Y-%m-%d") if _s else "",
                            _e.strftime("%Y-%m-%d") if _e else "",
                        )
                        st.session_state.conditions[idx]["is_range"] = True
                        st.session_state.conditions[idx].pop("values", None)
                        st.session_state.editing.pop(idx, None)
                        st.rerun()
                else:
                    st.session_state.conditions[idx]["value"] = build_date_value(
                        int(st.session_state.get(f"ey_{idx}", 2023)),
                        int(st.session_state.get(f"em_{idx}", 0)),
                        int(st.session_state.get(f"ed_{idx}", 0)),
                    )
                    st.session_state.conditions[idx]["is_range"] = False
                    st.session_state.editing.pop(idx, None)
                    st.rerun()
        with ec5:
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


def _first_leaf_idx(node):
    if node["type"] == "leaf":
        return node["idx"]
    if node["type"] == "or_group":
        return node["children"][0]["idx"]
    return _first_leaf_idx(node["left"])


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


def _render_node(node, conditions, prefix_parts=None, is_last=True, is_root=False, parent_op=None):
    if prefix_parts is None:
        prefix_parts = []
    connector       = "" if is_root else ("└── " if is_last else "├── ")
    connector_color = BRANCH_STYLES[parent_op]["color"] if parent_op else NEUTRAL
    prefix_len      = sum(len(t) for t, _ in prefix_parts) + len(connector)
    ph              = _prefix_html(prefix_parts, connector, connector_color)

    if node["type"] == "ghost":
        pending = node["pending"]
        target  = node["target"]
        oc      = BRANCH_STYLES[pending["join_op"]]["border"]
        m       = f"ghost-{target}"
        css = (
            f'<div id="{m}"></div><style>'
            f"div.element-container:has(#{m})+div.element-container button{{"
            f"background:transparent!important;color:#cbd5e1!important;"
            f"border:1px dashed {oc}!important;border-radius:5px!important;"
            f"font-family:'JetBrains Mono',monospace!important;font-size:.78rem!important;"
            f"opacity:.55!important;padding:3px 10px!important;min-height:0!important;"
            f"text-align:left!important;justify-content:flex-start!important;}}"
            f"div.element-container:has(#{m})+div.element-container button:hover{{"
            f"opacity:1!important;background:{oc}1a!important;"
            f"box-shadow:0 0 10px {oc}66!important;}}"
            f"div.element-container:has(#{m})+div.element-container button p{{"
            f"text-align:left!important;}}</style>"
        )
        tip = ("Relier à la dernière feuille" if target == "leaf"
               else "Créer une nouvelle branche au sommet")
        _coldisp = pending.get("label", pending["column"])
        if pending.get("is_pair"):
            _n = len(pending.get("pairs", []))
            cond_txt = f"{_coldisp} parmi {_n} couple{'s' if _n > 1 else ''}"
        elif pending.get("is_date"):
            if isinstance(pending["value"], (tuple, list)) and len(pending["value"]) == 2:
                d1, d2 = pending["value"]
                cond_txt = f"{_coldisp} entre le {_format_date_fr(d1)} et le {_format_date_fr(d2)}"
            else:
                cond_txt = f"{_coldisp} en {_date_label(pending['value'])}"
        elif pending.get("is_bulk"):
            _ops  = OP_NATURAL.get(pending["operator"], pending["operator"])
            _vals = pending.get("values", [])
            _prev = " · ".join(f"«{v}»" for v in _vals[:3])
            _suf  = f" +{len(_vals)-3}" if len(_vals) > 3 else ""
            cond_txt = f"{_coldisp} {_ops} [{_prev}{_suf}]"
        else:
            _ops = OP_NATURAL.get(pending["operator"], pending["operator"])
            cond_txt = f"{_coldisp} {_ops} « {pending.get('value','')} »"
        btn_label = f"＋ {cond_txt}"

        def _do_click():
            st.session_state.conditions.append(dict(pending, or_target=target))
            st.session_state.pop("_pending_cond", None)
            st.rerun()

        if ph:
            w = max(prefix_len * 0.135, 0.35)
            ca, cb = st.columns([w, max(9 - w, 1)])
            ca.markdown(f"<div style='padding-top:7px;line-height:1;'>{ph}</div>",
                        unsafe_allow_html=True)
            with cb:
                st.markdown(css, unsafe_allow_html=True)
                if st.button(btn_label, key=f"_ghostbtn_{target}",
                             help=tip, use_container_width=True):
                    _do_click()
        else:
            st.markdown(css, unsafe_allow_html=True)
            if st.button(btn_label, key=f"_ghostbtn_{target}",
                         help=tip, use_container_width=True):
                _do_click()
        return

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

    elif node["type"] == "or_group":
        children = node["children"]
        sub = children[0]
        for child in children[1:]:
            sub = {"type": "branch", "op": "OU", "left": sub, "right": child}
        _render_node(sub, conditions, prefix_parts, is_last=is_last,
                     is_root=is_root, parent_op=parent_op)

    else:
        op = node["op"]
        if node.get("ghost"):
            oc = BRANCH_STYLES[op]["border"]
            op_html = (f"<span style='font-family:JetBrains Mono,monospace;"
                       f"font-size:.78rem;color:{oc};opacity:.55;"
                       f"border:1px dashed {oc};border-radius:4px;"
                       f"padding:1px 9px;'>{op}</span>")
            if ph:
                st.markdown(f"<div style='padding-top:5px;'>{ph}{op_html}</div>",
                            unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding-top:2px;'>{op_html}</div>",
                            unsafe_allow_html=True)
        else:
            right_idx = _first_leaf_idx(node["right"])
            if ph:
                w = max(prefix_len * 0.135, 0.35)
                ca, cb = st.columns([w, max(9 - w, 1)])
                ca.markdown(f"<div style='padding-top:8px;line-height:1;'>{ph}</div>",
                            unsafe_allow_html=True)
                with cb:
                    _branch_button(op, right_idx)
            else:
                _branch_button(op, right_idx)

        new_pfx = (prefix_parts if is_root else
                   prefix_parts + [("│   ", connector_color)] if not is_last else
                   prefix_parts + [("    ", connector_color)])
        _render_node(node["left"],  conditions, new_pfx, is_last=False, parent_op=op)
        _render_node(node["right"], conditions, new_pfx, is_last=True,  parent_op=op)


def render_tree(conditions, table):
    st.markdown(
        f"<div class='tree-wrap'>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>Requête</span>"
        f"<div style='margin:6px 0 12px;'><span class='t-root'>SELECT * FROM {table}</span></div>"
        f"<span style='color:#94a3b8;font-size:.72rem;font-family:JetBrains Mono,monospace;"
        f"text-transform:uppercase;letter-spacing:1px;'>WHERE</span></div>",
        unsafe_allow_html=True)

    _pending = st.session_state.get("_pending_cond")
    if _pending and conditions:
        tree = build_preview_tree(conditions, _pending)
    else:
        tree = build_tree(conditions)

    if tree is None:
        st.markdown("<p style='color:#4a5170;font-style:italic;font-size:.85rem;'>Aucune condition.</p>",
                    unsafe_allow_html=True)
        return

    _render_node(tree, conditions, prefix_parts=[], is_last=True, is_root=True, parent_op=None)

    if _pending:
        st.markdown(
            "<div style='margin-top:8px;color:#64748b;font-size:.72rem;"
            "font-family:JetBrains Mono,monospace;'>"
            "↑ Cliquez un emplacement fantôme (pointillés) pour valider</div>",
            unsafe_allow_html=True)
        _mc = "gh-cancel"
        st.markdown(
            f'<div id="{_mc}"></div><style>'
            f"div.element-container:has(#{_mc})+div.element-container button{{"
            f"background:transparent!important;color:#475569!important;border:none!important;"
            f"font-size:.72rem!important;min-height:0!important;padding:2px!important;}}"
            f"div.element-container:has(#{_mc})+div.element-container button:hover{{"
            f"color:#94a3b8!important;}}</style>",
            unsafe_allow_html=True)
        if st.button("✕ annuler", key="_place_cancel"):
            st.session_state.pop("_pending_cond", None)
            st.rerun()
