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

# CSS für exakte Zentrierung und identische Breiten
st.markdown("""
    <style>
    .stApp { background-color: #40E0D0; font-family: 'Inter', sans-serif; }
    
    /* Riesiger Full-Width Violett Header */
    .full-header {
        background-color: #E0B0FF;
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        padding: 60px 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        margin-top: -60px;
        margin-bottom: 50px;
    }
    .full-header h1 { color: black; margin: 0; font-weight: 700; font-size: 55px; line-height: 1.0; }
    .subtitle { color: rgba(0,0,0,0.5); font-size: 11px; margin-top: 10px; }
    
    /* Navigation Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center; 
        gap: 20px;
        border-bottom: none !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 18px;
        font-weight: 600;
        padding: 12px 0 !important;
        width: 160px;
        justify-content: center;
        border-radius: 12px !important;
        border: 1px solid transparent !important;
        color: #1a1a1a !important;
        background-color: #f0f2f6 !important;
    }

    .stTabs [aria-selected="true"] {
        border: 1px solid black !important;
    }

    .stTabs [data-baseweb="tab-border"], 
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    .quiz-word {
        font-size: 38px;
        font-weight: 700;
        text-align: center;
        margin: 20px 0 30px 0;
        color: #1a1a1a;
    }
    
    /* ZENTRIERUNG DER BUTTONS & INPUT */
    /* Wir zwingen alle Buttons im Quiz-Bereich in die Mitte */
    div.stButton > button, div[data-testid="stTextInput"] {
        width: 450px !important;
        margin: 0 auto !important;
        display: block !important;
    }

    /* Styling für die Auswahl-Buttons */
    div.stButton > button {
        background-color: white !important;
        color: black !important;
        border-radius: 10px;
        border: 1px solid #ccc !important;
        font-size: 18px;
        padding: 12px;
        margin-bottom: 10px !important;
        text-align: center !important;
    }
    
    div.stButton > button:hover {
        border: 1px solid black !important;
        background-color: #f9f9f9 !important;
    }

    /* Spezifische Text-Zentrierung innerhalb der Buttons */
    div.stButton p {
        text-align: center !important;
        margin: 0 auto !important;
        width: 100%;
    }
    </style>
    
    <div class="full-header">
        <h1>Vallader</h1>
        <div class="subtitle">designed and powered by akeora</div>
    </div>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'quiz_q' not in st.session_state:
    st.session_state.quiz_q = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = None
if 'options' not in st.session_state:
    st.session_state.options = []

def get_new_question():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, german, target, level FROM vocab ORDER BY (level * RANDOM()) LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row

def load_new_quiz_data():
    q = get_new_question()
    st.session_state.quiz_q = q
    if q:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT target FROM vocab WHERE target != ? ORDER BY RANDOM() LIMIT 4", (q[2],))
        others = [row[0] for row in cursor.fetchall()]
        opts = others + [q[2]]
        random.shuffle(opts)
        st.session_state.options = opts
        conn.close()
    st.session_state.feedback = None

# --- LOGIN ---
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.write("### Anmeldung")
        pw = st.text_input("Passwort", type="password")
        if st.button("Einloggen"):
            if pw == "Vallader2026":
                st.session_state.logged_in = True
                st.rerun()
else:
    t_schreiben, t_auswahl, t_datenbank = st.tabs(["Schreiben", "Auswahl", "Datenbank"])

    if st.session_state.quiz_q is None:
        load_new_quiz_data()

    # --- SCHREIBEN ---
    with t_schreiben:
        q = st.session_state.quiz_q
        if q:
            st.markdown(f'<div class="quiz-word">{q[1]}</div>', unsafe_allow_html=True)
            if st.session_state.feedback:
                if st.session_state.feedback[0] == "ok": st.success(st.session_state.feedback[1])
                else: st.error(st.session_state.feedback[1])

            # Wichtig: Form benutzen für Enter-Logik
            with st.form("write_form", clear_on_submit=True):
                user_ans = st.text_input("Antwort", label_visibility="collapsed", placeholder="Tippen & Enter...")
                submit = st.form_submit_button("Prüfen", use_container_width=True)
                
                if submit and user_ans:
                    is_corr = user_ans.strip().lower() == q[2].strip().lower()
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("UPDATE vocab SET level = ? WHERE id = ?", (max(1, q[3]+1 if is_corr else 1), q[0]))
                    conn.commit()
                    conn.close()
                    st.session_state.feedback = ("ok", f"Richtig! ✅ {q[2]}") if is_corr else ("error", f"Falsch! ❌ Richtig: {q[2]}")
                    load_new_quiz_data()
                    st.rerun()

    # --- AUSWAHL ---
    with t_auswahl:
        q = st.session_state.quiz_q
        if q:
            st.markdown(f'<div class="quiz-word">{q[1]}</div>', unsafe_allow_html=True)
            if st.session_state.feedback:
                if st.session_state.feedback[0] == "ok": st.success(st.session_state.feedback[1])
                else: st.error(st.session_state.feedback[1])

            # Buttons untereinander (CSS sorgt für Breite und Zentrierung)
            for opt in st.session_state.options:
                if st.button(opt, key=f"sel_{opt}"):
                    is_corr = (opt == q[2])
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("UPDATE vocab SET level = ? WHERE id = ?", (max(1, q[3]+1 if is_corr else 1), q[0]))
                    conn.commit()
                    conn.close()
                    st.session_state.feedback = ("ok", "Richtig! ✅") if is_corr else ("error", f"Falsch! ❌ Richtig war: {q[2]}")
                    load_new_quiz_data()
                    st.rerun()

    # --- DATENBANK ---
    with t_datenbank:
        st.subheader("Vokabel-Datenbank")
        with st.expander("Neues Wort hinzufügen"):
            c1, c2 = st.columns(2)
            with c1: de_n = st.text_input("DE", key="add_de")
            with c2: val_n = st.text_input("VAL", key="add_val")
            if st.button("Hinzufügen"):
                if de_n and val_n:
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", ("Vallader", de_n, val_n, 1))
                    conn.commit()
                    conn.close()
                    st.rerun()
        
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT id, german, target, level FROM vocab ORDER BY id DESC", conn)
        conn.close()
        edited_df = st.data_editor(df, column_config={"id": None}, num_rows="dynamic", use_container_width=True)
        if st.button("Änderungen speichern"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM vocab")
            for _, r in edited_df.iterrows():
                conn.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", ("Vallader", r['german'], r['target'], r['level']))
            conn.commit()
            conn.close()
            st.rerun()
