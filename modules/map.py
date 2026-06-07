"""
Module carte mondiale des voyages.
"""
import pandas as pd
import streamlit as st

from utils import COUNTRY_ISO_MAP, CONT_COLORS, TYPE_COLORS
from db.demo import _get_db

_MAP_BG   = "#0d0f14"
_MAP_LAND = "#13151d"
_MAP_SEA  = "#0a0c12"
_MAP_LINE = "#1e2130"


def _map_geo_layout(fig, height: int = 460):
    fig.update_layout(
        paper_bgcolor=_MAP_BG, plot_bgcolor=_MAP_BG,
        font=dict(color="#e8eaf0"),
        margin=dict(l=0, r=0, t=0, b=0), height=height,
        coloraxis_showscale=False,
        geo=dict(
            bgcolor=_MAP_BG, showframe=False,
            showcoastlines=True, coastlinecolor="#2a2d3e",
            showland=True,    landcolor=_MAP_LAND,
            showocean=True,   oceancolor=_MAP_SEA,
            showlakes=True,   lakecolor=_MAP_SEA,
            showcountries=True, countrycolor=_MAP_LINE,
            projection_type="natural earth",
        ),
    )
    return fig


def _choropleth(df, color_col, hover_name, hover_data, color_scale,
                custom_data=None, highlight_iso=None, height=460):
    import plotly.express as px
    import plotly.graph_objects as go

    fig = px.choropleth(
        df, locations="iso_alpha", color=color_col,
        hover_name=hover_name, hover_data=hover_data,
        color_continuous_scale=color_scale,
        range_color=[0, max(df[color_col].max(), 1)],
        custom_data=custom_data or [],
    )
    if highlight_iso:
        fig.add_trace(go.Choropleth(
            locations=[highlight_iso], z=[1],
            colorscale=[[0, "#6366f1"], [1, "#6366f1"]],
            showscale=False, hoverinfo="skip",
            marker_line_color="#a78bfa", marker_line_width=2.5,
        ))
    return _map_geo_layout(fig, height)


def _read_map_click(event):
    sel = getattr(event, "selection", None)
    pts = getattr(sel, "points", None) or (sel or {}).get("points", [])
    if not pts:
        return None
    raw = pts[0].get("customdata") or []
    return (raw[0] if isinstance(raw, (list, tuple)) and raw else raw) or None


