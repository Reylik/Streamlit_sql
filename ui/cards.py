"""
Fiches profil client et voyage.
"""
import math
import pandas as pd
import streamlit as st

from utils import CONT_COLORS, TYPE_COLORS


def _safe_get(data, col, default="—"):
    """Accède à data[col] de manière résiliente (dict, pd.Series)."""
    if data is None:
        return default
    try:
        if hasattr(data, "get") and callable(data.get):
            val = data.get(col)
        elif hasattr(data, "index") and col in data.index:
            val = data[col]
        else:
            return default
    except (KeyError, IndexError, TypeError):
        return default
    if val is None:
        return default
    try:
        if math.isnan(float(val)):
            return default
    except (ValueError, TypeError):
        pass
    if str(val).strip() == "":
        return default
    return val


def render_client_profile_card(
    client_row,
    voyages_df=None,
    all_voyages_df=None,
    passeports_df=None,
    col_nom="nom", col_prenom="prenom", col_email="email",
    col_telephone="telephone", col_ville="ville", col_statut="statut",
    col_date_inscription="date_inscription",
    col_num_ci="num_carte_identite",
    col_exp_ci="date_expiration_ci",
    col_pp_num="num_passeport",
    col_pp_nat="nationalite",
    col_pp_emission="date_emission",
    col_pp_expiration="date_expiration",
    col_profession="profession", col_employeur="employeur",
    col_situation_pro="situation_pro",
    col_v_destination="destination", col_v_pays="pays_destination",
    col_v_continent="continent",    col_v_date_dep="date_depart",
    col_v_date_ret="date_retour",   col_v_duree="duree_jours",
    col_v_type="type_voyage",       col_v_transport="transport",
    col_v_hotel="hotel",            col_v_budget="budget",
    col_v_statut="statut_voyage",   col_v_note="note",
    col_v_groupe="groupe_voyage_id",
    col_c_client_id="client_id", col_c_nom="nom", col_c_prenom="prenom",
    col_c_profession="profession", col_c_ville="ville", col_c_statut="statut",
    show_identity=True, show_professional=True, show_companions=True,
):
    sg = lambda col, d="—": _safe_get(client_row, col, d)

    nom     = sg(col_nom);        prenom = sg(col_prenom)
    ville   = sg(col_ville, "");  statut = sg(col_statut, "")
    email   = sg(col_email, "");  tel    = sg(col_telephone, "")
    ini     = ((prenom[:1] if prenom and prenom != "—" else "") +
               (nom[:1]   if nom    and nom    != "—" else "")).upper() or "?"
    sc      = "#4ade80" if statut == "actif" else "#f87171"
    contact_html = ""
    if email: contact_html += f"<div style='font-size:.72rem;'>{email}</div>"
    if tel:   contact_html += f"<div style='font-size:.72rem;color:#64748b;'>{tel}</div>"

    id_section = ""
    if show_identity:
        ci_num = sg(col_num_ci, ""); ci_exp = sg(col_exp_ci, "")
        id_rows = []
        if passeports_df is not None and not passeports_df.empty:
            from datetime import date as _date
            _today = _date.today().isoformat()
            pp_tags = []
            for _, pp in passeports_df.iterrows():
                num  = _safe_get(pp, col_pp_num, "?")
                nat  = _safe_get(pp, col_pp_nat, "")
                emis = _safe_get(pp, col_pp_emission, "")
                exp  = _safe_get(pp, col_pp_expiration, "")
                expired = bool(exp and exp != "—" and str(exp) < _today)
                bg  = "#450a0a" if expired else "#052e16"
                fg  = "#fca5a5" if expired else "#86efac"
                brd = "#ef4444" if expired else "#22c55e"
                icon = '✗' if expired else '✓'
                lbl  = f"{icon} {num}"
                pp_tags.append(
                    f"<span class='pp-wrap' style='position:relative;display:inline-block;margin:1px;'>"
                    f"<span style='background:{bg};color:{fg};"
                    f"border:0.5px solid {brd};font-size:.7rem;padding:2px 8px;"
                    f"border-radius:20px;cursor:help;"
                    f"font-family:JetBrains Mono,monospace;display:inline-block;'>{lbl}</span>"
                    f"<span class='pp-tip'>"
                    f"<b>Nationalité</b>&nbsp;&nbsp;{nat}<br>"
                    f"<b>Émis</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{emis}<br>"
                    f"<b>Expiration</b>&nbsp;&nbsp;{exp}"
                    f"</span></span>"
                )
            if pp_tags:
                id_rows.append(("Passeports", " ".join(pp_tags)))
        if ci_num:
            id_rows.append(("Carte d'identité",
                            ci_num + (f"  ·  exp. {ci_exp}" if ci_exp else "")))
        id_body = "".join(
            f"<div style='display:flex;gap:8px;padding:5px 0;border-top:1px solid #1e2130;'>"
            f"<span style='color:#64748b;font-size:.72rem;min-width:100px;flex-shrink:0;'>{k}</span>"
            f"<span style='color:#e8eaf0;font-size:.78rem;font-family:JetBrains Mono,monospace;'>{v}</span>"
            f"</div>"
            for k, v in id_rows
        ) if id_rows else "<span style='color:#334155;font-size:.75rem;font-style:italic;'>Non renseigné</span>"
        _pp_css = (
            "<style>.pp-wrap{position:relative;display:inline-block;}"
            ".pp-tip{visibility:hidden;opacity:0;transition:opacity .12s;"
            "position:absolute;bottom:calc(100% + 6px);left:0;z-index:9999;"
            "background:#0f111a;border:0.5px solid #2a2d3e;border-radius:8px;"
            "padding:9px 13px;font-size:11px;color:#e8eaf0;line-height:1.8;"
            "white-space:nowrap;pointer-events:none;"
            "font-family:JetBrains Mono,monospace;box-shadow:0 4px 16px #00000088;}"
            ".pp-wrap:hover .pp-tip{visibility:visible;opacity:1;}</style>"
        )
        id_section = (
            _pp_css + f"<div style='flex:1;padding:11px 16px;"
            + ("border-right:0.5px solid #1e2130;" if show_professional else "")
            + f"'>"
            f"<div style='color:#a78bfa;font-size:.68rem;text-transform:uppercase;"
            f"letter-spacing:1px;font-family:JetBrains Mono,monospace;"
            f"margin-bottom:7px;'>Papiers d'identité</div>{id_body}</div>"
        )

    pro_section = ""
    if show_professional:
        prof = sg(col_profession, ""); emp = sg(col_employeur, "")
        sit  = sg(col_situation_pro, "")
        pro_rows = []
        if prof: pro_rows.append(("Profession", prof))
        if emp:  pro_rows.append(("Employeur",  emp))
        if sit:  pro_rows.append(("Contrat",    sit))
        pro_body = "".join(
            f"<div style='display:flex;gap:8px;padding:5px 0;border-top:1px solid #1e2130;'>"
            f"<span style='color:#64748b;font-size:.72rem;min-width:85px;flex-shrink:0;'>{k}</span>"
            f"<span style='color:#e8eaf0;font-size:.78rem;'>{v}</span></div>"
            for k, v in pro_rows
        ) if pro_rows else "<span style='color:#334155;font-size:.75rem;font-style:italic;'>Non renseigné</span>"
        pro_section = (
            f"<div style='flex:1;padding:11px 16px;'><div style='color:#60a5fa;font-size:.68rem;"
            f"text-transform:uppercase;letter-spacing:1px;font-family:JetBrains Mono,monospace;"
            f"margin-bottom:7px;'>Situation professionnelle</div>{pro_body}</div>"
        )

    idpro_html = ""
    if show_identity or show_professional:
        idpro_html = (
            f"<div style='display:flex;border-top:0.5px solid #1e2130;'>{id_section}{pro_section}</div>"
        )
    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;"
        f"border-radius:12px 12px 0 0;border-bottom:none;'>"
        f"<div style='padding:14px 20px 10px;display:flex;align-items:center;gap:14px;'>"
        f"<div style='width:44px;height:44px;border-radius:50%;"
        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-weight:700;font-size:.95rem;color:white;flex-shrink:0;'>{ini}</div>"
        f"<div style='flex:1;'>"
        f"<div style='font-weight:700;font-size:.95rem;color:#e8eaf0;'>{prenom} {nom}</div>"
        f"<div style='color:#64748b;font-size:.78rem;margin-top:1px;'>"
        f"{(''+ville+' &nbsp;·&nbsp; ' if ville else '')}"
        f"<span style='color:{sc};'>{statut}</span></div></div>"
        f"<div style='text-align:right;color:#94a3b8;'>{contact_html}</div>"
        f"</div>"
        f"{idpro_html}"
        f"</div>",
        unsafe_allow_html=True)

    if voyages_df is None or (hasattr(voyages_df, "empty") and voyages_df.empty):
        st.markdown(
            "<div style='background:#13151d;border:1px solid #1e2130;"
            "border-top:none;border-radius:0 0 12px 12px;padding:12px 16px;"
            "color:#334155;font-size:.8rem;font-style:italic;'>"
            "Aucun voyage enregistré.</div>"
            "<div style='margin-bottom:14px'></div>",
            unsafe_allow_html=True)
        return

    n_v = len(voyages_df)
    _own_id = _safe_get(client_row, "id", None)
    if _own_id in ("—", None):
        _own_id = _safe_get(client_row, "clients_id", None)

    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;"
        f"border-top:1px solid #2a2d3e;padding:7px 16px;'>"
        f"<span style='color:#94a3b8;font-size:.68rem;text-transform:uppercase;"
        f"letter-spacing:1px;font-family:JetBrains Mono,monospace;'>"
        f"{n_v} voyage{'s' if n_v > 1 else ''}</span></div>",
        unsafe_allow_html=True)

    vrows = list(voyages_df.iterrows())
    for vi, (_, vrow) in enumerate(vrows):
        vsg     = lambda col, d="—": _safe_get(vrow, col, d)
        is_last = vi == len(vrows) - 1
        br      = "border-radius:0 0 12px 12px;" if is_last else ""
        dest     = vsg(col_v_destination);  pays   = vsg(col_v_pays, "")
        cont     = vsg(col_v_continent, ""); tv     = vsg(col_v_type, "")
        date_dep = str(vsg(col_v_date_dep, ""))[:10]
        date_ret = str(vsg(col_v_date_ret, ""))[:10]
        duree    = vsg(col_v_duree, None)
        note_v   = vsg(col_v_note, None)
        gid      = vsg(col_v_groupe, None)
        cc       = CONT_COLORS.get(cont, "#6b7280")
        tc       = TYPE_COLORS.get(tv,   "#6b7280")
        try:    stars = "⭐" * int(float(note_v)) if note_v and note_v != "—" else ""
        except: stars = ""

        companions = []
        if show_companions and gid and gid != "—" and all_voyages_df is not None:
            try:
                gid_int = int(float(gid))
                cdf = all_voyages_df[
                    all_voyages_df[col_v_groupe].apply(
                        lambda x: int(float(x)) == gid_int
                        if pd.notna(x) and x != "" else False
                    )
                ]
                if _own_id not in ("—", None):
                    cdf = cdf[cdf[col_c_client_id].astype(str)
                              != str(int(float(_own_id)))]
                seen = set()
                for _, cr in cdf.iterrows():
                    cid_ = str(_safe_get(cr, col_c_client_id, ""))
                    if cid_ not in seen:
                        seen.add(cid_)
                        companions.append((
                            _safe_get(cr, col_c_prenom,    ""),
                            _safe_get(cr, col_c_nom,       ""),
                            _safe_get(cr, col_c_profession,""),
                            _safe_get(cr, col_c_ville,     ""),
                            _safe_get(cr, col_c_statut,    ""),
                        ))
            except Exception:
                companions = []

        last_border = f"border-bottom:1px solid #1e2130;{br}" if is_last else ""
        col_voy, col_comp = st.columns([9.5, 1.5])
        with col_voy:
            d_str = f"  ·  {int(float(duree))}j" if duree and duree != "—" else ""
            st.markdown(
                f"<div style='background:#13151d;"
                f"border-left:1px solid #1e2130;border-right:1px solid #1e2130;"
                f"{last_border}padding:8px 16px;'>"
                f"<div style='display:flex;align-items:center;gap:8px;"
                f"border-top:1px solid #1e2130;padding-top:6px;'>"
                f"<div style='width:3px;height:26px;border-radius:2px;"
                f"background:{cc};flex-shrink:0;'></div>"
                f"<div style='flex:1;'>"
                f"<span style='color:#e8eaf0;font-weight:600;font-size:.85rem;'>{dest}</span>"
                f"<span style='color:#475569;font-size:.73rem;margin-left:8px;'>"
                f"{pays}{'  ·  ' if pays else ''}{date_dep}"
                f"{'  →  '+date_ret if date_ret and date_ret != date_dep else ''}"
                f"{d_str}</span></div>"
                f"<span style='background:{tc}22;color:{tc};font-size:.68rem;"
                f"padding:2px 7px;border-radius:10px;white-space:nowrap;'>{tv}</span>"
                f"{'<span style=\"font-size:.72rem;margin-left:4px;\">'+stars+'</span>' if stars else ''}"
                f"</div></div>",
                unsafe_allow_html=True)

        with col_comp:
            _self = (
                _safe_get(client_row, col_prenom,     ""),
                _safe_get(client_row, col_nom,        ""),
                _safe_get(client_row, col_profession, ""),
                _safe_get(client_row, col_ville,      ""),
                _safe_get(client_row, col_statut,     ""),
            )
            all_members = [_self] + companions
            if len(all_members) <= 1:
                st.markdown(
                    "<div style='display:flex;align-items:center;justify-content:center;"
                    "height:36px;border:1px solid #1e2130;border-radius:6px;"
                    "color:#334155;font-size:.83rem;cursor:not-allowed;user-select:none;'>"
                    f"👥 {len(all_members)}</div>",
                    unsafe_allow_html=True)
            else:
                with st.popover(f"👥 {len(all_members)}", use_container_width=True):
                    st.markdown(
                        f"<div style='font-size:.7rem;text-transform:uppercase;"
                        f"letter-spacing:1px;font-family:JetBrains Mono,monospace;"
                        f"color:#94a3b8;margin-bottom:8px;'>"
                        f"{len(all_members)} participant"
                        f"{'s' if len(all_members)>1 else ''}</div>",
                        unsafe_allow_html=True)
                    for mp, mn, mprof, mvil, mstat in all_members:
                        cp_ini = ((mp[:1] if mp else "")+(mn[:1] if mn else "")).upper() or "?"
                        sc2    = "#4ade80" if mstat == "actif" else "#f87171"
                        meta   = "  ·  ".join(filter(None, [mprof, mvil]))
                        st.markdown(
                            f"<div style='display:flex;align-items:flex-start;gap:10px;"
                            f"padding:8px 0;border-top:1px solid #1e2130;'>"
                            f"<div style='width:32px;height:32px;border-radius:50%;"
                            f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                            f"display:flex;align-items:center;justify-content:center;"
                            f"font-weight:700;font-size:.72rem;color:white;"
                            f"flex-shrink:0;margin-top:1px;'>{cp_ini}</div>"
                            f"<div style='flex:1;'>"
                            f"<div style='font-weight:600;font-size:.85rem;color:#e8eaf0;'>"
                            f"{mp} {mn}</div>"
                            f"{'<div style=\"font-size:.72rem;color:#64748b;margin-top:2px;\">' + meta + '</div>' if meta else ''}"
                            f"<div style='margin-top:3px;'>"
                            f"<span style='font-size:.68rem;padding:1px 7px;border-radius:20px;"
                            f"background:{sc2}22;color:{sc2};'>{mstat or '—'}</span>"
                            f"</div></div></div>",
                            unsafe_allow_html=True)

        if is_last:
            st.markdown(
                "<div style='background:#13151d;border:1px solid #1e2130;"
                "border-top:none;border-radius:0 0 12px 12px;height:6px;'></div>",
                unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:14px'></div>", unsafe_allow_html=True)


def render_voyage_profile_card(
    voyage_row,
    all_voyages_df=None,
    col_destination="destination",  col_pays="pays_destination",
    col_continent="continent",      col_date_dep="date_depart",
    col_date_ret="date_retour",     col_duree="duree_jours",
    col_type="type_voyage",         col_transport="transport",
    col_hotel="hotel",
    col_statut="statut",            col_note="note",
    col_groupe="groupe_voyage_id",  col_client_id="client_id",
    col_nom="nom",                  col_prenom="prenom",
    col_ville="ville",              col_statut_client="statut",
    col_profession="profession",
    col_m_client_id="client_id",   col_m_nom="nom",
    col_m_prenom="prenom",         col_m_profession="profession",
    col_m_ville="ville",           col_m_statut="statut",
    show_client_info=True,
):
    vsg = lambda col, d="—": _safe_get(voyage_row, col, d)

    dest     = vsg(col_destination)
    pays     = vsg(col_pays,     "")
    cont     = vsg(col_continent,"")
    date_dep = str(vsg(col_date_dep, ""))[:10]
    date_ret = str(vsg(col_date_ret, ""))[:10]
    duree    = vsg(col_duree,    None)
    tv       = vsg(col_type,     "")
    transport= vsg(col_transport,"")
    hotel    = vsg(col_hotel,    "")
    statut   = vsg(col_statut,   "")
    note_v   = vsg(col_note,     None)
    gid      = vsg(col_groupe,   None)
    own_cid  = vsg(col_client_id,None)

    cc  = CONT_COLORS.get(cont, "#6b7280")
    tc  = TYPE_COLORS.get(tv,   "#6b7280")
    try:   stars = "⭐" * int(float(note_v)) if note_v and note_v != "—" else ""
    except: stars = ""
    sv_col = {"terminé":"#4ade80","à venir":"#fbbf24","annulé":"#f87171"}.get(statut,"#94a3b8")

    d_str  = f"{int(float(duree))}j" if duree and duree != "—" else ""
    dt_str = f"{date_dep} → {date_ret}" if date_ret and date_ret != date_dep else date_dep

    nom_c    = vsg(col_nom,     "")
    prenom_c = vsg(col_prenom,  "")
    members  = []
    if nom_c or prenom_c:
        members.append((prenom_c, nom_c,
                         vsg(col_profession,""), vsg(col_ville,""),
                         vsg(col_statut_client,"")))

    if gid and gid != "—" and all_voyages_df is not None:
        try:
            gid_int = int(float(gid))
            cdf = all_voyages_df[
                all_voyages_df[col_groupe].apply(
                    lambda x: int(float(x)) == gid_int
                    if pd.notna(x) and x != "" else False)]
            if own_cid not in ("—", None):
                cdf = cdf[cdf[col_m_client_id].astype(str) != str(int(float(own_cid)))]
            seen = set()
            for _, cr in cdf.iterrows():
                cid_ = str(_safe_get(cr, col_m_client_id, ""))
                if cid_ not in seen:
                    seen.add(cid_)
                    members.append((
                        _safe_get(cr, col_m_prenom,    ""),
                        _safe_get(cr, col_m_nom,       ""),
                        _safe_get(cr, col_m_profession,""),
                        _safe_get(cr, col_m_ville,     ""),
                        _safe_get(cr, col_m_statut,    ""),
                    ))
        except Exception:
            pass

    n_mbr = len(members)
    meta  = "  ·  ".join(filter(None, [pays, cont, d_str, dt_str]))
    ht    = "  ·  ".join(filter(None, [
        f"🏨 {hotel}"     if hotel     and hotel     != "—" else "",
        f"✈️ {transport}" if transport and transport != "—" else "",
    ]))

    _ht_html    = (f"<div style='color:#94a3b8;font-size:.75rem;margin-top:2px;'>{ht}</div>"
                   if ht else "")
    _stars_html = (f"<div style='font-size:.8rem;flex-shrink:0;'>{stars}</div>"
                   if stars else "")
    st.markdown(
        f"<div style='background:#13151d;border:1px solid #1e2130;"
        f"border-bottom:none;border-radius:12px 12px 0 0;"
        f"border-left:4px solid {cc};padding:13px 20px 10px;'>"
        f"<div style='display:flex;align-items:flex-start;"
        f"justify-content:space-between;gap:8px;'>"
        f"<div>"
        f"<div style='font-weight:700;font-size:1rem;color:#e8eaf0;'>{dest}</div>"
        f"<div style='color:#64748b;font-size:.77rem;margin-top:3px;'>{meta}</div>"
        f"{_ht_html}"
        f"</div>"
        f"{_stars_html}"
        f"</div></div>",
        unsafe_allow_html=True)

    col_tg, col_mb = st.columns([8, 2])
    with col_tg:
        t1 = (f"<span style='background:{tc}22;color:{tc};font-size:.7rem;"
              f"padding:2px 8px;border-radius:10px;margin-right:5px;'>{tv}</span>" if tv else "")
        t2 = (f"<span style='background:{sv_col}22;color:{sv_col};font-size:.7rem;"
              f"padding:2px 8px;border-radius:10px;'>{statut}</span>" if statut else "")
        st.markdown(
            f"<div style='background:#13151d;border-left:1px solid #1e2130;"
            f"border-right:1px solid #1e2130;border-top:1px solid #1e2130;"
            f"padding:7px 16px;min-height:36px;display:flex;align-items:center;'>"
            f"{t1}{t2}</div>",
            unsafe_allow_html=True)

    with col_mb:
        if members:
            with st.popover(f"👥 {n_mbr}", use_container_width=True):
                st.markdown(
                    f"<div style='font-size:.7rem;text-transform:uppercase;"
                    f"letter-spacing:1px;font-family:JetBrains Mono,monospace;"
                    f"color:#94a3b8;margin-bottom:8px;'>"
                    f"{n_mbr} participant{'s' if n_mbr > 1 else ''}</div>",
                    unsafe_allow_html=True)
                for mp, mn, mprof, mvil, mstat in members:
                    m_ini = ((mp[:1] if mp else "")+(mn[:1] if mn else "")).upper() or "?"
                    m_sc  = "#4ade80" if mstat=="actif" else ("#f87171" if mstat=="inactif" else "#94a3b8")
                    m_meta= "  ·  ".join(filter(None, [mprof, mvil]))
                    st.markdown(
                        f"<div style='display:flex;align-items:flex-start;gap:10px;"
                        f"padding:7px 0;border-top:1px solid #1e2130;'>"
                        f"<div style='width:30px;height:30px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;font-size:.7rem;color:white;"
                        f"flex-shrink:0;margin-top:1px;'>{m_ini}</div>"
                        f"<div style='flex:1;'>"
                        f"<div style='font-weight:600;font-size:.83rem;color:#e8eaf0;'>"
                        f"{mp} {mn}</div>"
                        f"{'<div style=\"font-size:.72rem;color:#64748b;margin-top:1px;\">' + m_meta + '</div>' if m_meta else ''}"
                        f"{'<div style=\"margin-top:2px;\"><span style=\"font-size:.68rem;padding:1px 7px;border-radius:20px;background:'+m_sc+'22;color:'+m_sc+';\">'+mstat+'</span></div>' if mstat and mstat != '—' else ''}"
                        f"</div></div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='display:flex;align-items:center;justify-content:center;"
                "height:36px;border:1px solid #1e2130;border-radius:6px;"
                "color:#334155;font-size:.83rem;cursor:not-allowed;user-select:none;'>"
                "👥 0</div>",
                unsafe_allow_html=True)

    if show_client_info and (nom_c or prenom_c):
        sc_c  = "#4ade80" if vsg(col_statut_client) == "actif" else "#f87171"
        ini_c = ((prenom_c[:1] if prenom_c else "")+(nom_c[:1] if nom_c else "")).upper() or "?"
        meta_c = "  ·  ".join(filter(None, [vsg(col_profession,""), vsg(col_ville,"")]))
        st.markdown(
            f"<div style='background:#13151d;border:1px solid #1e2130;"
            f"border-top:1px solid #2a2d3e;border-radius:0 0 12px 12px;"
            f"padding:8px 16px;display:flex;align-items:center;gap:10px;'>"
            f"<div style='width:28px;height:28px;border-radius:50%;"
            f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-weight:700;font-size:.7rem;color:white;flex-shrink:0;'>{ini_c}</div>"
            f"<div style='flex:1;'>"
            f"<span style='font-weight:600;font-size:.84rem;color:#e8eaf0;'>"
            f"{prenom_c} {nom_c}</span>"
            f"{'<span style=\"font-size:.72rem;color:#64748b;margin-left:8px;\">' + meta_c + '</span>' if meta_c else ''}"
            f"</div>"
            f"<span style='font-size:.68rem;padding:2px 8px;border-radius:20px;"
            f"background:{sc_c}22;color:{sc_c};'>{vsg(col_statut_client,'')}</span>"
            f"</div>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#13151d;border:1px solid #1e2130;"
            "border-top:none;border-radius:0 0 12px 12px;height:5px;'></div>",
            unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)
