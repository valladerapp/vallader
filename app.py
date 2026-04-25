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
st.set_page_config(page_title="Vallader", layout="wide")

# Modernes CSS
st.markdown("""
    <style>
    /* Ganze Seite Hintergrund */
    .stApp { background-color: #40E0D0; font-family: 'Inter', 'Segoe UI', Roboto, sans-serif; }
    
    /* Full-Width Violett Header */
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    .full-header {
        background-color: #E0B0FF;
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        padding: 30px 0 10px 0;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-top: -60px;
    }
    .full-header h1 { 
        color: black; 
        margin: 0; 
        font-weight: 700; 
        font-size: 50px;
        letter-spacing: -1px;
    }
    .subtitle {
        color: rgba(0,0,0,0.5);
        font-size: 10px;
        font-weight: 400;
        margin-bottom: 20px;
    }
    
    /* Buttons Styling (Hellgrau) */
    .stButton>button {
        background-color: #f0f2f6;
        color: #31333F;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #e0e2e6;
        border: none;
    }
    
    /* Tab Design Anpassung */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }

    /* Quiz Wort Fokus */
    .quiz-word {
        font-size: 60px;
        font-weight: 800;
        text-align: center;
        margin: 40px 0;
        color: #1a1a1a;
    }
    </style>
    
    <div class="full-header">
        <h1>Vallader</h1>
        <div class="subtitle">designed and powered by akeora</div>
    </div>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'quiz_q' not in st.session_state:
    st.session_state.quiz_q = None

# --- LOGIN ---
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.write("### Anmeldung")
        pw = st.text_input("Passwort", type="password")
        if st.button("Einloggen"):
            if pw == "Vallader2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Falsches Passwort")

# --- HAUPTBEREICH ---
else:
    # Navigation mit Spacing für Datenbank rechts
    t_schreiben, t_auswahl, spacer, t_datenbank = st.tabs(["Schreiben", "Auswahl", " ", "Datenbank"])

    # --- QUIZ LOGIK ---
    def get_new_question():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, german, target, level FROM vocab ORDER BY (level * RANDOM()) LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row

    # TAB SCHREIBEN & AUSWAHL
    for q_tab, mode in zip([t_schreiben, t_auswahl], ["tippen", "choice"]):
        with q_tab:
            col_q, col_btn = st.columns([3, 1])
            with col_btn:
                if st.button("Nächstes", key=f"next_{mode}") or st.session_state.quiz_q is None:
                    st.session_state.quiz_q = get_new_question()
            
            q = st.session_state.quiz_q
            if q:
                st.markdown(f'<div class="quiz-word">{q[1]}</div>', unsafe_allow_html=True)
                
                if mode == "tippen":
                    user_ans = st.text_input("Antwort:", key=f"in_{mode}", label_visibility="collapsed", placeholder="Hier schreiben...").strip()
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
                    ans = st.radio("Möglichkeiten:", opts, key=f"rad_{mode}", label_visibility="collapsed")
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

    # --- DATENBANK TAB ---
    with t_datenbank:
        st.subheader("Datenbank-Editor")
        
        with st.expander("Neues Wort hinzufügen"):
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

        st.divider()
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT id, german, target, level FROM vocab ORDER BY id DESC", conn)
        conn.close()

        edited_df = st.data_editor(
            df, 
            column_config={
                "id": None, 
                "german": st.column_config.TextColumn("Deutsch"),
                "target": st.column_config.TextColumn("Vallader"),
                "level": st.column_config.NumberColumn("Lvl", disabled=True),
            },
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key="vocab_editor"
        )

        if st.button("Änderungen übernehmen"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM vocab")
            for _, row in edited_df.iterrows():
                conn.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", 
                             ("Vallader", row['german'], row['target'], row['level']))
            conn.commit()
            conn.close()
            st.success("Aktualisiert!")
            st.rerun()
