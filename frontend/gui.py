import streamlit as st
import os
import json
from minio import Minio
from fastapi import HTTPException
import time

# MinIO-Konfiguration
minio_address = os.getenv("MINIO_ADDRESS", "localhost:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
minio_client = Minio(minio_address, access_key=minio_access_key, secret_key=minio_secret_key, secure=False)

bucket_name = "applicants"
bucket_jobs = "jobs"

def display_json(data):
    for category, questions in data.items():
        if not isinstance(questions, list):
            continue
        with st.expander(category, expanded=False):  # Dropdown-Menü für jede Kategorie
            for item in questions:
                if category == "Codingaufgabe":
                    st.subheader("Aufgabe")
                    st.write(item.get("Aufgabe", "Keine Aufgabe verfügbar."))
                    st.subheader("Bewertung")
                    st.write(item.get("Bewertung", "Kein Bewertungsmaßstab verfügbar."))
                else:
                    st.subheader("Frage")
                    st.write(item.get("Frage", "Keine Frage verfügbar."))
                    st.subheader("Bewertung")
                    st.write(item.get("Bewertung", "Kein Bewertungsmaßstab verfügbar."))

def display_solution_json(data):
    for category, questions in data.items():
        if category == "Zusammenfassung":
            st.subheader("Zusammenfassung")
            st.write(questions)
        if category == "Empfehlung":
            st.subheader("Empfehlung")
            st.write(questions)
        if not isinstance(questions, list):
            continue
        with st.expander(category, expanded=False):  # Dropdown-Menü für jede Kategorie
            for item in questions:
                if category == "Codingaufgabe":
                    st.subheader("Frage")
                    st.write(item.get("Frage", "Keine Frage verfügbar."))
                    st.subheader("Antwort")
                    st.write(item.get("Antwort", "Kein Bewertungsmaßstab verfügbar."))
                    st.subheader("Bewertung")
                    st.write(item.get("Bewertung", "Kein Bewertungsmaßstab verfügbar."))
                else:
                    st.subheader("Frage")
                    st.write(item.get("Frage", "Keine Frage verfügbar."))
                    st.subheader("Antwort")
                    st.write(item.get("Antwort", "Kein Bewertungsmaßstab verfügbar."))
                    st.subheader("Bewertung")
                    st.write(item.get("Bewertung", "Kein Bewertungsmaßstab verfügbar."))

def load_objects_from_minio(bucket_name):
    # Überprüfen, ob der Bucket existiert
    if not minio_client.bucket_exists(bucket_name):
        raise HTTPException(status_code=404, detail="Bucket does not exist.")
    
    applicants = {}
    objects = minio_client.list_objects(bucket_name, recursive=True)
    
    for obj in objects:
        parts = obj.object_name.split("/")
        if len(parts) > 1 and parts[-1] == "metadata.json":
            applicant_id = parts[0]
            response = minio_client.get_object(bucket_name, obj.object_name)
            content = response.read().decode("utf-8")
            data = json.loads(content)
            applicants[applicant_id] = data
    return applicants

# Bewerberdaten aus MinIO laden
applicants = load_objects_from_minio(bucket_name)

# Streamlit Layout
st.set_page_config(layout="wide", page_title="Bewerberportal")
st.markdown("""
    <style>
        body {
            background-color: #2e2e2e;  /* Mattgrauer Hintergrund */
            color: white;  /* Weiße Schrift */
        }
        .logo-container {
            display: flex;
            justify-content: left;
            align-items: center;
            margin-bottom: 20px;
        }
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 14px;
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
    </style>
""", unsafe_allow_html=True)

# Logo und Titel links oben


# Spaltenlayout
col1, col2, col3 = st.columns([1, 2, 1])

# Rechte Spalte: "Mailvorlage" und "Persönliche Daten"
with col3:
    st.header("Optionen")
    st.subheader("Persönliche Daten")
    if st.session_state.get("selected_id"):
        selected_applicant = applicants[st.session_state["selected_id"]]
        personal_data = selected_applicant.get("personal_data", {})
        #st.write({k: v for k, v in personal_data.items() if k != "Name"})
        st.write("Alter: "+str(personal_data.get("Alter", 40)))
        st.write("Wohnort: "+personal_data.get("Wohnort", "Augsburg"))

    st.subheader("Mailvorlage")
    mail_type = st.selectbox("Wähle eine Aktion:", ["Absage", "Einladung", "Aufgabe senden", "Sonstiges"])
    if st.button("Mail generieren"):
        st.success(f"Mail für {mail_type} generiert!")
        st.session_state.button = True
        st.session_state.mail_type = mail_type
        st.session_state.time_sent = time.time()
    if 'time_sent' not in st.session_state:
        st.session_state.time_sent = 0
    wait_time = 5
    not_sent = (st.session_state.time_sent == 0)
    if time.time() > st.session_state.time_sent + wait_time and not not_sent:
        st.button("You are hired!")

# Linke Spalte: Bewerber IDs
with col1:
    st.markdown("""
    <div class="logo-container">
        <img src="https://qbn.world/wp-content/uploads/2022/06/logo-sq-3.png" 
             alt="Logo" 
             style="margin-right: 10px; height: 300px; width: 370px;">
    </div>
""", unsafe_allow_html=True)
    st.header("Bewerber IDs")
    selected_id = st.selectbox("Wähle eine Bewerber ID:", list(applicants.keys()), key="selected_id")

# Mittlere Spalte: Challenge-Daten
with col2:
    st.header("Challenge Übersicht")
    if selected_id:
        applicant_data = applicants[selected_id]
        st.subheader("Beschreibung der Challenge")
        try:
            # Lade challenge.json
            job_id = applicant_data.get("job_id")
            challenge_path = f"{job_id}/challenge.json"
            challenge_obj = minio_client.get_object(bucket_jobs, challenge_path)
            challenge_data = json.loads(challenge_obj.read().decode("utf-8"))
            display_json(challenge_data)  # Dropdown-Darstellung
        except Exception as e:
            st.error(e)

        # set session data if not exists
        if 'button' not in st.session_state:
            st.session_state.button = False
        if 'mail_type' not in st.session_state:
            st.session_state.mail_type = ""
        if 'time_sent' not in st.session_state:
            st.session_state.time_sent = 0
        if 'spinner_finished' not in st.session_state:
            st.session_state.spinner_finished = False

        st.subheader("Challengeübersicht")
        if st.session_state.button and st.session_state.mail_type == "Aufgabe senden":
            #wait_time = 5
            #if time.time() > st.session_state.time_sent + wait_time:
            #    st.write("Antwort ist da")
            #else:
            #    st.write("Warte auf Antwort")
            #    st.spinner("Warte auf Antwort")
            if not st.session_state.spinner_finished:
                with st.spinner('Wait for it...'):
                    time.sleep(5)
                    st.session_state.spinner_finished = True
                    st.experimental_rerun()
            st.success("Antwort ist da")
        else:
            st.write("Keine Challenge an Bewerber gesendet")

        st.subheader("Beurteilung der Lösung")
        try:
            wait_time = 5
            not_sent = (st.session_state.time_sent == 0)
            if time.time() > st.session_state.time_sent + wait_time and not not_sent:
                # Lade solution.json after response received
                job_id = applicant_data.get("job_id")
                ChallengeSolution_path = f"{job_id}/challengeSolution.json"
                ChallengeSolution_obj = minio_client.get_object(bucket_jobs, ChallengeSolution_path)
                ChallengeSolution_data = json.loads(ChallengeSolution_obj.read().decode("utf-8"))
                display_solution_json(ChallengeSolution_data)
            else:
                st.write("Bewertung noch nicht verfügbar.")
        except Exception as e:
            st.error("Bewertung nicht verfügbar.")
            st.error(e)

