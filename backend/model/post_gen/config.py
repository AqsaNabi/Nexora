import os
from pathlib import Path
from dotenv import load_dotenv


# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Locate the root .env file
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables
load_dotenv(dotenv_path=ENV_FILE, override=False)


# Bedrock configuration
BEDROCK_API_KEY = os.getenv("BEDROCK_API_KEY")
BEDROCK_BASE_URL = os.getenv("BEDROCK_BASE_URL")
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL")


# Validate configuration
if not BEDROCK_API_KEY:
    raise ValueError("BEDROCK_API_KEY is missing from the project root .env")

if not BEDROCK_BASE_URL:
    raise ValueError("BEDROCK_BASE_URL is missing from the project root .env")

if not BEDROCK_MODEL:
    raise ValueError("BEDROCK_MODEL is missing from the project root .env")