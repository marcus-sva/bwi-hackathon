import streamlit as st
import os
import json
from minio import Minio
#from minio.error import ResponseError
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

    # Alle Objekte im Bucket durchlaufen
    objects = minio_client.list_objects(bucket_name, recursive=True)
    
    for obj in objects:
        # Extrahiere den Ordnernamen (Bewerber-ID) und lade die 'metadata.json'
        parts = obj.object_name.split("/")
        
        if len(parts) > 1 and parts[-1] == "metadata.json":  # Sicherstellen, dass es die 'metadata.json' ist
            applicant_id = parts[0]  # Der erste Teil des Objektnamens ist die Bewerber-ID
#            try:
                # Lade das 'metadata.json' Objekt aus MinIO
            response = minio_client.get_object(bucket_name, obj.object_name)
            content = response.read().decode("utf-8")
            data = json.loads(content)
                
                # Bewerberdaten speichern
            applicants[applicant_id] = data
                
#            except ResponseError as e:
#                print(f"Fehler beim Laden der Datei {obj.object_name}: {e}")
#    
    return applicants

# Bewerberdaten aus MinIO laden
applicants = load_objects_from_minio(bucket_name)

# Streamlit Layout
st.set_page_config(layout="wide")

# Spaltenlayout
col1, col2, col3 = st.columns([1, 2, 1])

# Linke Spalte: Bewerber IDs
with col1:
    st.header("Bewerber IDs")
    selected_id = st.selectbox("Wähle eine Bewerber ID:", list(applicants.keys()))

# Mittlere Spalte: Zusammenfassung des Bewerbers
with col2:
    st.header("Bewerber Details")
    
    if selected_id:
        # Bewerberdaten laden
        applicant_data = applicants[selected_id]
        
        # Persönliche Daten (Anonymisiert)
        st.subheader("Persönliche Daten (Anonymisiert)")
        personal_data = applicant_data.get("personal_data", {})
        anonymized_data = {k: v for k, v in personal_data.items() if k != "Name"}
        st.write(anonymized_data)
        
        # KI-Bewertung
        st.subheader("KI-Einordnung")
        st.write(applicant_data.get("evaluation", "Keine Bewertung verfügbar."))
        
        # Mailvorlagen
        st.subheader("Mailvorlage")
        mail_type = st.selectbox("Wähle eine Aktion:", ["Absage", "Einladung", "Sonstiges"])
        if st.button("Mail generieren"):
            st.success(f"Mail für {mail_type} generiert!")

# Rechte Spalte: Dokumente des Bewerbers
with col3:
    st.header("Dokumente")
    if selected_id:
        documents = applicant_data.get("documents", [])
        st.write("Liste der Dokumente:")
        for doc in documents:
            st.write(f"- {doc}")


