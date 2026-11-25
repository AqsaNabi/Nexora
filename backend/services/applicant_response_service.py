import json
from datetime import datetime
 
from backend.database.concect import cur, conn
 
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
 
cursor = cur
connection = conn


def _get(row, key):
    """Safe dict reader for RealDictCursor"""
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    return row[0]

 
def _answer_value(answer):
    text_answers = answer.get("textAnswers", {}).get("answers", [])
    values = [item.get("value", "") for item in text_answers]
    if not values:
        return None
    return values[0] if len(values) == 1 else values
 
 
def _get_form_metadata(form_id):
    try:
        with connection.cursor() as local_cursor:
            # Allow matching with or without the "forms/" prefix
            local_cursor.execute(
                """
                SELECT post_id, question_mapping
                FROM recruitment_metadata
                WHERE form_id = %s 
                   OR form_id = %s
                   OR form_id = %s;
                """,
                (form_id, f"forms/{form_id}", form_id.replace("forms/", ""))
            )
            result = local_cursor.fetchone()
 
            if not result:
                print(f"Database lookup failed for form_id: {form_id}")
                raise ValueError(f"No recruitment post found for form {form_id}")
 
            post_id = _get(result, "post_id")
            question_mapping = _get(result, "question_mapping")
 
            if isinstance(question_mapping, str):
                question_mapping = json.loads(question_mapping)
 
            return post_id, question_mapping or {}
    except Exception as e:
        connection.rollback()
        raise
 
 
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
 
    resume_link = None
    additional_data = {}
 
    # Extract applicant information
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
        raise ValueError(f"Required applicant details missing: {response_id}")
 
    # Get the job description.
    job_description = get_job_description(post_id)
    if not job_description:
        job_description = "No description provided."

    # ---------------------------------------------------------
    # ✅ SAFE RESUME PROCESSING (Won't crash if file is private)
    # ---------------------------------------------------------
    resume_content = None
    resume_filename = None
    resume_content_type = None
    resume_text = "No resume provided"
    candidate_score = None

    if resume_link:
        try:
            resume_content, resume_filename, resume_content_type = (
                download_resume_from_drive(resume_link)
            )
            if resume_content:
                resume_text = extract_resume_text(
                    resume_content, 
                    resume_filename, 
                    resume_content_type
                )
        except Exception as e:
            print(f"⚠️ Could not process resume for {applicant['email']}: {e}")

    if resume_text and resume_text != "No resume provided":
        try:
            candidate_score = evaluate_candidate(
                job_description=job_description,
                resume_text=resume_text,
                application_answers=additional_data
            )
        except Exception as e:
            print(f"⚠️ AI Evaluation failed for {applicant['email']}: {e}")

    # ---------------------------------------------------------
    # SAVE TO DATABASE
    # ---------------------------------------------------------
    try:
        with connection.cursor() as local_cursor:
            # Prevent duplicate processing
            local_cursor.execute(
                """
                INSERT INTO recruitment_processed_responses (form_id, response_id)
                VALUES (%s, %s)
                ON CONFLICT (form_id, response_id)
                DO NOTHING
                RETURNING response_id;
                """,
                (form_id, response_id)
            )
            if not local_cursor.fetchone():
                print(f"Duplicate response ignored: {response_id}")
                return False
 
            submitted_at = response.get("lastSubmittedTime")
            if submitted_at:
                submitted_at = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
 
            local_cursor.execute(
                """
                INSERT INTO recruitment_data (
                    post_id, full_name, email, phone,
                    resume_file, resume_filename, resume_content_type,
                    additional_data, submitted_at, candidate_score
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
        print(f"✅ Applicant saved: {applicant['email']} | Score: {candidate_score}")
        return True
 
    except Exception as e:
        connection.rollback()
        print(f"❌ Database error saving applicant: {e}")
        raise
 
 
def process_form_responses(form_id):
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
 
        result = service.forms().responses().list(**request_args).execute()
 
        for response in result.get("responses", []):
            try:
                if _save_applicant(form_id, response, post_id, question_mapping):
                    saved_count += 1
            except Exception as e:
                # Catch errors per-response so one bad response doesn't block the rest
                print(f"Skipping response {response.get('responseId')}: {e}")
 
        page_token = result.get("nextPageToken")
        if not page_token:
            break
 
    print(f"Processing complete for {post_id}. Saved: {saved_count}")
    return saved_count
