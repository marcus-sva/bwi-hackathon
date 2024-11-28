import requests, json

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
        "Stellenbeschreibung": [
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
    Basierend auf den oben genannten Fähigkeiten und Technologien unter Berücksichtigung, dass die Stelle für ein {job_level}-Level ausgeschrieben ist, 
    generiere eine Liste von {question_count} Interviewfragen. Die Fragen sollten eine breite Palette abdecken, von grundlegenden bis zu komplexen Fragestellungen.
    

    Unterteile die Fragen in die folgenden Kategorien:
    1. Technische Fragen: Überprüfung des Wissens ausschließlich zu den genannten Technologien oder Tools (z. B. Programmiersprachen, Software, Frameworks) der Stellenbeschreibung. 
    2. Persönliche Eignung: Überprüfung von Soft Skills z.B. Teamfähigkeit, Kommunikationsstärke oder andere Soft Skills die zur .
    3. Codingaufgabe: Überprüfung, warum der Bewerber auf {job_level}-Level in einer der genannten Programmiersprachen coden kann.
    

    Beispiel:
    "Frage": "Eine klassische Retrospektive wird im Team regelmäßig durchgeführt. Ein Post Mortem allerdings nur bei Bedarf. Bitte gehe auf folgende Fragen näher ein: Was ist der Unterschied zwischen einer Retro und einem Post Mortem? Wann und warum wird ein Post Mortem hauptsächlich durchgeführt? Nenne das Ziel eines Post Mortems und gehe darauf ein, was muss alles beachtet werden sollte."
    
    "Frage": "Die Bundesregierung muss im Notfall eigene Staatsbürger im Ausland aus Gefahr für Leib und Leben retten können. 
    Durch ein gemeinsames Lagebild aller beteiligten Bundesressorts soll eine schnelle, flexible und mobile Krisenbewältigung gefördert werden. 
    KVInfoSysBund wird im Kern ein von der BWI betriebenes webbasiertes Geo-
    Informationssystem zur individuellen Lagebilddarstellung und ressortübergreifenden
    Zusammenarbeit sein und als Datendrehscheibe zwischen verschiedenen internen und
    externen Datenquellen dienen.
    Ihre Aufgabe ist nun einen Backend Service zu entwickeln, der Schnittstellen zur Verfügung
    stellt, um Points of Interest zu speichern und abzurufen. Ein vorhandener, imaginärer Service
    erwartet Benachrichtigungen bei Datenänderungen.
    Ein Point of Interest besteht aus den folgenden Informationen: 
    Name, Geo-Koordinate, Art des POI (Hafen, Flughafen, Krankenhaus…), Anschrift ,Spezielle Felder je nach Art des POI:, Hafen: 0-n Piers mit Name und Geo-Koordinate, Flughafen: 0-n Landebahnen mit Himmelsrichtung und Länge, Krankenhaus: Anzahl Betten auf Intensivstation und Pflegestation. 
    Ihre Aufgaben sind konkret: Implementieren Sie die geeigneten Endpunkte, Persistieren Sie die Daten in einer Datenbank Ihrer Wahl, Versenden Sie Benachrichtigungen bei Datenänderungen, Achten Sie auf eine geeignete Testabdeckung"
    

    Erstelle die hälfte der {question_count} Fragen als Technische Fragen und den Rest als Persönliche Eignung oder Codingaufgabe.
    Formatiere das Ergebnis exakt im folgenden JSON-Format:
    {{
        "Technische Fragen": [
            {{
                "Frage": "<Text der technischen Frage>",
                "Bewertungsmaßstab": "<Bewertungsmaßstab für die Antwort>"
            }},
            ...
        ],
        "Persönliche Eignung": [
            {{
                "Frage": "<Text der Frage zur persönlichen Eignung>",
                "Bewertungsmaßstab": "<Bewertungsmaßstab für die Antwort>"
            }},
            ...
        ],
        "Codingaufgabe": [
            {{
                "Aufgabe": "<Text der Codingaufgabe>",
                "Bewertungsmaßstab": "<Bewertungsmaßstab für die Antwort>"
            }},
            ...
        ]
    }}

    Achte darauf, dass:
    - Die Fragen klar und spezifisch formuliert sind.
    - Jede Kategorie relevante Fragen enthält.
    - Die Bewertungsmaßstäbe konkrete Hinweise enthalten, um Antworten sinnvoll zu bewerten.

    Liefere ausschließlich die JSON-Ausgabe als Ergebnis.
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