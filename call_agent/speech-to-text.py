import whisper
import pyaudio
import wave
import os
import time

# --- Konfiguration ---
MODEL_GROESSE = "small"
SPRACHE = "de"
TEMP_DATEINAME = "temp_aufnahme.wav"


def speech_to_text(aufnahmedauer_sekunden: int):
    """Nimmt Audio vom Mikrofon auf (mit der stabilen Callback-Methode) und transkribiert es."""

    audio = pyaudio.PyAudio()

    # Eine Liste, in der die Callback-Funktion die Audiodaten ablegt
    frames = []

    # --- NEUE CALLBACK-FUNKTION ---
    # Diese Funktion wird von PyAudio im Hintergrund aufgerufen, sobald neue Audiodaten da sind.
    def audio_callback(in_data, frame_count, time_info, status):
        frames.append(in_data)
        return in_data, pyaudio.paContinue  # Signalisiert, dass die Aufnahme weitergehen soll

    # --- GEÄNDERTER STREAM-AUFRUF ---
    # Wir übergeben unsere Callback-Funktion hier direkt an den Stream.
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=1024,
                        stream_callback=audio_callback)  # Hier ist die Magie!

    print(f"▶️  Aufnahme läuft für {aufnahmedauer_sekunden} Sekunden...")

    # Der Stream läuft jetzt im Hintergrund. Wir warten einfach die gewünschte Zeit.
    # Die alte for-Schleife wird nicht mehr benötigt.
    time.sleep(aufnahmedauer_sekunden)

    # Aufnahme stoppen
    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("⏹️  Aufnahme beendet.")

    # Der Rest des Codes bleibt unverändert
    # ------------------------------------
    with wave.open(TEMP_DATEINAME, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    print(f"Aufnahme temporär gespeichert als '{TEMP_DATEINAME}'.")

    try:
        print("Lade Whisper-Modell...")
        model = whisper.load_model(MODEL_GROESSE)

        print("Transkription wird durchgeführt...")
        result = model.transcribe(TEMP_DATEINAME, language=SPRACHE)

        print("\n--- TRANSKRIPTION ---")
        print(result["text"].strip() if result["text"] else "[Keine Sprache erkannt]")
        print("-----------------------")

    finally:
        if os.path.exists(TEMP_DATEINAME):
            os.remove(TEMP_DATEINAME)
            print(f"Temporäre Datei '{TEMP_DATEINAME}' wurde gelöscht.")


if __name__ == "__main__":
    speech_to_text(5)