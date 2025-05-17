# base_tools.py

from groq import Groq as GroqClient

from dotenv import load_dotenv
import os

from pathlib import Path
import mimetypes
import base64

load_dotenv()
GROK_API_KEY = os.getenv("GROK_API_KEY")
STT = os.getenv("STT")
VLM = os.getenv("VLM")


def transcribe_audio(path_to_audio: str) -> str:
    """
    Converts speech from an audio file into text.
    Args:
        path_to_audio (str): The path to the audio file to be transcribed.
    Returns:
        str: The transcribed text content of the audio.
    """
    
    # Validate path
    path = Path(path_to_audio).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"No such audio file: {path}")

    # Initialize the Groq client
    client = GroqClient(api_key=GROK_API_KEY) 
    
    # Open the audio file
    with open(path_to_audio, "rb") as audio_file:
        # Create a transcription of the audio file
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=STT,
            response_format="text",
            temperature=0.1
        )

    return transcription.strip()

def analyze_image(path_to_image: str, question: str) -> str:
    """
    Analyzes an image and generates a response to a given question based on the image's content.
    
    Args:
        path_to_image (str): The path to the image file to be analyzed.
        question (str): The question to be answered, based on the contents of the image.
        
    Returns:
        str: The response from a VLM, typically a textual analysis or description based on the image.
    """

    # Validate path
    path = Path(path_to_image).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"No such image file: {path}")

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    # Get the MIME type (e.g., image/png, image/jpeg)
    mime_type, _ = mimetypes.guess_type(path_to_image)
    if mime_type is None:
        raise ValueError("Unsupported file type. Please provide a valid image.")

    base64_image = encode_image(path_to_image)

    # Initialize the Groq client
    client = GroqClient(api_key=GROK_API_KEY)
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        model=VLM,
    )
    
    analysis = chat_completion.choices[0].message.content
    return analysis.strip()