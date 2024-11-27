import requests

API_URL = "http://localhost:8001/generate"

def extract_requirements_and_skills_with_json(job_posting_json):
    """
    Kombiniert die Anforderungen aus der Stellenbeschreibung mit Informationen aus einem JSON-Datensatz.

    Args:
        job_posting_json (dict): JSON-Daten mit Stellenbeschreibung, Fähigkeiten und anderen Informationen.

    Returns:
        dict: Eine JSON-kompatible Struktur mit Anforderungen, Fähigkeiten und Technologien.
    """
    # Extrahiere Informationen aus dem JSON
    job_title = job_posting_json.get("title", "N/A")
    job_description = job_posting_json.get("text", "Keine Beschreibung verfügbar.")
    it_skills = job_posting_json.get("skills", {}).get("IT Skills", "")
    soft_skills = job_posting_json.get("skills", {}).get("Soft Skills", "")

    # Prompt für die Modellanfrage
    prompt = f"""
    [STELLENBESCHREIBUNG]
    {job_description}

    [JOB-TITEL]
    {job_title}

    [ZUSÄTZLICHE INFORMATIONEN]
    IT-Fähigkeiten: {it_skills}
    Soft Skills: {soft_skills}

    [INSTRUCTIONS]
    Analysiere die Stellenbeschreibung und die zusätzlichen Informationen. Extrahiere die Anforderungen in Stichpunkten.
    Für jede Anforderung definiere:
    - Die relevanten Fähigkeiten (z. B. Problemlösung, Teamarbeit, Projektmanagement, technisches Fachwissen).
    - Die zugehörigen Technologien oder Tools (z. B. Programmiersprachen, Software, Frameworks).

    Gib das Ergebnis als JSON zurück mit folgendem Format:
    {{
        "Anforderungen": [
            {{
                "Anforderung": "<Text der Anforderung>",
                "Fähigkeiten": ["<Fähigkeit 1>", "<Fähigkeit 2>", ...],
                "Technologien": ["<Technologie 1>", "<Technologie 2>", ...]
            }},
            ...
        ]
    }}
    """

    # Nachricht an das Modell senden
    messages = [{"role": "user", "content": prompt}]
    payload = {"messages": messages}

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Fehler bei der Kommunikation mit der API: {e}"}


def generate_questions_from_requirements(requirements_json, question_count=10, job_level="Junior"):
    """
    Generiert Fragen basierend auf extrahierten Anforderungen, Fähigkeiten und Technologien.

    Args:
        requirements_json (dict): JSON-Struktur mit Anforderungen, Fähigkeiten und Technologien.
        question_count (int): Anzahl der zu generierenden Fragen.
        job_level (str): Schwierigkeitsgrad ("Junior" oder "Senior").

    Returns:
        dict: Eine JSON-kompatible Struktur mit generierten Fragen und Bewertungsmaßstäben nach Kategorien.
    """
    # Anforderungen in Text umwandeln
    requirements_text = "\n".join(
        [f"- {req['Anforderung']} (Fähigkeiten: {', '.join(req['Fähigkeiten'])}; Technologien: {', '.join(req['Technologien'])})"
         for req in requirements_json.get("Anforderungen", [])]
    )

    # Prompt für die Fragen- und Bewertungsmaßstab-Generierung
    prompt = f"""
    [ANFORDERUNGEN]
    {requirements_text}

    [INSTRUCTIONS]
    Basierend auf den oben genannten Anforderungen und unter Berücksichtigung, dass die Stelle für ein {job_level}-Level ausgeschrieben ist, 
    generiere eine Liste von {question_count} Interviewfragen. Die Fragen sollten eine breite Palette abdecken, von grundlegenden bis zu komplexen Fragestellungen.
    
    Unterteile die Fragen in die folgenden Kategorien:
    1. Fachliche Fragen: Überprüfung des technischen Wissens und der beruflichen Qualifikationen.
    2. Persönliche Eignung: Überprüfung von Soft Skills wie Teamfähigkeit, Kommunikationsstärke oder Führungsqualitäten (falls relevant).
    3. Motivationsfragen: Überprüfung, warum der Bewerber für diese Rolle geeignet ist und was ihn an der Stelle motiviert.

    Ergänze zu jeder Frage einen Bewertungsmaßstab, der beschreibt, wie eine Antwort bewertet werden kann. 
    Gib das Ergebnis als JSON zurück mit den folgenden Schlüsseln:
    - Kategorien: Fachliche Fragen, Persönliche Eignung, Motivationsfragen.
    - Jede Frage sollte ein zugehöriges Bewertungsmaßstab-Feld haben.
    """

    # Nachricht an das Modell senden
    messages = [{"role": "user", "content": prompt}]
    payload = {"messages": messages}

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Fehler bei der Kommunikation mit der API: {e}"}