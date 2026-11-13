
import uuid


def create_approved_payload(session_id, job_post, application_form):
    """Prepare approved recruitment data in memory."""

    try:
        safe_session_id = str(uuid.UUID(str(session_id)))
    except (ValueError, TypeError):
        raise ValueError("Invalid session ID.")

    if not isinstance(job_post, dict):
        raise ValueError("Invalid job post.")

    if not isinstance(application_form, dict):
        raise ValueError("Invalid application form.")

    if not job_post.get("job_description"):
        raise ValueError("Job description is missing.")

    if not application_form.get("questions"):
        raise ValueError("Application questions are missing.")

    return {
        "session_id": safe_session_id,
        "job_post": job_post,
        "application_form": application_form
    }
