"""
Module Personnel — affectations mondiales et analyse des mutations.
"""
import pandas as pd
import streamlit as st

from utils import COUNTRY_ISO_MAP
from db.demo import _get_db
from modules.map import _map_geo_layout

_CONT_COL_P = {
    "Europe": "#3b82f6", "Asie": "#f59e0b", "Amérique": "#10b981",
    "Afrique": "#ef4444", "Océanie": "#8b5cf6",
}


def _load_personnel_data(db) -> dict:
    current = db.read_sql("""
        SELECT e.id, e.nom, e.prenom, e.poste, e.statut, e.date_embauche,
               a.agence, a.ville, a.pays, a.continent, a.date_debut
        FROM employes e
        JOIN affectations a ON e.id = a.employe_id
        WHERE a.date_fin IS NULL
        ORDER BY a.continent, a.pays, e.nom
    """)
    mutations = db.read_sql("""
        SELECT
            e.id AS employe_id, e.nom, e.prenom, e.poste,
            a_prev.pays       AS pays_depart,
            a_prev.continent  AS cont_depart,
            a_prev.agence     AS agence_depart,
            a_curr.pays       AS pays_arrivee,
            a_curr.continent  AS cont_arrivee,
            a_curr.agence     AS agence_arrivee,
            a_curr.ville      AS ville_arrivee,
            a_curr.date_debut AS date_mutation,
            CAST(strftime('%Y', a_curr.date_debut) AS INTEGER) AS annee
        FROM affectations a_curr
        JOIN affectations a_prev
          ON  a_prev.employe_id = a_curr.employe_id
          AND a_prev.date_fin   = (
                SELECT MAX(date_fin) FROM affectations
                WHERE employe_id = a_curr.employe_id
                  AND date_fin  < a_curr.date_debut
              )
        JOIN employes e ON e.id = a_curr.employe_id
        WHERE a_curr.date_debut >= '2019-01-01'
        ORDER BY a_curr.date_debut DESC
    """)
    all_aff = db.read_sql("""
        SELECT a.*, e.nom, e.prenom, e.poste, e.statut
        FROM affectations a
        JOIN employes e ON e.id = a.employe_id
        ORDER BY a.date_debut
    """)
    return {"current": current, "mutations": mutations, "all_aff": all_aff}


