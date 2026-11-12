
import json
import threading
import time

from google.cloud import pubsub_v1

from backend.services.applicant_response_service import (
    process_form_responses
)

PROJECT_ID = "manifest-life-513710-d4"
SUBSCRIPTION_ID = "nexora-form-responses-sub"

SUBSCRIPTION_PATH = (
    f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_ID}"
)

subscriber = pubsub_v1.SubscriberClient()

_listener_thread = None
_stop_event = threading.Event()


def _process_message(received_message):
    message = received_message.message

    try:
        # Google Forms sends notification details as Pub/Sub attributes.
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
        return False


def _listen():
    print("Nexora Pub/Sub listener started.")

    while not _stop_event.is_set():
        try:
            response = subscriber.pull(
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
                    subscriber.acknowledge(
                        request={
                            "subscription": SUBSCRIPTION_PATH,
                            "ack_ids": [received_message.ack_id]
                        }
                    )
                else:
                    # Release the message for redelivery.
                    subscriber.modify_ack_deadline(
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
    _stop_event.set()

    if _listener_thread and _listener_thread.is_alive():
        _listener_thread.join(timeout=5)

    subscriber.close()
