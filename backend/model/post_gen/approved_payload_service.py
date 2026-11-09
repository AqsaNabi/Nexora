
import json
import uuid
from pathlib import Path


# This file is inside backend/model/post_gen
POST_GEN_FOLDER = Path(__file__).resolve().parent

# Final approved JSON files are stored here
OUTPUT_FOLDER = POST_GEN_FOLDER / "generated_outputs"


def create_approved_payload(
    session_id,
    job_post,
    application_form
):
    try:
        safe_session_id = str(uuid.UUID(session_id))
    except ValueError:
        raise ValueError("Invalid session ID.")

    # Combine both approved drafts into one object
    approved_payload = {
        "job_post": job_post,
        "application_form": application_form
    }

    # Create generated_outputs if it doesn't exist
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    file_path = (
        OUTPUT_FOLDER /
        f"approved_{safe_session_id}.json"
    )

    # Write to a temporary file before replacing the final file
    temporary_path = file_path.with_suffix(".tmp")

    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(
            approved_payload,
            file,
            indent=4,
            ensure_ascii=False
        )

    temporary_path.replace(file_path)

    return approved_payload, str(file_path)


def delete_approved_payload(session_id):
    try:
        safe_session_id = str(uuid.UUID(session_id))
    except ValueError:
        raise ValueError("Invalid session ID.")

    file_path = (
        OUTPUT_FOLDER /
        f"approved_{safe_session_id}.json"
    )

    if file_path.exists():
        file_path.unlink()
