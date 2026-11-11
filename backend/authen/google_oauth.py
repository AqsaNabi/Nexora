
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

# Project root: Nexora/
BASE_DIR = Path(__file__).resolve().parents[2]

# Load environment variables from Nexora/.env
load_dotenv(BASE_DIR / ".env")

TOKEN_FILE = Path(__file__).resolve().parent / "token.json"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file"
]


def get_client_config():
    if not all([CLIENT_ID, CLIENT_SECRET, PROJECT_ID, REDIRECT_URI]):
        raise ValueError(
            "Google OAuth environment variables are missing. "
            "Please check your .env file."
        )

    return {
        "web": {
            "client_id": CLIENT_ID,
            "project_id": PROJECT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }


def create_oauth_flow():
    return Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        autogenerate_code_verifier=True
    )


def get_authorization_url():
    flow = create_oauth_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    return authorization_url, state, flow
def exchange_code_for_token(code, flow):
    flow.fetch_token(code=code)

    credentials = flow.credentials

    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }

    with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
        json.dump(token_data, token_file, indent=4)

    return credentials
