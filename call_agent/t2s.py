import os
import boto3
from botocore.exceptions import ClientError
from pydub import AudioSegment
from pydub.playback import play
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


def text_to_speech(text, output_file="voice_files/speech.mp3", voice_id="Vicki"):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        polly_client = boto3.client(
            "polly",
            region_name="us-west-2",
            aws_access_key_id="AKIATMOA6AAEPC3EUEF6",
            aws_secret_access_key="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",
        )

        response = polly_client.synthesize_speech(
            Text=text, OutputFormat="mp3", VoiceId=voice_id, Engine='neural',
        )

        if "AudioStream" in response:
            # Save the audio file
            with open(output_file, "wb") as file:
                file.write(response["AudioStream"].read())
            print(f"Audio successfully saved as {output_file}")

            # Play the audio and block until complete
            audio = AudioSegment.from_mp3(output_file)
            print("Playing audio...")
            play(audio)
            print("Audio playback finished")
        else:
            print("Error: No AudioStream received")

    except ClientError as e:
        print(f"AWS Error: {e}")
    except Exception as e:
        print(f"General Error: {e}")
