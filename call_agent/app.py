import requests
import json
import psycopg2
import prompts
import time  # Import für die Wartefunktion

from psycopg2.extras import RealDictCursor
from flask import jsonify

# --- Bestehende Tool- und Hilfsfunktionen (unverändert) ---

def get_current_weather(location: str) -> str:
    """
    Ruft die aktuellen Wetterbedingungen für einen bestimmten Ort ab.
    """
    print(f"[TOOL] Frage Wetter für {location} ab...")
    if location.lower() == "hamburg":
        return json.dumps({"location": location, "temperature": "20°C", "conditions": "sonnig"})
    elif location.lower() == "berlin":
        return json.dumps({"location": location, "temperature": "18°C", "conditions": "bewölkt"})
    else:
        return json.dumps({"location": location, "error": "Wetterdaten nicht verfügbar"})


def get_db_connection():
    """
    Stellt eine Verbindung zur PostgreSQL-Datenbank her.
    """
    conn = psycopg2.connect(
        host="terminagent-db.cty0uqagcewj.us-west-2.rds.amazonaws.com",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="2WiIo5_g2-c+",
    )
    conn.autocommit = True
    return conn


def call_external_schedule_api(user_id: str, doctor_id: str, appointment_reason: str,
                               additional_remark: str, date: str, time_range_start: str,
                               time_range_end: str) -> str:
    """
    Simuliert den Aufruf einer externen API, um eine Anrufaufgabe zu planen.
    """
    print(f"[TOOL] Plane Anrufaufgabe für Terminbuchung...")
    print(f"  User ID: {user_id}")
    print(f"  Doctor ID: {doctor_id}")
    print(f"  Reason: {appointment_reason}")
    print(f"  Date: {date}, Time: {time_range_start}-{time_range_end}")

    external_api_url = "http://34.217.126.24/schedule_call_task"
    payload = {
        "user_id": user_id,
        "doctor_id": doctor_id,
        "appointment_reason": appointment_reason,
        "additional_remark": additional_remark,
        "date": date,
        "time_range_start": time_range_start,
        "time_range_end": time_range_end
    }
    try:
        response = requests.post(external_api_url, json=payload)
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Failed to call external API: {str(e)}", "status": "failed"})


AVAILABLE_TOOLS = {
    "get_current_weather": get_current_weather,
    "schedule_call_task": call_external_schedule_api
}

TOOL_DEFINITIONS = [
    {
        "name": "get_current_weather",
        "description": "Ruft die aktuellen Wetterbedingungen für einen bestimmten Ort ab.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Die Stadt, für die das Wetter abgefragt werden soll."}},
            "required": ["location"]
        }
    },
    {
        "name": "schedule_call_task",
        "description": "Plant eine Anrufaufgabe zur Terminbuchung für einen Benutzer und einen Arzt mit spezifischen Details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Die ID des Benutzers, der den Anruf plant."},
                "doctor_id": {"type": "string",
                              "description": "Die ID des Arztes, bei dem ein Termin gebucht werden soll."},
                "appointment_reason": {"type": "string",
                                       "description": "Der Grund für den Termin, z.B. 'Kontrolluntersuchung', 'Erstberatung'."},
                "additional_remark": {"type": "string",
                                      "description": "Zusätzliche Anmerkungen oder Details zum Termin. Wenn keine vorhanden sind, ein leerer String oder 'N/A'."},
                "date": {"type": "string", "description": "Das gewünschte Datum des Anrufs im Format YYYY-MM-DD."},
                "time_range_start": {"type": "string",
                                     "description": "Die Startzeit des gewünschten Zeitfensters für den Anruf im Format HH:MM."},
                "time_range_end": {"type": "string",
                                   "description": "Die Endzeit des gewünschten Zeitfensters für den Anruf im Format HH:MM."}
            },
            "required": ["user_id", "doctor_id", "appointment_reason", "additional_remark", "date", "time_range_start",
                         "time_range_end"]
        }
    }
]


def create_claude_session(api_url: str, model_id: str) -> dict:
    """
    Initialisiert und konfiguriert eine neue Konversations-Session.
    """
    # print(f"Starte Claude Session mit Modell: {model_id}")
    session = {
        "api_url": api_url,
        "model_id": model_id,
        "conversation_history": [],
        "tools": TOOL_DEFINITIONS,
        "available_tools": AVAILABLE_TOOLS
    }
    return session