def render_map_module() -> None:
    import plotly.express as px

    db  = _get_db()
    nav = st.session_state

    selected_country = nav.get("map_country")
    selected_cid     = nav.get("map_client_id")
    selected_cname   = nav.get("map_client_name", "")

    if selected_cid or selected_country:
        back_cols = st.columns([2, 10])
        with back_cols[0]:
            if selected_cid:
                label = f"← {selected_country}" if selected_country else "← Carte"
                if st.button(label, key="map_back", use_container_width=True):
                    nav.pop("map_client_id",   None)
                    nav.pop("map_client_name", None)
                    st.rerun()
            else:
                if st.button("← Carte mondiale", key="map_back", use_container_width=True):
                    nav.pop("map_country", None)
                    st.rerun()

    try:
        cdf = db.read_sql("""
            SELECT pays_destination,
                   COUNT(*)                    AS nb_voyages,
                   COUNT(DISTINCT client_id)   AS nb_clients,
                   ROUND(AVG(budget),  0)      AS budget_moyen,
                   ROUND(SUM(budget),  0)      AS total_budget
            FROM voyages
            GROUP BY pays_destination
            ORDER BY nb_voyages DESC
        """)
    except Exception:
        st.error("La table `voyages` est introuvable dans la base connectée.")
        return

    if cdf.empty:
        st.info("Aucune donnée de voyage disponible.")
        return

    cdf["iso_alpha"] = cdf["pays_destination"].map(COUNTRY_ISO_MAP)

    # ── VUE CLIENT ────────────────────────────────────────────────────────────
    if selected_cid:
        try:
            trips = db.read_sql("""
                SELECT v.pays_destination, v.destination, v.continent,
                       v.date_depart, v.date_retour, v.duree_jours,
                       v.budget, v.note, v.type_voyage, v.statut
                FROM voyages v
                WHERE v.client_id = ?
                ORDER BY v.date_depart DESC
            """, [selected_cid])
        except Exception:
            st.error("Impossible de récupérer les voyages de ce client.")
            return

        if trips.empty:
            st.info("Aucun voyage pour ce client.")
            return

        pers = (trips.groupby("pays_destination")
                     .agg(nb_voyages=("pays_destination", "count"),
                          total_budget=("budget", "sum"))
                     .reset_index())
        pers["iso_alpha"] = pers["pays_destination"].map(COUNTRY_ISO_MAP)

        n_pays    = pers["pays_destination"].nunique()
        total_bgt = int(trips["budget"].sum())
        n_trips   = len(trips)

        st.markdown(
            f"<h2 style='margin-bottom:.15rem;'>🧳 {selected_cname}</h2>"
            f"<p style='color:#64748b;margin-bottom:1rem;font-size:.88rem;'>"
            f"{n_trips} voyage(s) · {n_pays} pays · {total_bgt:,} €</p>",
            unsafe_allow_html=True)

        fig_c = _choropleth(
            pers, "total_budget", "pays_destination",
            {"iso_alpha": False, "nb_voyages": "Voyages", "total_budget": "Budget total (€)"},
            [[0, "#172554"], [0.4, "#7c3aed"], [1, "#a78bfa"]],
            custom_data=["pays_destination"], height=400,
        )
        st.plotly_chart(fig_c, use_container_width=True, key="client_map")

        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        for _, r in trips.iterrows():
            note_v = r.get("note")
            stars  = "⭐" * int(note_v) if note_v and pd.notna(note_v) else "—"
            sc     = "#4ade80" if r.get("statut") == "terminé" else "#fbbf24"
            cc     = CONT_COLORS.get(r.get("continent", ""), "#6b7280")
            st.markdown(
                f"<div style='background:#13151d;border:1px solid #1e2130;"
                f"border-left:3px solid {cc};"
                f"border-radius:10px;padding:10px 16px;margin-bottom:7px;"
                f"display:flex;align-items:center;gap:12px;'>"
                f"<div style='flex:1;'>"
                f"<span style='font-weight:600;color:#e8eaf0;'>{r['destination']}</span>"
                f"<span style='color:#475569;font-size:.8rem;margin-left:8px;'>"
                f"{r['pays_destination']} · {str(r['date_depart'])[:10]}"
                f"{'  ·  ' + str(r['duree_jours']) + 'j' if r.get('duree_jours') else ''}"
                f"</span></div>"
                f"<span style='color:#4ade80;font-family:JetBrains Mono,monospace;"
                f"font-size:.82rem;'>{int(r['budget']):,}€</span>"
                f"<span style='color:{sc};font-size:.75rem;margin-left:10px;'>{r['statut']}</span>"
                f"<span style='font-size:.78rem;margin-left:8px;'>{stars}</span>"
                f"</div>",
                unsafe_allow_html=True)
        return

    # ── VUE MONDE / VUE PAYS ──────────────────────────────────────────────────
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Pays visités",  int(cdf["pays_destination"].nunique()))
    mc2.metric("Total voyages", int(cdf["nb_voyages"].sum()))
    mc3.metric("Budget total",  f"{int(cdf['total_budget'].sum()):,}€")
    mc4.metric("Budget moyen",  f"{int(cdf['budget_moyen'].mean()):,}€")

    hi_iso = None
    if selected_country:
        row_hi = cdf[cdf["pays_destination"] == selected_country]
        if not row_hi.empty and pd.notna(row_hi.iloc[0].get("iso_alpha")):
            hi_iso = row_hi.iloc[0]["iso_alpha"]

    fig_w = _choropleth(
        cdf, "nb_voyages", "pays_destination",
        {"iso_alpha": False, "nb_voyages": "Voyages",
         "nb_clients": "Clients", "budget_moyen": "Budget moyen (€)"},
        [[0, "#172554"], [0.25, "#1d4ed8"], [0.6, "#3b82f6"], [1, "#93c5fd"]],
        custom_data=["pays_destination"], highlight_iso=hi_iso,
    )
    event_w = st.plotly_chart(fig_w, on_select="rerun",
                              key="world_map", use_container_width=True)

    clicked = _read_map_click(event_w)
    if clicked and clicked != selected_country:
        nav["map_country"] = clicked
        st.rerun()

    all_countries = [""] + sorted(cdf["pays_destination"].tolist())
    idx    = all_countries.index(selected_country) if selected_country in all_countries else 0
    chosen = st.selectbox(
        "Ou sélectionnez un pays :", all_countries, index=idx,
        key="map_country_sel",
        format_func=lambda x: x or "— cliquer sur la carte ou choisir ici —",
    )
    if chosen != selected_country:
        nav["map_country"] = chosen or None
        st.rerun()

    if not selected_country:
        st.markdown(
            "<p style='color:#334155;font-style:italic;font-size:.85rem;"
            "text-align:center;margin-top:20px;padding-bottom:4rem;'>"
            "Cliquez sur un pays pour explorer ses statistiques.</p>",
            unsafe_allow_html=True)
        return

    r = cdf[cdf["pays_destination"] == selected_country]
    if r.empty:
        return
    r = r.iloc[0]

    st.markdown(f"<h3 style='margin:20px 0 4px;'>📍 {selected_country}</h3>",
                unsafe_allow_html=True)
    ps1, ps2, ps3, ps4 = st.columns(4)
    ps1.metric("Voyages",      int(r["nb_voyages"]))
    ps2.metric("Clients",      int(r["nb_clients"]))
    ps3.metric("Budget moyen", f"{int(r['budget_moyen']):,}€")
    ps4.metric("Budget total", f"{int(r['total_budget']):,}€")

    try:
        clients_c = db.read_sql("""
            SELECT c.id, c.nom, c.prenom, c.ville, c.statut,
                   COUNT(v.id)             AS nb_voyages,
                   ROUND(SUM(v.budget), 0) AS total_budget
            FROM clients c
            JOIN voyages v ON c.id = v.client_id
            WHERE v.pays_destination = ?
            GROUP BY c.id
            ORDER BY nb_voyages DESC, total_budget DESC
        """, [selected_country])
    except Exception:
        return

    st.markdown(
        f"<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
        f"letter-spacing:1px;font-family:JetBrains Mono,monospace;margin:18px 0 10px;'>"
        f"Clients ayant visité {selected_country}</div>",
        unsafe_allow_html=True)

    for _, cl in clients_c.iterrows():
        sc  = "#4ade80" if cl.get("statut") == "actif" else "#f87171"
        ini = (str(cl.get("nom","?"))[:1] + str(cl.get("prenom","?"))[:1]).upper()
        cc, cb = st.columns([8, 2])
        with cc:
            st.markdown(
                f"<div style='background:#13151d;border:1px solid #1e2130;"
                f"border-radius:10px;padding:10px 16px;"
                f"display:flex;align-items:center;gap:12px;'>"
                f"<div style='width:34px;height:34px;border-radius:50%;"
                f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                f"display:flex;align-items:center;justify-content:center;"
                f"font-weight:700;font-size:.82rem;color:white;flex-shrink:0;'>{ini}</div>"
                f"<div style='flex:1;'>"
                f"<span style='font-weight:600;color:#e8eaf0;'>"
                f"{cl.get('prenom','')} {cl.get('nom','')}</span>"
                f"<span style='color:#64748b;font-size:.78rem;margin-left:8px;'>"
                f"{cl.get('ville','')} · "
                f"<span style='color:{sc};'>{cl.get('statut','')}</span></span></div>"
                f"<span style='font-family:JetBrains Mono,monospace;font-size:.8rem;"
                f"color:#4ade80;'>{int(cl['total_budget']):,}€</span>"
                f"<span style='font-size:.72rem;color:#475569;margin-left:8px;'>"
                f"{int(cl['nb_voyages'])} voyage(s)</span>"
                f"</div>",
                unsafe_allow_html=True)
        with cb:
            if st.button("Voir ses voyages →",
                         key=f"map_client_{cl['id']}",
                         use_container_width=True):
                nav["map_client_id"]   = int(cl["id"])
                nav["map_client_name"] = f"{cl.get('prenom','')} {cl.get('nom','')}".strip()
                st.rerun()
