import json
import uuid

from pathlib import Path


POST_GEN_FOLDER = Path(__file__).resolve().parent

OUTPUT_FOLDER = POST_GEN_FOLDER / "generated_outputs"


def create_approved_payload(
    session_id,
    job_post,
    application_form
):

    try:
        safe_session_id = str(uuid.UUID(str(session_id)))

    except (ValueError, TypeError):
        raise ValueError("Invalid session ID.")

    approved_payload = {
        "job_post": job_post,
        "application_form": application_form
    }

    OUTPUT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = (
        OUTPUT_FOLDER /
        f"approved_{safe_session_id}.json"
    )

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
        safe_session_id = str(uuid.UUID(str(session_id)))

    except (ValueError, TypeError):
        raise ValueError("Invalid session ID.")

    file_path = (
        OUTPUT_FOLDER /
        f"approved_{safe_session_id}.json"
    )

    if file_path.exists():
        file_path.unlink()