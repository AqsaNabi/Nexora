
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# Locate the saved Google OAuth token
BASE_DIR = Path(__file__).resolve().parents[1]
TOKEN_FILE = BASE_DIR / "authen" / "token.json"


def get_forms_service():

    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            "Google authentication token not found. "
            "Please authenticate with Google first."
        )

    # Load saved credentials
    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        scopes=["https://www.googleapis.com/auth/forms.body"]
    )

    # Refresh expired access token if necessary
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        # Save refreshed credentials
        with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(credentials.to_json())

    # Connect to Google Forms API
    service = build(
        "forms",
        "v1",
        credentials=credentials
    )

    return service

def create_google_form(title):

    service = get_forms_service()

    form_body = {
        "info": {
            "title": title
        }
    }

    response = service.forms().create(
        body=form_body
    ).execute()

    return {
        "form_id": response.get("formId"),
        "title": response.get("info", {}).get("title"),
        "form_url": response.get("responderUri")
    }
