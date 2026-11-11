
import os
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

POST_GEN_FOLDER = Path(__file__).resolve().parent

ENV_FILE = POST_GEN_FOLDER / ".env"

load_dotenv(ENV_FILE, override=True)


# ============================================================
# AWS BEDROCK CONFIGURATION
# ============================================================

BEDROCK_API_KEY = os.getenv("BEDROCK_API_KEY")

BEDROCK_BASE_URL = os.getenv(
    "BEDROCK_BASE_URL",
    "https://bedrock-mantle.us-east-1.api.aws/v1"
)

BEDROCK_MODEL = os.getenv(
    "BEDROCK_MODEL",
    "openai.gpt-oss-20b"
)


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not BEDROCK_API_KEY:

    raise ValueError(
        f"BEDROCK_API_KEY is missing. "
        f"Please check your environment file: {ENV_FILE}"
    )

if not BEDROCK_BASE_URL:

    raise ValueError(
        "BEDROCK_BASE_URL is missing."
    )

if not BEDROCK_MODEL:

    raise ValueError(
        "BEDROCK_MODEL is missing."
    )
