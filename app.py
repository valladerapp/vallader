import streamlit as st
import sqlite3
import random
import os
import pandas as pd

# Pfad zur Datenbank
DB_PATH = "languages.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vocab 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       language TEXT, german TEXT, target TEXT, level INTEGER)''')
    conn.commit()
    conn.close()

# Initialisierung
init_db()

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="Vallader", layout="centered")

# Design & CSS
st.markdown("""
    <style>
    .stApp { background-color: #40E0D0; }
    .header { 
        background-color: #E0B0FF; 
        padding: 25px; 
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 25px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .header h1 { color: black; margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .footer { text-align: center; color: #555; font-size: 12px; margin-top: 50px; padding: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; }
    </style>
    <div class="header"><h1>Vallader</h1></div>
    """, unsafe_allow_html=True)

# Session State Initialisierung
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'quiz_q' not in st.session_state:
    st.session_state.quiz_q = None

# --- LOGIN ---
if not st.session_state.logged_in:
    st.write("### Willkommen - bitte anmelden")
    pw = st.text_input("Passwort", type="password")
    if st.button("Einloggen"):
        if pw == "Vallader2026":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Falsches Passwort")

# --- HAUPTBEREICH ---
else:
    tab1, tab2, tab3 = st.tabs(["📝 Lernen (Tippen)", "🔘 Lernen (Auswahl)", "🗄️ Datenbank"])

    # --- QUIZ FUNKTIONEN ---
    def get_new_question():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, german, target, level FROM vocab ORDER BY (level * RANDOM()) LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row

    def update_level(vocab_id, current_lvl, correct):
        new_lvl = current_lvl + 1 if correct else 1
        if new_lvl < 1: new_lvl = 1
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE vocab SET level = ? WHERE id = ?", (new_lvl, vocab_id))
        conn.commit()
        conn.close()

    # --- LERNEN TABS ---
    for q_tab, mode in zip([tab1, tab2], ["tippen", "choice"]):
        with q_tab:
            if st.button("Nächstes Wort", key=f"next_{mode}") or st.session_state.quiz_q is None:
                st.session_state.quiz_q = get_new_question()
            
            q = st.session_state.quiz_q
            if q:
                st.write(f"### Was heißt: **{q[1]}**?")
                if mode == "tippen":
                    user_ans = st.text_input("Antwort:", key=f"in_{mode}").strip()
                    if st.button("Prüfen", key=f"btn_{mode}"):
                        if user_ans.lower() == q[2].lower().strip():
                            st.success(f"Richtig! ✅ ({q[2]})")
                            update_level(q[0], q[3], True)
                        else:
                            st.error(f"Falsch. ❌ Richtig wäre: {q[2]}")
                            update_level(q[0], q[3], False)
                else:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT target FROM vocab WHERE target != ? ORDER BY RANDOM() LIMIT 3", (q[2],))
                    opts = [o[0] for o in cursor.fetchall()] + [q[2]]
                    random.shuffle(opts)
                    conn.close()
                    ans = st.radio("Wähle:", opts, key=f"rad_{mode}")
                    if st.button("Antworten", key=f"btn_{mode}"):
                        if ans == q[2]:
                            st.success("Richtig! ✅")
                            update_level(q[0], q[3], True)
                        else:
                            st.error(f"Falsch. ❌ Richtig wäre: {q[2]}")
                            update_level(q[0], q[3], False)
            else:
                st.info("Datenbank leer.")

    # --- DATENBANK TAB (EDITIEREN & LÖSCHEN) ---
    with tab3:
        # 1. Hinzufügen
        with st.expander("➕ Neue Vokabel hinzufügen"):
            c1, c2 = st.columns(2)
            with c1: de_n = st.text_input("Deutsch", key="add_de")
            with c2: val_n = st.text_input("Vallader", key="add_val")
            if st.button("Speichern"):
                if de_n and val_n:
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", ("Vallader", de_n, val_n, 1))
                    conn.commit()
                    conn.close()
                    st.rerun()

        # 2. Editieren / Löschen
        conn = sqlite3.connect(DB_PATH)
        df_all = pd.read_sql_query("SELECT id, german, target, level FROM vocab ORDER BY target ASC", conn)
        conn.close()

        if not df_all.empty:
            with st.expander("✏️ Wort bearbeiten oder löschen", expanded=True):
                v_list = {f"{r['target']} ({r['german']})": r['id'] for _, r in df_all.iterrows()}
                sel = st.selectbox("Wort auswählen:", v_list.keys())
                sel_id = v_list[sel]
                curr = df_all[df_all['id'] == sel_id].iloc[0]
                
                ce1, ce2 = st.columns(2)
                with ce1: new_de = st.text_input("Deutsch:", value=curr['german'], key="e_de")
                with ce2: new_val = st.text_input("Vallader:", value=curr['target'], key="e_val")
                
                be1, be2 = st.columns(2)
                with be1:
                    if st.button("Änderung speichern"):
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("UPDATE vocab SET german=?, target=? WHERE id=?", (new_de, new_val, sel_id))
                        conn.commit()
                        conn.close()
                        st.rerun()
                with be2:
                    if st.button("🗑️ Löschen"):
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("DELETE FROM vocab WHERE id=?", (sel_id,))
                        conn.commit()
                        conn.close()
                        st.rerun()

        # 3. Ansicht
        st.divider()
        search = st.text_input("Suchen...")
        conn = sqlite3.connect(DB_PATH)
        df_view = pd.read_sql_query(f"SELECT german, target, level FROM vocab WHERE german LIKE '%{search}%' OR target LIKE '%{search}%' ORDER BY id DESC", conn)
        st.dataframe(df_view, use_container_width=True, hide_index=True)
        conn.close()

st.markdown('<div class="footer">designed and powered by akeora gmbh</div>', unsafe_allow_html=True)
