# multimodal.py

from groq import Groq as GroqClient

from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
STT = os.getenv("STT")

def stt(audio_file) -> str:
    """Converts speech from an audio file into text."""

	# Initialize the Groq client
    client = GroqClient(api_key=API_KEY)
    
    # Create a transcription of the audio file
    transcription = client.audio.transcriptions.create(
        file=audio_file,
        model=STT,
        response_format="text",
        temperature=0.1
    )

    return transcription.strip()

# TODO: def tts(message: str):