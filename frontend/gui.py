import streamlit as st
import os
import json

minio_address = os.getenv("MINIO_ADDRESS", "localhost:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
minio_client = Minio(minio_address, access_key=minio_access_key, secret_key=minio_secret_key, secure=False)

bucket_name = "jobs"
object_name = "company_values.json"
response = minio_client.get_object(bucket_name, object_name)
content = response.read().decode("utf-8")
json_objects = json.loads(content)


# Funktion zum Laden der JSON-Dateien
def load_applicants_from_json(folder_path):
    applicants = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):  # Nur JSON-Dateien laden
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r") as json_file:
                data = json.load(json_file)
                applicants[data["applicant_id"]] = data
    return applicants

# JSON-Dateien-Verzeichnis
JSON_FOLDER = "./applicant_data"  # Ordner mit JSON-Dateien

# Bewerberdaten laden
applicants = load_applicants_from_json(JSON_FOLDER)

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
        documents = applicants[selected_id].get("documents", [])
        st.write("Liste der Dokumente:")
        for doc in documents:
            st.write(f"- {doc}")