def process_prompt_in_session(claude_session: dict, user_prompt: str) -> tuple[str, dict]:
    """
    Verarbeitet einen einzelnen Prompt innerhalb einer bestehenden Session.
    """
    # print("[CLIENT] Sende Benutzer-Prompt an Claude...")
    api_url, model_id, conversation_history, tools, available_tools = (
        claude_session['api_url'], claude_session['model_id'], claude_session['conversation_history'],
        claude_session['tools'], claude_session['available_tools']
    )
    request_payload = {
        "prompt": user_prompt, "modelId": model_id, "messages": conversation_history, "tools": tools
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(api_url, headers=headers, json=request_payload)
        response.raise_for_status()
        body_content = json.loads(response.json().get("body", "{}"))
        generated_text = body_content.get("generated_text", "")
        print(generated_text)
        tool_use_response = body_content.get("tool_use")
        claude_session['conversation_history'] = body_content.get("conversation_history", conversation_history)

        if tool_use_response:
            # ... (Tool-Verarbeitungslogik bleibt unverändert)
            print(claude_session)
            return "Tool-Nutzung wird verarbeitet...", claude_session
        elif generated_text:
            return generated_text, claude_session
        else:
            return "Claude hat keine Antwort geliefert.", claude_session

    except requests.exceptions.RequestException as e:
        return f"[CLIENT ERROR] Fehler bei der Anfrage: {e}", claude_session
    except Exception as e:
        return f"[CLIENT ERROR] Unerwarteter Fehler: {e}", claude_session


# --- NEUE FUNKTIONEN für das Polling und die automatische Verarbeitung ---

def trigger_claude_for_task(task: dict, claude_session: dict):
    """
    Erstellt eine neue Claude-Session für eine bestimmte Aufgabe und startet sie.
    """
    print(f"\n--- [SYSTEM] Neue Aufgabe gefunden: ID {task['task_id']}. Starte Claude-Sitzung. ---")


    # 2. Den initialen System-Prompt verarbeiten, um die Rolle des Assistenten festzulegen
    _, claude_session = process_prompt_in_session(claude_session, prompts.initialization)

    # 3. Einen spezifischen Prompt aus den Aufgabendetails erstellen
    task_prompt = (
        f"Hallo, es liegt ein neuer Terminauftrag aus der Datenbank vor. "
        f"Hier sind die Details:\n"
        f"- Benutzer-ID: {task['user_id']}\n"
        f"- Arzt-ID: {task['user_id']}\n"
        f"- Auftrags-ID: {task['task_id']}\n"
        f"- Grund des Termins: {task['appointment_reason']}\n"
        f"- Gewünschtes Datum: {task.get('appointment_date', 'N/A')}\n"
        f"- Gewünschtes Zeitfenster: {task.get('time_range_start', 'N/A')} - {task.get('time_range_end', 'N/A')}\n\n"
        f"Bitte bestätige den Erhalt dieser Aufgabe und leite die nächsten Schritte ein."
    )

    print(f"[SYSTEM] Sende folgenden Kontext an Claude: \n{task_prompt}")

    # 4. Den aufgabenspezifischen Prompt in der Session verarbeiten
    response_text, _ = process_prompt_in_session(claude_session, task_prompt)

    print(f"\n[CLAUDE ANTWORT für Aufgabe {task['task_id']}]")
    print(f"--- [SYSTEM] Verarbeitung für Aufgabe {task['task_id']} abgeschlossen. ---\n")


def check_and_process_new_tasks(processed_ids: set, claude_session: dict):
    """
    Sucht nach neuen Aufgaben in der DB und löst deren Verarbeitung aus.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # WICHTIG: Die Abfrage muss eine eindeutige ID (z.B. task_id) enthalten
        cursor.execute(
            """
            SELECT *
            FROM tasks
            """
        )
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        for task in tasks:
            if task['task_id'] not in processed_ids:
                # Neue Aufgabe gefunden, Verarbeitung auslösen
                trigger_claude_for_task(task, session)
                # Die ID zur Liste der bearbeiteten Aufgaben hinzufügen
                processed_ids.add(task['task_id'])

    except psycopg2.Error as e:
        print(f"[DB ERROR] Datenbankfehler: {e}")
    except Exception as e:
        print(f"[SYSTEM ERROR] Ein unerwarteter Fehler ist aufgetreten: {e}")


# --- Hauptausführung: Ersetzt die interaktive Schleife durch einen Polling-Mechanismus ---

if __name__ == "__main__":
    API_GATEWAY_URL = "https://0621ja9smk.execute-api.us-west-2.amazonaws.com/dev/prompt"
    CLAUDE_HAIKU_MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"

    # Ein Set, um die IDs der bereits bearbeiteten Aufgaben zu speichern
    processed_task_ids = set()

    print("Starte den automatischen Task-Processor...")
    print("Das Programm sucht alle 5 Sekunden nach neuen Aufgaben in der Datenbank.")
    print("Drücken Sie STRG+C, um das Programm zu beenden.")

    session = create_claude_session(API_GATEWAY_URL, CLAUDE_HAIKU_MODEL_ID)
    process_prompt_in_session(session, prompts.initialization)

    try:
        #while True:
            # Nach neuen Aufgaben suchen und diese verarbeiten
            check_and_process_new_tasks(processed_task_ids, session)

            # 5 Sekunden warten bis zur nächsten Überprüfung
           # time.sleep(5)

    except KeyboardInterrupt:
        print("\nProgramm wird beendet. Auf Wiedersehen!")