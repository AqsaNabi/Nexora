
import os
from pathlib import Path
from dotenv import load_dotenv

# Locate .env inside the post_gen folder
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

OLLAMA_API_KEY ="c63a8923d89e453d9d0184e974cad9d4.2MLgKToqBZ8dyiI2gKFMpyKj"

OLLAMA_API_URL = "https://ollama.com/v1"
    

OLLAMA_MODEL ="gemma4:31b-cloud"

if not OLLAMA_API_KEY:
    raise ValueError("OLLAMA_API_KEY is missing from post_gen/.env")
