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

# CSS für das ultra-cleane Design
st.markdown("""
    <style>
    .stApp { background-color: #40E0D0; font-family: 'Inter', sans-serif; }
    
    /* Full-Width Violett Header */
    .full-header {
        background-color: #E0B0FF;
        width: 100vw;
        position: relative;
        left: 50%;
        right: 50%;
        margin-left: -50vw;
        margin-right: -50vw;
        padding: 15px 0 5px 0;
        text-align: center;
        margin-top: -60px;
        margin-bottom: 70px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .full-header h1 { color: black; margin: 0; font-weight: 700; font-size: 45px; line-height: 0.9; }
    .subtitle { color: rgba(0,0,0,0.4); font-size: 9px; margin-top: 0px; padding-top: 0px; }
    
    /* Navigation Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        justify-content: center; 
        gap: 25px;
        border-bottom: none !important; /* Entfernt den grauen Hauptstrich */
    }
    
    /* Entfernt ALLE Unterstreichungen und Linien unter den Tabs */
    .stTabs [data-baseweb="tab-border"], 
    .stTabs [data-baseweb="tab-highlight-highlight"] {
        display: none !important;
        height: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 18px;
        font-weight: 600;
        padding: 12px 45px !important;
        border-radius: 12px !important;
        border: 1px solid transparent !important; /* Platzhalter für Rahmen */
        color: #1a1a1a !important;
        margin-bottom: 10px;
    }

    /* Schreiben & Auswahl: Schöneres, helleres Blau */
    .stTabs [data-baseweb="tab"]:nth-child(1),
    .stTabs [data-baseweb="tab"]:nth-child(2) {
        background-color: #87CEEB !important; /* SkyBlue */
    }
    
    /* Datenbank: Hellgrau und rechts */
    .stTabs [data-baseweb="tab"]:nth-child(3) {
        background-color: #f0f2f6 !important;
        margin-left: auto;
    }

    /* AKTIVER BUTTON: Feiner schwarzer Rahmen */
    .stTabs [aria-selected="true"] {
        border: 1px solid black !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Quiz Wort */
    .quiz-word {
        font-size: 38px;
        font-weight: 700;
        text-align: center;
        margin: 40px 0;
        color: #1a1a1a;
    }
    
    div[data-testid="stTextInput"] {
        max-width: 450px;
        margin: 0 auto;
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

def get_new_question():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, german, target, level FROM vocab ORDER BY (level * RANDOM()) LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row

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
        st.session_state.quiz_q = get_new_question()

    # --- SCHREIBEN ---
    with t_schreiben:
        q = st.session_state.quiz_q
        if q:
            st.markdown(f'<div class="quiz-word">{q[1]}</div>', unsafe_allow_html=True)
            if st.session_state.feedback:
                if st.session_state.feedback[0] == "ok": st.success(st.session_state.feedback[1])
                else: st.error(st.session_state.feedback[1])

            user_ans = st.text_input("Antwort", key="input_schreiben", label_visibility="collapsed", placeholder="Tippen & Enter...").strip()
            
            if user_ans:
                is_corr = user_ans.lower() == q[2].lower().strip()
                new_lvl = q[3] + 1 if is_corr else 1
                conn = sqlite3.connect(DB_PATH)
                conn.execute("UPDATE vocab SET level = ? WHERE id = ?", (max(1, new_lvl), q[0]))
                conn.commit()
                conn.close()
                st.session_state.feedback = ("ok", f"Richtig! ✅ {q[2]}") if is_corr else ("error", f"Falsch! ❌ Richtig: {q[2]}")
                st.session_state.quiz_q = get_new_question()
                st.rerun()

    # --- AUSWAHL ---
    with t_auswahl:
        q = st.session_state.quiz_q
        if q:
            st.markdown(f'<div class="quiz-word">{q[1]}</div>', unsafe_allow_html=True)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT target FROM vocab WHERE target != ? ORDER BY RANDOM() LIMIT 3", (q[2],))
            opts = [o[0] for o in cursor.fetchall()] + [q[2]]
            random.shuffle(opts)
            conn.close()
            
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                ans = st.radio("Optionen", opts, label_visibility="collapsed")
                if st.button("Prüfen"):
                    is_corr = (ans == q[2])
                    new_lvl = q[3] + 1 if is_corr else 1
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("UPDATE vocab SET level = ? WHERE id = ?", (max(1, new_lvl), q[0]))
                    conn.commit()
                    conn.close()
                    st.session_state.quiz_q = get_new_question()
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
        if st.button("Alle Änderungen speichern"):
            conn = sqlite3.connect(DB_PATH)
            conn.execute("DELETE FROM vocab")
            for _, r in edited_df.iterrows():
                conn.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", ("Vallader", r['german'], r['target'], r['level']))
            conn.commit()
            conn.close()
            st.rerun()
