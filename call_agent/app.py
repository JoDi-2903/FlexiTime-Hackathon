import json
import time
from typing import Optional

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


def check_for_open_tasks() -> list[Optional[str], Optional[dict]]:
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
            return [tasks[0]["task_id"], tasks[0]]  # Return the task ID and the task
        else:
            return [None, None]

    except psycopg2.Error as e:
        print(f"[DB ERROR] Datenbankfehler: {e}")
        return [None, None]
    except Exception as e:
        print(f"[SYSTEM ERROR] Ein unerwarteter Fehler ist aufgetreten: {e}")
        return [None, None]


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
    # Einen spezifischen Prompt aus den Aufgabendetails erstellen und senden
    task_prompt = (
        f"[Details zum Terminbuchungsauftrag aus der Datenbank]\n"
        f"- Benutzer-ID: {task['user_id']}\n"
        f"- Arzt-ID: {task['user_id']}\n"
        f"- Auftrags-ID: {task['task_id']}\n"
        f"- Grund des Termins: {task['appointment_reason']}\n"
        f"- Gewünschtes Datum: {task.get('appointment_date', 'N/A')}\n"
        f"- Gewünschtes Zeitfenster: {task.get('time_range_start', 'N/A')} - {task.get('time_range_end', 'N/A')}\n\n"
        f" "
    )

    # Den initialen System-Prompt verarbeiten, um die Rolle des Assistenten festzulegen
    system_prompt = "Du heißt FlexiTime bist ein Anruf-Agent, der automatisiert Terminbuchungen bei Arztpraxen für Kunden vornehmen kann, die nicht selbst telefonieren können oder wollen (z.B. zeitliche Gründe, körperliche EInschränkungen, usw.). Das heißt, dass du stellvertretend wie ein Assistent für die Kunden Terminvereinbarungen beim Arzt vereinbarst. Dafür erhälst du Infomationen aus der Datenbank bereitgestellt, die alle relevanten Informationen über den Kunden, sein Anliegen, den Arzt bei dem der Termin vereinbart werden soll sowie die Terminspanne die dem Kunden passt enthält. Deine Aufgabe ist es, diese Informationen zu nutzen, um den Anruf beim Arzt zu tätigen und den Termin zu vereinbaren. Du wirst dabei von einem KI-Modell unterstützt, das dir hilft, die richtigen Fragen zu stellen und die Informationen zu verarbeiten. Deine Antworten sollten klar und präzise sein, damit der Arzt oder das Praxisteam die Informationen leicht verstehen kann und auch nicht zu lang werden. Es soll wie ein natürliches Gespräch zwischen zwei Personen sein. Wenn alles geklärt ist, beendest du das Gespräch indem du dich verabschiedest, dann 'FINISHED_CALL' ausgibst und dann im json-Format das Gesprächsergebnis. Das JSOn soll dabei das Format task_status: str mit den Optionen 'successful' und 'unsuccessful' enthalten, appointment_date: str mit dem Datum des Termins im Format YYYY-MM-DD und appointment_time: str mit der Uhrzeit des Termins im Format HH:MM. Wenn du keine Informationen hast, die du ausgeben kannst, dann gib 'N/A' aus. Es ist wichtig dass du dich an diese Struktur hältst, damit die Informationen korrekt verarbeitet werden können. Wenn eine Terminvereinbarung nicht möglich ist, z.B. weil die Praxis für den vom Nutzer angegebenen Zeitraum schon komplett ausgebucht ist oder aus diversen anderen Gründen, gib bitte den task_status 'unsuccessful' im JSON an und erfinde keinen Termin. Bitte reagiere dynamisch auf den Gesprächsverlauf mit dem Mitarbeiter oder der Mitarbeiterin aus der Arztpraxis aber verliere dein Ziel dabei nicht aus den Augben. Das Gespräch sollte nicht abdriften. Alle weiteren Prompts sind die Telefonantworten des Gesprächpartners aus der Arzpraxis. Es wird der gesamte bisherige Gesprächsverlauf mit jedem neuen Prompt mitgegeben, sodass der Kontext für dich erhalten bleibt. Kommuniziere bitte auf Deutsch, sei freundlich, höflich aber nicht zu formell und steif."
    _, claude_session = send_prompt_to_claude(claude_session, task_prompt+system_prompt)
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
            open_task_result = check_for_open_tasks()
            task_id, task_details_dict = open_task_result
            if task_id:
                print(f"[SYSTEM] Neue Aufgabe mit ID {task_id} wurde gefunden.")
                session = create_claude_session(API_GATEWAY_URL, CLAUDE_HAIKU_MODEL_ID)
                session = pass_task_and_appointment_details_to_claude(
                    task_details_dict, session
                )
                while not "FINISHED_CALL" in ai_response:
                    # Trap for conversation between AI and doctor office
                    doctor_office_respone = input("> ")  # TODO: Spech2Text Function
                    ai_response, session = send_prompt_to_claude(
                        session, doctor_office_respone
                    )
                    # TODO: Text2Speech Function
                # Split the AI response at "FINISHED_CALL"
                if "FINISHED_CALL" in ai_response:
                    conversation_part, result_part = ai_response.split("FINISHED_CALL", 1)
                    print(f"[SYSTEM] Call completed. Processing results...")
                    print(f"[SYSTEM] Conversation: {conversation_part.strip()}")
                    print(f"[SYSTEM] Result data: {result_part.strip()}")
                    
                    try:
                        # Try to parse the JSON data from the result part
                        result_json = json.loads(result_part.strip())
                        print(f"[SYSTEM] Parsed result: {result_json}")
                        # This JSON contains task_status, appointment_date, appointment_time
                    except json.JSONDecodeError as e:
                        print(f"[SYSTEM ERROR] Could not parse result JSON: {e}")

                # TODO: Update task in db to 'finished' or 'error'
                # TODO: Save call protocol to db
                # TODO: Save appointmeint date and time to db if successful

            # 5 Sekunden warten bis zur nächsten Überprüfung
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nProgramm wird beendet. Auf Wiedersehen!")
