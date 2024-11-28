import streamlit as st
import os
import json
from minio import Minio
from fastapi import HTTPException

# MinIO-Konfiguration
minio_address = os.getenv("MINIO_ADDRESS", "localhost:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
minio_client = Minio(minio_address, access_key=minio_access_key, secret_key=minio_secret_key, secure=False)

bucket_name = "applicants"

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
    </style>
""", unsafe_allow_html=True)

# Logo und Titel links oben
st.markdown("""
    <div class="logo-container">
        <img src="https://via.placeholder.com/100" alt="Logo" style="margin-right: 10px;">
        <h2 style="color: white;">Bewerberverwaltung</h2>
    </div>
""", unsafe_allow_html=True)

# Spaltenlayout
col1, col2, col3 = st.columns([1, 2, 1])

# Rechte Spalte: "Mailvorlage" und "Persönliche Daten"
with col3:
    st.header("Optionen")
    st.subheader("Persönliche Daten")
    if st.session_state.get("selected_id"):
        selected_applicant = applicants[st.session_state["selected_id"]]
        personal_data = selected_applicant.get("personal_data", {})
        st.write({k: v for k, v in personal_data.items() if k != "Name"})

    st.subheader("Mailvorlage")
    mail_type = st.selectbox("Wähle eine Aktion:", ["Absage", "Einladung", "Sonstiges"])
    if st.button("Mail generieren"):
        st.success(f"Mail für {mail_type} generiert!")

# Linke Spalte: Bewerber IDs
with col1:
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
            challenge_path = f"{selected_id}/challenge.json"
            challenge_obj = minio_client.get_object(bucket_name, challenge_path)
            challenge_data = json.loads(challenge_obj.read().decode("utf-8"))
            st.write(challenge_data.get("description", "Keine Beschreibung verfügbar."))
            st.subheader("Aufgabenstellung")
            st.write(challenge_data.get("task", "Keine Aufgabenstellung verfügbar."))
        except:
            st.error("Challenge-Daten nicht verfügbar.")

        st.subheader("Beurteilung der Lösung")
        try:
            # Lade solution.json
            ChallengeSolution_path = f"{selected_id}/ChallengeSolution.json"
            ChallengeSolution_obj = minio_client.get_object(bucket_name, ChallengeSolution_path)
            ChallengeSolution_data = json.loads(ChallengeSolution_obj.read().decode("utf-8"))
            st.write(ChallengeSolution_data.get("evaluation", "Keine Bewertung verfügbar."))
        except:
            st.error("Bewertung nicht verfügbar.")