def render_personnel_module() -> None:
    import plotly.express as px

    db = _get_db()
    try:
        pdata = _load_personnel_data(db)
    except Exception as e:
        st.error(f"Tables `employes` / `affectations` introuvables : {e}")
        return

    cur     = pdata["current"]
    mut     = pdata["mutations"]

    n_actifs   = len(cur)
    n_pays     = cur["pays"].nunique()    if not cur.empty else 0
    n_mut      = len(mut)
    n_cur_year = len(mut[mut["annee"] == pd.Timestamp.now().year]) if not mut.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Employés actifs",   n_actifs)
    m2.metric("Pays couverts",     n_pays)
    m3.metric("Mutations totales", n_mut)
    m4.metric(f"Mutations {pd.Timestamp.now().year}", n_cur_year)

    tab_map, tab_mut, tab_teams = st.tabs(
        ["🌍 Carte des effectifs", "📊 Mutations annuelles", "👥 Équipes par pays"])

    with tab_map:
        if not cur.empty:
            emp_by_country = (cur.groupby("pays")
                                 .agg(nb_employes=("id","count"),
                                      continents=("continent", lambda x: x.iloc[0]))
                                 .reset_index())
            emp_by_country["iso_alpha"] = emp_by_country["pays"].map(COUNTRY_ISO_MAP)

            fig = px.choropleth(
                emp_by_country,
                locations="iso_alpha",
                color="nb_employes",
                hover_name="pays",
                hover_data={"iso_alpha": False, "nb_employes": "Employés"},
                color_continuous_scale=[[0,"#172554"],[0.4,"#1d4ed8"],[1,"#93c5fd"]],
                custom_data=["pays"],
            )
            _map_geo_layout(fig, 400)
            st.plotly_chart(fig, use_container_width=True, key="pers_map")

            btn_c, _ = st.columns([2, 8])
            with btn_c:
                from reports.mutations import _mutations_rapport_dialog
                if st.button("📋 Rapport mutations", key="pers_rpt_btn",
                             use_container_width=True):
                    _mutations_rapport_dialog(pdata)
        else:
            st.info("Aucun employé actif trouvé.")

    with tab_mut:
        if not mut.empty:
            by_year = (mut.groupby("annee")
                          .agg(nb_mutations=("employe_id","count"),
                               nb_employes=("employe_id","nunique"))
                          .reset_index())
            by_year["annee_str"] = by_year["annee"].astype(str)

            fig2 = px.bar(
                by_year, x="annee_str", y="nb_mutations",
                text="nb_mutations",
                color_discrete_sequence=["#3b82f6"],
                labels={"annee_str": "Année", "nb_mutations": "Mutations"},
            )
            fig2.update_traces(textposition="outside")
            fig2.update_layout(
                paper_bgcolor="#0d0f14", plot_bgcolor="#0d0f14",
                font_color="#e8eaf0", showlegend=False,
                margin=dict(l=0,r=0,t=20,b=0), height=300,
                xaxis=dict(gridcolor="#1e2130"),
                yaxis=dict(gridcolor="#1e2130"),
            )
            st.plotly_chart(fig2, use_container_width=True, key="mut_bar")

            st.markdown(
                "<div style='color:#94a3b8;font-size:.75rem;text-transform:uppercase;"
                "letter-spacing:1px;font-family:JetBrains Mono,monospace;margin:12px 0 8px;'>"
                "Détail des mutations</div>", unsafe_allow_html=True)

            for _, r in mut.head(20).iterrows():
                c_dep = _CONT_COL_P.get(r.get("cont_depart",""), "#6b7280")
                c_arr = _CONT_COL_P.get(r.get("cont_arrivee",""), "#6b7280")
                st.markdown(
                    f"<div style='background:#13151d;border:1px solid #1e2130;"
                    f"border-radius:10px;padding:9px 16px;margin-bottom:6px;"
                    f"display:flex;align-items:center;gap:12px;'>"
                    f"<span style='font-size:.72rem;color:#475569;font-family:JetBrains Mono;"
                    f"white-space:nowrap;'>{str(r.get('date_mutation',''))[:10]}</span>"
                    f"<span style='font-weight:600;color:#e8eaf0;min-width:130px;'>"
                    f"{r.get('prenom','')} {r.get('nom','')}</span>"
                    f"<span style='font-size:.75rem;color:#64748b;'>{r.get('poste','')}</span>"
                    f"<span style='flex:1;text-align:right;font-size:.8rem;'>"
                    f"<span style='color:{c_dep};'>{r.get('pays_depart','')}</span>"
                    f"<span style='color:#475569;'>  →  </span>"
                    f"<span style='color:{c_arr};'>{r.get('pays_arrivee','')}</span>"
                    f"</span></div>",
                    unsafe_allow_html=True)
        else:
            st.info("Aucune mutation enregistrée.")

    with tab_teams:
        if not cur.empty:
            postes = {"Directeur Régional":"#6366f1","Agent Commercial":"#3b82f6",
                      "Responsable Visa":"#10b981","Responsable Opérations":"#f59e0b"}
            for pays, grp in cur.groupby("pays", sort=True):
                cont  = grp.iloc[0]["continent"]
                c_col = _CONT_COL_P.get(cont, "#6b7280")
                st.markdown(
                    f"<div style='color:{c_col};font-size:.75rem;font-weight:500;"
                    f"text-transform:uppercase;letter-spacing:1px;"
                    f"font-family:JetBrains Mono,monospace;margin:14px 0 6px;'>"
                    f"{pays}  ·  {cont}  ·  {len(grp)} poste(s)</div>",
                    unsafe_allow_html=True)
                for _, emp in grp.iterrows():
                    p_col = postes.get(emp.get("poste",""), "#94a3b8")
                    ini   = (str(emp.get("nom","?"))[:1]+str(emp.get("prenom","?"))[:1]).upper()
                    st.markdown(
                        f"<div style='background:#13151d;border:1px solid #1e2130;"
                        f"border-radius:9px;padding:8px 14px;margin-bottom:5px;"
                        f"display:flex;align-items:center;gap:10px;'>"
                        f"<div style='width:30px;height:30px;border-radius:50%;"
                        f"background:linear-gradient(135deg,#3b82f6,#7c3aed);"
                        f"display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;font-size:.8rem;color:white;flex-shrink:0;'>{ini}</div>"
                        f"<div style='flex:1;'>"
                        f"<span style='font-weight:600;color:#e8eaf0;'>"
                        f"{emp.get('prenom','')} {emp.get('nom','')}</span>"
                        f"  <span style='font-size:.75rem;color:#64748b;'>"
                        f"{emp.get('agence','')}</span></div>"
                        f"<span style='font-size:.72rem;padding:2px 8px;border-radius:20px;"
                        f"background:{p_col}22;color:{p_col};white-space:nowrap;'>"
                        f"{emp.get('poste','')}</span>"
                        f"<span style='font-size:.7rem;color:#475569;margin-left:6px;'>"
                        f"depuis {str(emp.get('date_debut',''))[:10]}</span>"
                        f"</div>", unsafe_allow_html=True)
        else:
            st.info("Aucune affectation active.")
