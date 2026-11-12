
import os

from backend.services.google_form_service import get_forms_service


PROJECT_ID = "manifest-life-513710-d4"

TOPIC_NAME = (
    f"projects/{PROJECT_ID}/topics/nexora-form-responses"
)


def create_response_watch(form_id: str):
    service = get_forms_service()

    # Avoid creating duplicate watches.
    existing = service.forms().watches().list(
        formId=form_id
    ).execute().get("watches", [])

    for watch in existing:
        target = watch.get("target", {}).get("topic", {})

        if (
            watch.get("eventType") == "RESPONSES"
            and target.get("topicName") == TOPIC_NAME
            and watch.get("state") == "ACTIVE"
        ):
            print("An active response watch already exists.")
            return watch

    request_body = {
        "watch": {
            "target": {
                "topic": {
                    "topicName": TOPIC_NAME
                }
            },
            "eventType": "RESPONSES"
        }
    }

    result = service.forms().watches().create(
        formId=form_id,
        body=request_body
    ).execute()

    print("Google Forms response watch created!")
    return result
