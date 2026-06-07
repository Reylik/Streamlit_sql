"""
Historique des requêtes persisté dans la table SQL _app_history.
"""
import copy
import json
from datetime import datetime

import streamlit as st

from query.builder import build_query_display

MAX_HISTORY = 20


def _init_history_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _app_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT    NOT NULL,
            ts         TEXT    NOT NULL,
            table_name TEXT    NOT NULL,
            summary    TEXT    NOT NULL,
            conds_json TEXT    NOT NULL,
            joins_json TEXT    NOT NULL DEFAULT '[]',
            row_count  INTEGER NOT NULL
        )
    """)
    try:
        conn.execute("ALTER TABLE _app_history ADD COLUMN joins_json TEXT NOT NULL DEFAULT '[]'")
    except Exception:
        pass
    conn.commit()


def _db_push_history(conn, user_id: str, table: str,
                     conditions: list, row_count: int,
                     joins: list | None = None) -> None:
    qd      = build_query_display(table, conditions)
    summary = qd.split("\nWHERE ", 1)[1] if "\nWHERE " in qd else "Tous les enregistrements"
    ts      = datetime.now().strftime("%d/%m %H:%M:%S")

    last = conn.execute(
        "SELECT id, summary, table_name FROM _app_history "
        "WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (user_id,)
    ).fetchone()

    if last and last[2] == table and last[1] == summary:
        conn.execute(
            "UPDATE _app_history SET ts=?, row_count=? WHERE id=?",
            (ts, row_count, last[0])
        )
    else:
        conn.execute(
            "INSERT INTO _app_history "
            "(user_id, ts, table_name, summary, conds_json, joins_json, row_count) "
            "VALUES (?,?,?,?,?,?,?)",
            (user_id, ts, table, summary,
             json.dumps(conditions, ensure_ascii=False),
             json.dumps(joins or [],  ensure_ascii=False),
             row_count)
        )

    conn.execute("""
        DELETE FROM _app_history
        WHERE user_id = ? AND id NOT IN (
            SELECT id FROM _app_history
            WHERE user_id = ? ORDER BY id DESC LIMIT ?
        )
    """, (user_id, user_id, MAX_HISTORY))
    conn.commit()


def _db_get_history(conn, user_id: str) -> list:
    rows = conn.execute(
        "SELECT id, ts, table_name, summary, conds_json, joins_json, row_count "
        "FROM _app_history WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    result = []
    for r in rows:
        try:
            joins_val = json.loads(r[6]) if r[6] else []
        except Exception:
            joins_val = []
        result.append({
            "id":         r[0],
            "ts":         r[1],
            "table":      r[2],
            "summary":    r[3],
            "conditions": json.loads(r[4]),
            "joins":      joins_val,
            "row_count":  r[5],
        })
    return result


def _render_history_popover(conn, user_id: str, enrich: dict) -> None:
    history = _db_get_history(conn, user_id)
    n       = len(history)
    label   = f"🕐  {n}" if n else "🕐"

    with st.popover(label, use_container_width=True):
        st.markdown(
            "<span style='color:#94a3b8;font-size:.72rem;text-transform:uppercase;"
            "letter-spacing:1px;font-family:JetBrains Mono,monospace;'>"
            f"Historique ({n} / {MAX_HISTORY})  —  user {user_id}</span>",
            unsafe_allow_html=True)

        if not history:
            st.markdown(
                "<p style='color:#4a5170;font-style:italic;font-size:.82rem;"
                "margin-top:6px;'>Aucune requête exécutée.</p>",
                unsafe_allow_html=True)
            return

        for entry in history:
            n_rows = entry["row_count"]
            summ_d = (entry["summary"][:160] + "…") \
                     if len(entry["summary"]) > 160 else entry["summary"]

            st.markdown(
                f"<div style='background:#13151d;border:1px solid #1e2130;"
                f"border-radius:10px;padding:10px 12px;margin-bottom:8px;'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;margin-bottom:5px;'>"
                f"<span style='font-family:JetBrains Mono,monospace;"
                f"font-size:.72rem;color:#6366f1;font-weight:600;'>"
                f"{entry['table']}</span>"
                f"<span style='font-size:.7rem;color:#475569;'>{entry['ts']}</span>"
                f"</div>"
                f"<div style='font-family:JetBrains Mono,monospace;font-size:.72rem;"
                f"color:#a5f3fc;white-space:pre-wrap;word-break:break-word;"
                f"line-height:1.55;margin-bottom:7px;'>{summ_d}</div>"
                f"<span style='font-size:.7rem;color:#4ade80;'>"
                f"{n_rows} ligne{'s' if n_rows != 1 else ''}</span>"
                f"</div>",
                unsafe_allow_html=True)

            if st.button("↩ Relancer", key=f"hist_replay_{entry['id']}",
                         use_container_width=True):
                st.session_state.selected_table      = entry["table"]
                st.session_state.conditions          = copy.deepcopy(entry["conditions"])
                st.session_state.joins               = copy.deepcopy(entry.get("joins", []))
                st.session_state.results             = None
                st.session_state.enrich_count        = None
                st.session_state["_last_cell_click"] = None
                st.session_state["_auto_execute"]    = True
                st.rerun()

        st.divider()
        if st.button("🗑 Vider mon historique", key="hist_clear",
                     use_container_width=True):
            conn.execute("DELETE FROM _app_history WHERE user_id=?", (user_id,))
            conn.commit()
            st.rerun()
