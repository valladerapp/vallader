import streamlit as st
import sqlite3
import random
import os
import pandas as pd

# Pfad zur Datenbank (lokal im selben Ordner)
DB_PATH = "languages.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vocab 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       language TEXT, german TEXT, target TEXT, level INTEGER)''')
    conn.commit()
    conn.close()

# Initialisierung der Datenbank beim Start
init_db()

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="Vallader", layout="centered")

# Design & CSS
st.markdown("""
    <style>
    /* Hintergrund der gesamten App */
    .stApp { background-color: #40E0D0; }
    
    /* Violetter Header */
    .header { 
        background-color: #E0B0FF; 
        padding: 25px; 
        border-radius: 15px; 
        text-align: center; 
        margin-bottom: 25px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .header h1 { color: black; margin: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Footer Styling */
    .footer { text-align: center; color: #555; font-size: 12px; margin-top: 50px; padding: 20px; }
    
    /* Buttons einheitlich machen */
    .stButton>button { width: 100%; border-radius: 8px; }
    </style>
    
    <div class="header"><h1>Vallader</h1></div>
    """, unsafe_allow_html=True)

# --- SESSION STATE (Zustand der App merken) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'quiz_q' not in st.session_state:
    st.session_state.quiz_q = None

# --- LOGIN BEREICH ---
if not st.session_state.logged_in:
    st.write("### Willkommen - bitte anmelden")
    with st.container():
        pw = st.text_input("Passwort", type="password")
        if st.button("Einloggen"):
            if pw == "Vallader2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Falsches Passwort")

# --- HAUPTBEREICH (Eingeloggt) ---
else:
    # Navigation über Tabs
    tab1, tab2, tab3 = st.tabs(["📝 Lernen (Tippen)", "🔘 Lernen (Auswahl)", "🗄️ Datenbank"])

    # --- DATENBANK TAB ---
    with tab3:
        st.subheader("Vokabeln verwalten")
        
        # Eingabeformular
        with st.expander("Neue Vokabel hinzufügen", expanded=True):
            col1, col2 = st.columns(2)
            with col1: de = st.text_input("Deutsch", key="de_add")
            with col2: val = st.text_input("Vallader", key="val_add")
            
            if st.button("In Datenbank speichern"):
                if de and val:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO vocab (language, german, target, level) VALUES (?,?,?,?)", 
                                   ("Vallader", de, val, 1))
                    conn.commit()
                    conn.close()
                    st.success(f"'{val}' wurde hinzugefügt!")
                    st.rerun()

        st.divider()
        
        # Suche und Tabelle
        search = st.text_input("Suchen in der Datenbank...", placeholder="Wort eingeben...")
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT id, german, target, level FROM vocab"
        if search:
            query += f" WHERE german LIKE '%{search}%' OR target LIKE '%{search}%'"
        
        df = pd.read_sql_query(query + " ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("Liste aktualisieren"):
            st.rerun()
        conn.close()

    # --- QUIZ FUNKTIONEN ---
    def get_new_question():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Gewichtung nach Level: Niedrigere Level kommen öfter vor
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
                st.write(f"### Was heißt: **{q[1]}**?") # Deutsche Frage
                
                if mode == "tippen":
                    user_ans = st.text_input("Antwort hier tippen:", key=f"input_{mode}", placeholder="..." ).strip()
                    if st.button("Prüfen", key=f"check_{mode}"):
                        if user_ans.lower() == q[2].lower().strip():
                            st.success(f"Richtig! ✅ ({q[2]})")
                            update_level(q[0], q[3], True)
                        else:
                            st.error(f"Leider falsch. ❌ Richtig wäre: {q[2]}")
                            update_level(q[0], q[3], False)
                
                else: # Auswahl-Modus (Multiple Choice)
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    # 3 falsche Antworten holen
                    cursor.execute("SELECT target FROM vocab WHERE target != ? ORDER BY RANDOM() LIMIT 3", (q[2],))
                    options = [o[0] for o in cursor.fetchall()] + [q[2]]
                    random.shuffle(options)
                    conn.close()
                    
                    user_choice = st.radio("Wähle die richtige Übersetzung:", options, key=f"radio_{mode}")
                    if st.button("Antwort einloggen", key=f"check_{mode}"):
                        if user_choice == q[2]:
                            st.success(f"Richtig! ✅")
                            update_level(q[0], q[3], True)
                        else:
                            st.error(f"Falsch. ❌ Richtig wäre: {q[2]}")
                            update_level(q[0], q[3], False)
            else:
                st.info("Die Datenbank ist noch leer. Füge zuerst Vokabeln im Tab 'Datenbank' hinzu!")

# --- FOOTER ---
st.markdown('<div class="footer">designed and powered by akeora gmbh</div>', unsafe_allow_html=True)