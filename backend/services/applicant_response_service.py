
import json
from datetime import datetime

from backend.database.recruitment_db import get_recruitment_connection
from backend.services.google_form_service import get_forms_service


def _answer_value(answer):
    """Extract answer values from a Google Forms response."""
    text_answers = answer.get("textAnswers", {}).get("answers", [])

    values = [item.get("value", "") for item in text_answers]

    if not values:
        return None

    return values[0] if len(values) == 1 else values


def _get_form_metadata(form_id):
    connection = get_recruitment_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT post_id, question_mapping
                FROM recruitment_metadata
                WHERE form_id = %s
                """,
                (form_id,)
            )

            result = cursor.fetchone()

            if not result:
                raise ValueError(
                    f"No recruitment post found for form {form_id}"
                )

            post_id, question_mapping = result

            if isinstance(question_mapping, str):
                question_mapping = json.loads(question_mapping)

            return post_id, question_mapping or {}

    finally:
        connection.close()


def _save_applicant(form_id, response, post_id, question_mapping):
    response_id = response.get("responseId")

    if not response_id:
        raise ValueError("Google Forms response has no responseId")

    answers = response.get("answers", {})

    applicant = {
        "full_name": None,
        "email": None,
        "phone": None
    }

    additional_data = {}

    for question_id, answer in answers.items():
        field_name = question_mapping.get(question_id)

        if not field_name:
            continue

        value = _answer_value(answer)

        if field_name in applicant:
            applicant[field_name] = value
        elif field_name != "resume_file":
            additional_data[field_name] = value

    if not applicant["full_name"] or not applicant["email"]:
        raise ValueError(
            f"Required applicant details missing in response {response_id}. "
            "Check the question_mapping."
        )

    connection = get_recruitment_connection()

    try:
        with connection.cursor() as cursor:

            # Prevent duplicate applications.
            cursor.execute(
                """
                INSERT INTO recruitment_processed_responses
                    (form_id, response_id)
                VALUES (%s, %s)
                ON CONFLICT (form_id, response_id) DO NOTHING
                RETURNING response_id
                """,
                (form_id, response_id)
            )

            inserted = cursor.fetchone()

            if not inserted:
                connection.rollback()
                print(f"Duplicate response ignored: {response_id}")
                return False

            submitted_at = response.get("lastSubmittedTime")

            if submitted_at:
                submitted_at = datetime.fromisoformat(
                    submitted_at.replace("Z", "+00:00")
                )

            cursor.execute(
                """
                INSERT INTO recruitment_data (
                    post_id,
                    full_name,
                    email,
                    phone,
                    additional_data,
                    submitted_at
                )
                VALUES (%s, %s, %s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
                """,
                (
                    post_id,
                    applicant["full_name"],
                    applicant["email"],
                    applicant["phone"],
                    json.dumps(additional_data),
                    submitted_at
                )
            )

        connection.commit()

        print(
            f"Applicant saved: {applicant['email']} "
            f"for {post_id}"
        )

        return True

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def process_form_responses(form_id):
    """Fetch and process all responses for a recruitment form."""

    post_id, question_mapping = _get_form_metadata(form_id)

    service = get_forms_service()

    page_token = None
    saved_count = 0

    while True:
        request_args = {
            "formId": form_id,
            "pageSize": 500
        }

        if page_token:
            request_args["pageToken"] = page_token

        result = service.forms().responses().list(
            **request_args
        ).execute()

        for response in result.get("responses", []):
            if _save_applicant(
                form_id,
                response,
                post_id,
                question_mapping
            ):
                saved_count += 1

        page_token = result.get("nextPageToken")

        if not page_token:
            break

    print(
        f"Response processing completed for {post_id}. "
        f"New applicants saved: {saved_count}"
    )

    return saved_count
