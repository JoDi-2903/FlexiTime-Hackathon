import requests
import json
import psycopg2
import prompts

from psycopg2.extras import RealDictCursor

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


# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host="terminagent-db.cty0uqagcewj.us-west-2.rds.amazonaws.com",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="2WiIo5_g2-c+",
        # Note: Credentials should be stored securely in environment variables for a production system
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


# Globale Konstanten für Tools und deren Definitionen
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


# --- 2. Neue Session-Management-Funktionen ---

def create_claude_session(api_url: str, model_id: str) -> dict:
    """
    Initialisiert und konfiguriert eine neue Konversations-Session.

    Args:
        api_url: Die URL des API Gateways.
        model_id: Die ID des zu verwendenden Claude-Modells.

    Returns:
        Ein Dictionary, das den Zustand der Session repräsentiert.
    """
    print(f"Starte Claude Session (mit Tools) mit Modell: {model_id}")
    print(f"Sende Anfragen an: {api_url}\n")

    session = {
        "api_url": api_url,
        "model_id": model_id,
        "conversation_history": [],
        "tools": TOOL_DEFINITIONS,
        "available_tools": AVAILABLE_TOOLS
    }
    return session


def process_prompt_in_session(session: dict, user_prompt: str) -> tuple[str, dict]:
    """
    Verarbeitet einen einzelnen Prompt innerhalb einer bestehenden Session.

    Args:
        session: Das Session-Objekt von create_claude_session.
        user_prompt: Die neue Eingabe des Benutzers.

    Returns:
        Ein Tupel bestehend aus (Antwort_des_Modells, aktualisiertes_Session_Objekt).
    """
    print("[CLIENT] Sende Benutzer-Prompt an Claude...")

    # Lokale Kopien für die Verarbeitung in dieser Runde
    api_url = session['api_url']
    model_id = session['model_id']
    conversation_history = session['conversation_history']
    tools = session['tools']
    available_tools = session['available_tools']

    request_payload = {
        "prompt": user_prompt,
        "modelId": model_id,
        "messages": conversation_history,
        "tools": tools
    }
    headers = {"Content-Type": "application/json"}

    try:
        # --- Schritt 1: Initial-Anfrage an Claude ---
        response = requests.post(api_url, headers=headers, json=request_payload)
        response.raise_for_status()

        body_content = json.loads(response.json().get("body", "{}"))
        generated_text = body_content.get("generated_text", "")
        tool_use_response = body_content.get("tool_use")

        # Wichtig: Den Verlauf aus der Antwort übernehmen
        session['conversation_history'] = body_content.get("conversation_history", conversation_history)

        if tool_use_response:
            print(f"[CLIENT] Claude möchte ein Tool aufrufen: {tool_use_response['name']}")
            tool_name = tool_use_response['name']
            tool_input = tool_use_response['input']

            if tool_name in available_tools:
                tool_function = available_tools[tool_name]
                tool_output = tool_function(**tool_input)
                print(f"[TOOL-RESULT] Ausgabe des Tools {tool_name}: {tool_output}")

                # Füge den Tool-Output zum Verlauf hinzu
                session['conversation_history'].append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": tool_use_response['id'], "content": tool_output}]
                })

                # --- Schritt 2: Sende das Tool-Ergebnis zurück an Claude ---
                print("[CLIENT] Sende Tool-Ergebnis zurück an Claude für finale Antwort...")
                final_response_payload = {
                    "prompt": "hallo",  # Dummy-Prompt, da der Verlauf die Führung übernimmt
                    "modelId": model_id,
                    "messages": session['conversation_history'],
                    "tools": tools
                }

                final_response = requests.post(api_url, headers=headers, json=final_response_payload)
                final_response.raise_for_status()

                final_body_content = json.loads(final_response.json().get("body", "{}"))
                final_generated_text = final_body_content.get("generated_text", "Keine finale Antwort erhalten.")

                # Aktualisiere den Verlauf mit der finalen Antwort
                session['conversation_history'] = final_body_content.get("conversation_history",
                                                                         session['conversation_history'])

                return final_generated_text, session

            else:
                error_message = f"Unbekanntes Tool angefordert: {tool_name}"
                print(f"[CLIENT ERROR] {error_message}")
                # Optional: Claude über den Fehler informieren (hier einfach als finale Antwort zurückgegeben)
                return error_message, session

        elif generated_text:
            # Der Verlauf wurde bereits oben aktualisiert
            return generated_text, session

        else:
            return "Claude hat keine Antwort oder Tool-Aufruf geliefert.", session

    except requests.exceptions.RequestException as e:
        error_msg = f"[CLIENT ERROR] Fehler beim Senden der Anfrage: {e}"
        print(error_msg)
        return error_msg, session
    except json.JSONDecodeError as e:
        error_msg = f"[CLIENT ERROR] Fehler beim Parsen der JSON-Antwort. Details: {e}"
        print(error_msg)
        return error_msg, session
    except Exception as e:
        error_msg = f"[CLIENT ERROR] Ein unerwarteter Fehler ist aufgetreten: {e}"
        print(error_msg)
        return error_msg, session



if __name__ == "__main__":
    API_GATEWAY_URL = "https://0621ja9smk.execute-api.us-west-2.amazonaws.com/dev/prompt"
    # Verwenden Sie ein spezifisches, verfügbares Modell
    CLAUDE_HAIKU_MODEL_ID = "anthropic.claude-3-5-haiku-20241022-v1:0"  # oder ein anderes wie claude-3-5-sonnet

    # 1. Session einmalig erstellen
    claude_session = create_claude_session(API_GATEWAY_URL, CLAUDE_HAIKU_MODEL_ID)

    print("Verfügbare Tools: get_current_weather(location), schedule_call_task(...)")
    print("Stellen Sie Fragen wie: 'Wie ist das Wetter in Hamburg?' oder")
    print("'Buche einen Termin für user123 bei dr_meyer für eine Kontrolluntersuchung morgen zwischen 10 und 12 Uhr.'")
    print("Geben Sie 'exit', 'quit' oder 'beenden' ein, um die Session zu beenden.\n")

    # 2. Interaktive Schleife, die die Session wiederverwendet
    response_text, claude_session = process_prompt_in_session(claude_session, prompts.initialization)

    while True:
        user_input = input("Du: ")
        if user_input.lower() in ["exit", "quit", "beenden"]:
            print("Session beendet.")
            break

        # 3. Prompt in der bestehenden Session verarbeiten
        # Die claude_session wird bei jedem Durchlauf aktualisiert

        response_text, claude_session = process_prompt_in_session(claude_session, user_input)

        print(f"Claude: {response_text}\n")
