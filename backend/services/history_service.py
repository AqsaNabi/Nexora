
import json
import uuid

from datetime import datetime, timezone
from pathlib import Path


# -----------------------------------------
# FOLDER PATHS
# -----------------------------------------

BACKEND_FOLDER = Path(__file__).resolve().parents[1]

POST_GEN_FOLDER = BACKEND_FOLDER / "model" / "post_gen"

OUTPUT_FOLDER = POST_GEN_FOLDER / "generated_outputs"

HISTORY_FOLDER = OUTPUT_FOLDER / "chat_history"


# -----------------------------------------
# VALIDATE SESSION ID
# -----------------------------------------

def validate_session_id(session_id):

    try:
        return str(uuid.UUID(str(session_id)))

    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid session ID.")


# -----------------------------------------
# GET HISTORY FILE PATH
# -----------------------------------------

def get_history_path(session_id):

    safe_id = validate_session_id(session_id)

    return HISTORY_FOLDER / f"{safe_id}.json"


# -----------------------------------------
# SAVE CONVERSATION
# -----------------------------------------

def save_chat_history(session_id, chat_service):

    safe_id = validate_session_id(session_id)

    HISTORY_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    history_data = {
        "session_id": safe_id,

        "conversation": chat_service.conversation,

        "chat_messages": chat_service.chat_messages,

        "current_job_post": chat_service.current_job_post,

        "current_application_form": chat_service.current_application_form,

        "job_post_approved": chat_service.job_post_approved,

        "application_form_approved": chat_service.application_form_approved,

        "approved_payload": chat_service.approved_payload,

        "approved_json_path": chat_service.approved_json_path,

        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    file_path = get_history_path(safe_id)

    # Write to temporary file first to avoid incomplete JSON files
    temporary_path = file_path.with_suffix(".tmp")

    with open(
        temporary_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    # Replace the old history file
    temporary_path.replace(file_path)

    return str(file_path)


# -----------------------------------------
# LOAD PREVIOUS CONVERSATION
# -----------------------------------------

def load_chat_history(session_id):

    file_path = get_history_path(session_id)

    if not file_path.exists():
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# -----------------------------------------
# LIST ALL SAVED CONVERSATIONS
# -----------------------------------------

def list_chat_histories():

    HISTORY_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    histories = []

    for file_path in HISTORY_FOLDER.glob("*.json"):

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            job_post = data.get("current_job_post") or {}

            chat_messages = data.get("chat_messages") or []

            # Use job title as conversation title
            title = job_post.get("job_title", "")

            # If job title is unavailable, use the first HR message
            if not title:

                first_user_message = next(
                    (
                        item.get("content", "")
                        for item in chat_messages
                        if item.get("role") == "user"
                    ),
                    "New conversation"
                )

                title = str(first_user_message)

            histories.append({

                "session_id": data.get(
                    "session_id",
                    file_path.stem
                ),

                "title": title[:60],

                "updated_at": data.get("updated_at", ""),

                "message_count": len(chat_messages)

            })

        except (
            json.JSONDecodeError,
            OSError,
            AttributeError
        ):

            continue

    # Latest conversation appears first
    histories.sort(
        key=lambda item: item["updated_at"],
        reverse=True
    )

    return histories


# -----------------------------------------
# DELETE CONVERSATION
# -----------------------------------------

def delete_chat_history(session_id):

    file_path = get_history_path(session_id)

    if file_path.exists():

        file_path.unlink()

