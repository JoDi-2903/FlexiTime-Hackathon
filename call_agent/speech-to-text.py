import asyncio
import json
import os
import time

import boto3
import pyaudio
import websockets
from botocore.exceptions import ClientError


async def speech_to_text(language_code: str = "de-DE", break_delay: float = 2.0) -> str:
    """
    Captures audio from microphone and uses AWS Transcribe streaming to convert speech to text.
    Stops listening after detecting a 2-second pause in speech.

    :param language_code: Language code for transcription
    :param break_delay: Time in seconds to wait before stopping transcription after a pause
    :return: Transcribed text as a string
    """
    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Audio parameters
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024

    # AWS Transcribe client
    try:
        transcribe_client = boto3.client(
            "transcribe",
            region_name="us-west-2",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
    except ClientError as e:
        print(f"AWS Error: {e}")
        return ""

    # Get streaming endpoint
    try:
        response = transcribe_client.start_stream_transcription(
            LanguageCode=language_code, MediaSampleRateHertz=RATE, MediaEncoding="pcm"
        )
        streaming_endpoint = response["StreamTranscriptionWebsocketURI"]
    except ClientError as e:
        print(f"AWS Error: {e}")
        return ""

    # Open audio stream
    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    print("Listening... (speak now)")

    # Initialize variables
    transcription = ""
    last_speech_time = time.time()
    is_speaking = False

    async with websockets.connect(streaming_endpoint) as websocket:
        # Start the audio stream
        async def send_audio():
            nonlocal last_speech_time, is_speaking

            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)

                # Simple voice activity detection based on audio level
                audio_level = max(
                    abs(
                        int.from_bytes(data[i : i + 2], byteorder="little", signed=True)
                    )
                    for i in range(0, len(data), 2)
                )

                if audio_level > 500:  # Threshold for voice detection
                    if not is_speaking:
                        is_speaking = True
                    last_speech_time = time.time()

                # Check for pause
                if is_speaking and time.time() - last_speech_time > break_delay:
                    # pause detected
                    break

                # Send audio chunk to AWS
                await websocket.send(data)
                await asyncio.sleep(0.01)

            # Close the stream when done
            await websocket.close()

        # Receive transcription results
        async def receive_transcription():
            nonlocal transcription

            while True:
                try:
                    result = await websocket.recv()
                    result = json.loads(result)

                    if "Transcript" in result and "Results" in result["Transcript"]:
                        for result_item in result["Transcript"]["Results"]:
                            if not result_item.get("IsPartial", True):
                                if (
                                    "Alternatives" in result_item
                                    and result_item["Alternatives"]
                                ):
                                    transcription = " ".join(
                                        [
                                            transcription,
                                            result_item["Alternatives"][0][
                                                "Transcript"
                                            ],
                                        ]
                                    ).strip()
                                    print(f"Transcript: {transcription}")
                except websockets.exceptions.ConnectionClosed:
                    break

        # Run tasks concurrently
        await asyncio.gather(send_audio(), receive_transcription())

    # Clean up
    stream.stop_stream()
    stream.close()
    audio.terminate()

    print(f"Final transcript: {transcription}")
    return transcription


# if __name__ == "__main__":
#     import asyncio
#     result = asyncio.run(speech_to_text())
#     print(f"You said: {result}")
