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

init_db()

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="Vallader", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #40E0D0; }
    .header { 
        background-color: #E0B0FF; padding: 25px; border-radius: 15px; 
        text-align: center; margin-bottom: 25px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .header h1 { color: black; margin: 0; font-family: 'Segoe UI'; }
    .footer { text-align: center; color: #555; font-size: 12px; margin-top: 50px; padding: 20px; }
    </style>
    <div class="header"><h1>Vallader</h1></div>
    """, unsafe_allow_html=True)

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

else:
    tab1, tab2, tab3 = st.tabs(["📝 Lernen (Tippen)", "🔘 Lernen (Auswahl)", "🗄️ Datenbank"])

    # --- QUIZ LOGIK ---
    def get_new_question():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, german, target, level FROM vocab ORDER BY (level * RANDOM()) LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row

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
                        is_corr = user_ans.lower() == q[2].lower().strip()
                        new_lvl = q[3] + 1 if is_corr else 1
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("UPDATE vocab SET level = ? WHERE id = ?", (max(1, new_lvl), q[0]))
                        conn.commit()
                        conn.close()
                        if is_corr: st.success(f"Richtig! ✅ ({q[2]})")
                        else: st.error(f"Falsch. ❌ Richtig wäre: {q[2]}")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT target FROM vocab WHERE target != ? ORDER BY RANDOM() LIMIT 3", (q[2],))
                    opts = [o[0] for o in cursor.fetchall()] + [q[2]]
                    random.shuffle(opts)
                    conn.close()
                    ans = st.radio("Wähle:", opts, key=f"rad_{mode}")
                    if st.button("Antworten", key=f"btn_c_{mode}"):
                        is_corr = (ans == q[2])
                        new_lvl = q[3] + 1 if is_corr else 1
                        conn = sqlite3.connect(DB_PATH)
                        conn.execute("UPDATE vocab SET level = ? WHERE id = ?", (max(1, new_lvl), q[0]))
                        conn.commit()
                        conn.close()
                        if is_corr: st.success("Richtig! ✅")
                        else: st.error(f"Falsch. ❌ Richtig wäre: {q[2]}")
            else:
                st.info("Datenbank leer.")

    # --- DATENBANK TAB (DIREKT-EDITOR) ---
    with tab3:
        st.subheader("Vokabeln direkt bearbeiten")
        st.info("💡 Tippe direkt in eine Zelle zum Ändern. Markiere eine Zeile und drücke 'Entf' zum Löschen.")

        # 1. Schnelles Hinzufügen
        with st.expander("➕ Neues Wort hinzufügen"):
            c1, c2 = st.columns(2)
            with c1: de_n = st.text_input("Deutsch", key="add_de")
            with c2: val_n = st.text_input("Vallader", key="add_val")
            if st.button("Schnell-Speichern"):
                if de_n and val_n:
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", ("Vallader", de_n, val_n, 1))
                    conn.commit()
                    conn.close()
                    st.rerun()

        st.divider()

        # 2. Der Daten-Editor (Anzeigen, Editieren, Löschen)
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT id, german, target, level FROM vocab ORDER BY id DESC", conn)
        conn.close()

        # Editor anzeigen
        edited_df = st.data_editor(
            df, 
            column_config={
                "id": None, # ID verstecken
                "german": st.column_config.TextColumn("Deutsch", width="medium"),
                "target": st.column_config.TextColumn("Vallader", width="medium"),
                "level": st.column_config.NumberColumn("Lvl", width="small", disabled=True),
            },
            num_rows="dynamic", # Erlaubt das Löschen von Zeilen
            hide_index=True,
            use_container_width=True,
            key="vocab_editor"
        )

        # Änderungen in DB speichern
        if st.button("Alle Änderungen in Datenbank übernehmen"):
            conn = sqlite3.connect(DB_PATH)
            # Einfachste Methode: Tabelle löschen und neu befüllen
            conn.execute("DELETE FROM vocab")
            for _, row in edited_df.iterrows():
                conn.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", 
                             ("Vallader", row['german'], row['target'], row['level']))
            conn.commit()
            conn.close()
            st.success("Datenbank erfolgreich aktualisiert!")
            st.rerun()

st.markdown('<div class="footer">designed and powered by akeora gmbh</div>', unsafe_allow_html=True)
