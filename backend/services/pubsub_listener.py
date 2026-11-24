import json
import os
import threading
import time

from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError

from backend.services.applicant_response_service import (
    process_form_responses
)

PROJECT_ID = "manifest-life-513710-d4"
SUBSCRIPTION_ID = "nexora-form-responses-sub"

SUBSCRIPTION_PATH = (
    f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_ID}"
)

subscriber = None

_listener_thread = None
_stop_event = threading.Event()


def _get_subscriber():
    global subscriber

    if subscriber is None:
        # ✅ FIXED: Explicitly load the credentials from the Render secret file
        # or local path.
        creds_path = os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS", 
            "backend/authen/pubsub_credentials.json"
        )
        
        if os.path.exists(creds_path):
            credentials = service_account.Credentials.from_service_account_file(creds_path)
            subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        else:
            # Fallback to default ADC if file isn't found
            subscriber = pubsub_v1.SubscriberClient()

    return subscriber


def _process_message(received_message):
    message = received_message.message

    try:
        attributes = dict(message.attributes)

        form_id = attributes.get("formId")
        event_type = attributes.get("eventType")

        if not form_id:
            raise ValueError(
                f"Notification does not contain formId: {attributes}"
            )

        if event_type != "RESPONSES":
            print(f"Ignoring notification event: {event_type}")
            return True

        print(f"Google Forms response notification received: {form_id}")

        saved_count = process_form_responses(form_id)

        print(
            f"Processing completed. New applicants saved: {saved_count}"
        )

        return True

    except Exception as error:
        print(f"Error processing notification: {error}")
        print(f"Message attributes: {dict(message.attributes)}")
        return True
    

def _listen():
    global subscriber

    print("Nexora Pub/Sub listener started.")

    try:
        client = _get_subscriber()
    except DefaultCredentialsError:
        print(
            "Pub/Sub listener not started: "
            "Google Cloud credentials are not configured."
        )
        return 

    while not _stop_event.is_set():
        try:
            response = client.pull(
                request={
                    "subscription": SUBSCRIPTION_PATH,
                    "max_messages": 10
                },
                retry=None,
                timeout=60
            )

            for received_message in response.received_messages:
                if _stop_event.is_set():
                    break

                success = _process_message(received_message)

                if success:
                    client.acknowledge(
                        request={
                            "subscription": SUBSCRIPTION_PATH,
                            "ack_ids": [received_message.ack_id]
                        }
                    )
                else:
                    client.modify_ack_deadline(
                        request={
                            "subscription": SUBSCRIPTION_PATH,
                            "ack_ids": [received_message.ack_id],
                            "ack_deadline_seconds": 0
                        }
                    )

        except Exception as error:
            if not _stop_event.is_set():
                print(f"Pub/Sub listener error: {error}")
                time.sleep(5)

    print("Nexora Pub/Sub listener stopped.")


def start_pubsub_listener():
    global _listener_thread

    if _listener_thread and _listener_thread.is_alive():
        print("Pub/Sub listener is already running.")
        return

    _stop_event.clear()

    _listener_thread = threading.Thread(
        target=_listen,
        daemon=True
    )

    _listener_thread.start()


def stop_pubsub_listener():
    global subscriber

    _stop_event.set()

    if _listener_thread and _listener_thread.is_alive():
        _listener_thread.join(timeout=5)

    if subscriber is not None:
        subscriber.close()
        subscriber = None
