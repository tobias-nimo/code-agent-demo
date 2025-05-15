# multimodal.py

from groq import Groq as GroqClient
from dotenv import load_dotenv
import os

load_dotenv()
STT_MODEL = os.getenv("STT_MODEL")
API_KEY = os.getenv("API_KEY")

def stt(audio_file) -> str:
    """
    Converts speech from an audio file into text.
    Args:
        path_to_audio (str): The path to the audio file to be transcribed.
    Returns:
        str: The transcribed text content of the audio file.
    """
    
    # TODO: Validate audio file

	# Initialize the Groq client
    client = GroqClient(api_key=API_KEY)
    
    # Create a transcription of the audio file
    transcription = client.audio.transcriptions.create(
        file=audio_file,
        model=STT_MODEL,
        response_format="text", # Returns plain text instead of JSON
        language="en",
        temperature=0.1
    )

    return transcription.strip()
