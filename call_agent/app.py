import json
import time  # Import für die Wartefunktion
from typing import Optional

import prompts
import psycopg2
import requests
from flask import jsonify
from psycopg2.extras import RealDictCursor


# DATABASE CONNECTION AND TASK PROCESSING
def get_db_connection():
    """Stellt eine Verbindung zur PostgreSQL-Datenbank her."""
    conn = psycopg2.connect(
        host="terminagent-db.cty0uqagcewj.us-west-2.rds.amazonaws.com",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="2WiIo5_g2-c+",
    )
    conn.autocommit = True
    return conn


def check_for_open_tasks() -> tuple[Optional[str], Optional[dict]]:
    """
    Sucht nach offene Tasks in der DB und gibt ggf. die ID und ein task dictionary zurück.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # WICHTIG: Die Abfrage muss eine eindeutige ID (z.B. task_id) enthalten
        cursor.execute(
            """
            SELECT *
            FROM tasks
            WHERE status = 'open'
            """
        )  # TODO: Also check in SQL that doctor office is opened at current time and date
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        if tasks:
            # Found at least one open task
            return tasks[0]["task_id"], tasks
        else:
            return None, None

    except psycopg2.Error as e:
        print(f"[DB ERROR] Datenbankfehler: {e}")
    except Exception as e:
        print(f"[SYSTEM ERROR] Ein unerwarteter Fehler ist aufgetreten: {e}")


# CLAUDE LLM API INTERACTIONS
TOOL_DEFINITIONS = [
    {
        "name": "schedule_call_task",
        "description": "Plant eine Anrufaufgabe zur Terminbuchung für einen Benutzer und einen Arzt mit spezifischen Details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Die ID des Benutzers, der den Anruf plant.",
                },
                "doctor_id": {
                    "type": "string",
                    "description": "Die ID des Arztes, bei dem ein Termin gebucht werden soll.",
                },
                "appointment_reason": {
                    "type": "string",
                    "description": "Der Grund für den Termin, z.B. 'Kontrolluntersuchung', 'Erstberatung'.",
                },
                "additional_remark": {
                    "type": "string",
                    "description": "Zusätzliche Anmerkungen oder Details zum Termin. Wenn keine vorhanden sind, ein leerer String oder 'N/A'.",
                },
                "date": {
                    "type": "string",
                    "description": "Das gewünschte Datum des Anrufs im Format YYYY-MM-DD.",
                },
                "time_range_start": {
                    "type": "string",
                    "description": "Die Startzeit des gewünschten Zeitfensters für den Anruf im Format HH:MM.",
                },
                "time_range_end": {
                    "type": "string",
                    "description": "Die Endzeit des gewünschten Zeitfensters für den Anruf im Format HH:MM.",
                },
            },
            "required": [
                "user_id",
                "doctor_id",
                "appointment_reason",
                "additional_remark",
                "date",
                "time_range_start",
                "time_range_end",
            ],
        },
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
    }
    return session


def send_prompt_to_claude(claude_session: dict, prompt: str) -> tuple[str, dict]:
    """
    Verarbeitet einen einzelnen Prompt innerhalb einer bestehenden Session.

    Note: Stateless API-Aufruf, daher wird die Historie in der Session gespeichert.
    """
    print(f"\n[SYSTEM] Sende Prompt an Claude: \n{prompt}\n")
    api_url, model_id, conversation_history, tools = (
        claude_session["api_url"],
        claude_session["model_id"],
        claude_session["conversation_history"],
        claude_session["tools"],
    )
    request_payload = {
        "prompt": prompt,
        "modelId": model_id,
        "messages": conversation_history,
        "tools": tools,
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(api_url, headers=headers, json=request_payload)
        response.raise_for_status()
        body_content = json.loads(response.json().get("body", "{}"))
        generated_text = body_content.get("generated_text", "")
        print(f"[CLAUDE RESPONSE] {generated_text}")
        tool_use_response = body_content.get("tool_use")
        claude_session["conversation_history"] = body_content.get(
            "conversation_history", conversation_history
        )

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


def pass_task_and_appointment_details_to_claude(
    task: dict, claude_session: dict
) -> dict:
    """
    Erstellt eine neue Claude-Session für eine bestimmte Aufgabe und startet sie.
    """
    # Den initialen System-Prompt verarbeiten, um die Rolle des Assistenten festzulegen
    system_prompt = "Du heißt FlexiTime und du bist ein Anruf-Agent für deinen Kunden. Das heißt, dass du stellvertretend für deinen Kunden Terminvereinbarungen beim Arzt vereinbarst. Wenn du einen Auftrag erstellt hast, "
    _, claude_session = send_prompt_to_claude(claude_session, system_prompt)

    # Einen spezifischen Prompt aus den Aufgabendetails erstellen und senden
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
    _, claude_session = send_prompt_to_claude(claude_session, task_prompt)
    return claude_session


# MAIN
if __name__ == "__main__":
    API_GATEWAY_URL = (
        "https://0621ja9smk.execute-api.us-west-2.amazonaws.com/dev/prompt"
    )
    CLAUDE_HAIKU_MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"

    print("Starte den automatischen Task-Processor...")
    print("Das Programm sucht alle 5 Sekunden nach neuen Aufgaben in der Datenbank.")
    print("Drücken Sie STRG+C, um das Programm zu beenden.")

    try:
        while True:
            # Nach neuen Aufgaben suchen und diese verarbeiten
            task_id, task_details_dict = check_for_open_tasks()
            if task_id:
                print(f"[SYSTEM] Neue Aufgabe mit ID {task_id} wurde gefunden.")
                session = create_claude_session(API_GATEWAY_URL, CLAUDE_HAIKU_MODEL_ID)
                session = pass_task_and_appointment_details_to_claude(
                    task_details_dict, session
                )
                while not "FINISHED_CALL" in ai_response:
                    doctor_office_respone = "PLACEHOLDER"  # TODO: Spech2Text Function
                    ai_response, session = send_prompt_to_claude(
                        session, doctor_office_respone
                    )
                    # TODO: Text2Speech Function
                # TODO: Update task in db to 'finished' or 'error'
                # TODO: Save call protocol to db
                # TODO: Save appointmeint date and time to db if successful

            # 5 Sekunden warten bis zur nächsten Überprüfung
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nProgramm wird beendet. Auf Wiedersehen!")
