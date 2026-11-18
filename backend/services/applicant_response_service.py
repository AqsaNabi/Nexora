
import json
from datetime import datetime

from backend.database.recruitment_db import get_recruitment_connection

from backend.services.google_form_service import get_forms_service

from backend.repository.recruitment_repository import (
    get_job_description
)

from backend.services.google_drive_service import (
    download_resume_from_drive
)

from backend.services.resume_parser_service import (
    extract_resume_text
)

from backend.services.candidate_evaluation_service import (
    evaluate_candidate
)


def _answer_value(answer):
    """Extract answer values from a Google Forms response."""

    text_answers = answer.get(
        "textAnswers", {}
    ).get("answers", [])

    values = [
        item.get("value", "")
        for item in text_answers
    ]

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
                WHERE form_id = %s;
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


def _save_applicant(
    form_id,
    response,
    post_id,
    question_mapping
):

    response_id = response.get("responseId")

    if not response_id:
        raise ValueError(
            "Google Forms response has no responseId"
        )

    answers = response.get("answers", {})

    applicant = {
        "full_name": None,
        "email": None,
        "phone": None
    }

    resume_link = None
    additional_data = {}

    # Extract applicant information.
    for question_id, answer in answers.items():

        field_name = question_mapping.get(question_id)

        if not field_name:
            continue

        value = _answer_value(answer)

        if field_name in applicant:
            applicant[field_name] = value

        elif field_name == "resume_link":
            resume_link = value

        elif field_name != "resume_file":
            additional_data[field_name] = value

    if not applicant["full_name"] or not applicant["email"]:
        raise ValueError(
            f"Required applicant details missing: {response_id}"
        )

    if not resume_link:
        raise ValueError(
            f"Resume link missing for response {response_id}"
        )

    # Get the job description.
    job_description = get_job_description(post_id)

    if not job_description:
        raise ValueError(
            f"Job description not found for post {post_id}"
        )

    # Download resume from Google Drive.
    resume_content, resume_filename, resume_content_type = (
        download_resume_from_drive(resume_link)
    )

    if not resume_content:
        raise ValueError(
            f"Could not download resume for {applicant['email']}"
        )

    # Extract resume text.
    resume_text = extract_resume_text(
        resume_content,
        resume_filename,
        resume_content_type
    )

    if not resume_text:
        raise ValueError(
            f"Could not extract resume text for {applicant['email']}"
        )

    # Evaluate candidate using Bedrock.
    candidate_score = evaluate_candidate(
        job_description=job_description,
        resume_text=resume_text,
        application_answers=additional_data
    )

    # Save applicant, resume and score in one transaction.
    connection = get_recruitment_connection()

    try:
        with connection.cursor() as cursor:

            # Prevent duplicate processing.
            cursor.execute(
                """
                INSERT INTO recruitment_processed_responses (
                    form_id,
                    response_id
                )
                VALUES (%s, %s)
                ON CONFLICT (form_id, response_id)
                DO NOTHING
                RETURNING response_id;
                """,
                (form_id, response_id)
            )

            inserted = cursor.fetchone()

            if not inserted:
                connection.rollback()

                print(
                    f"Duplicate response ignored: {response_id}"
                )

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
                    resume_file,
                    resume_filename,
                    resume_content_type,
                    additional_data,
                    submitted_at,
                    candidate_score
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s::jsonb,
                    COALESCE(%s, CURRENT_TIMESTAMP),
                    %s
                );
                """,
                (
                    post_id,
                    applicant["full_name"],
                    applicant["email"],
                    applicant["phone"],
                    resume_content,
                    resume_filename,
                    resume_content_type,
                    json.dumps(additional_data),
                    submitted_at,
                    candidate_score
                )
            )

        connection.commit()

        print(
            f"Applicant saved: {applicant['email']} "
            f"| Score: {candidate_score}"
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
