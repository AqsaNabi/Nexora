"""
Create Google Forms from scratch for Nexora WITHOUT a resume-upload question.

Place this file at:
    backend/services/google_form_scratch_service.py

It reuses the existing Google authentication helpers from google_form_service.py.
The form is created empty with Forms API, then populated with ordinary questions.
No master template is copied and no FILE_UPLOAD question is created.
"""

from typing import Any

from backend.services.google_form_service import (
    get_forms_service,
    get_drive_service,
)

def ensure_resume_link_question(
    questions: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    for question in questions:
        field_name = question.get("field_name", "").lower()

        if field_name == "resume_link":
            question["type"] = "url"
            question["required"] = True
            return questions

    questions.append({
        "field_name": "resume_link",
        "question": "Paste Your Resume Google Drive Link",
        "type": "url",
        "required": True,
        "description": (
            "Paste a Google Drive link to your resume. "
            "Make sure the file is accessible to the recruitment system."
        )
    })

    return questions
def _get_question_title(question: dict[str, Any]) -> str:
    """Read the question label from the common Nexora AI response formats."""
    for key in ("question", "title", "label", "text", "question_text"):
        value = question.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    raise ValueError(f"Question has no title: {question!r}")


def _get_choice_options(question: dict[str, Any]) -> list[str]:
    """Normalize options/choices into the format required by Google Forms."""
    raw_options = question.get("options") or question.get("choices") or []
    options: list[str] = []

    for option in raw_options:
        if isinstance(option, str):
            value = option.strip()
        elif isinstance(option, dict):
            value = (
                option.get("value")
                or option.get("label")
                or option.get("text")
                or ""
            )
            value = str(value).strip()
        else:
            value = str(option).strip()

        if value and value not in options:
            options.append(value)

    return options


def _build_question_item(question: dict[str, Any]) -> dict[str, Any]:
    """
    Convert one Nexora application-form question into a Google Forms API item.

    Supported types:
      text, short_answer, email, number, url,
      paragraph, long_answer,
      yes_no, multiple_choice, checkbox, dropdown,
      date, time.

    Email, number and URL are represented as ordinary short-text questions.
    The Google Forms API's standard question schema does not provide a
    dedicated question type for those three values.
    """
    title = _get_question_title(question)

    raw_type = str(question.get("type", "text")).strip().lower()
    question_type = raw_type.replace("-", "_").replace(" ", "_")

    required_value = question.get("required", False)
    if isinstance(required_value, str):
        required = required_value.strip().lower() in ("true", "yes", "1", "required")
    else:
        required = bool(required_value)

    question_body: dict[str, Any] = {"required": required}

    if question_type in ("paragraph", "long_answer", "long_text"):
        question_body["textQuestion"] = {"paragraph": True}

    elif question_type in (
        "multiple_choice",
        "multiplechoice",
        "radio",
        "checkbox",
        "checkboxes",
        "dropdown",
        "drop_down",
        "yes_no",
    ):
        if question_type == "yes_no":
            options = ["Yes", "No"]
            choice_type = "RADIO"
        else:
            options = _get_choice_options(question)

            if question_type in ("checkbox", "checkboxes"):
                choice_type = "CHECKBOX"
            elif question_type in ("dropdown", "drop_down"):
                choice_type = "DROP_DOWN"
            else:
                choice_type = "RADIO"

        if not options:
            raise ValueError(
                f"Choice question '{title}' must contain at least one option."
            )

        question_body["choiceQuestion"] = {
            "type": choice_type,
            "options": [{"value": option} for option in options],
            "shuffle": False,
        }

    elif question_type in ("date",):
        question_body["dateQuestion"] = {
            "includeTime": False,
            "includeYear": True,
        }

    elif question_type in ("time",):
        question_body["timeQuestion"] = {
            "duration": False,
        }

    else:
        # text, short_answer, email, number, url, and unknown types
        # are safely represented as ordinary short-text questions.
        question_body["textQuestion"] = {"paragraph": False}

    item: dict[str, Any] = {
        "title": title,
        "questionItem": {
            "question": question_body,
        },
    }

    description = question.get("description") or question.get("help_text")
    if isinstance(description, str) and description.strip():
        item["description"] = description.strip()

    return item


def create_google_form_from_scratch(
    title: str,
    description: str,
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create and publish a brand-new Google Form without a resume-upload field.

    Returns a structure compatible with the main fields returned by the
    previous Nexora Google Form service.
    """
    title = (title or "").strip()
    description = (description or "").strip()

    if not title:
        raise ValueError("Google Form title cannot be empty.")

    if not isinstance(questions, list) or not questions:
        raise ValueError("At least one application question is required.")

    forms_service = get_forms_service()
    drive_service = get_drive_service()

    form_id = None

    try:
        # Step 1: Create a completely new, empty form.
        # New API-created forms are explicitly kept unpublished until we
        # finish adding the questions.
        created_form = forms_service.forms().create(
            body={
                "info": {
                    "title": title,
                    "documentTitle": title,
                }
            },
            unpublished=True,
        ).execute()

        form_id = created_form.get("formId")
        if not form_id:
            raise RuntimeError("Google Forms API did not return a form ID.")

        # Step 2: Add the description and all ordinary questions.
        requests = []

        if description:
            requests.append({
                "updateFormInfo": {
                    "info": {"description": description},
                    "updateMask": "description",
                }
            })

        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                raise ValueError(
                    f"Question at index {index} must be a JSON object."
                )

            item = _build_question_item(question)

            requests.append({
                "createItem": {
                    "item": item,
                    "location": {"index": index},
                }
            })

        forms_service.forms().batchUpdate(
            formId=form_id,
            body={"requests": requests},
        ).execute()

        # Step 3: Publish the form so applicants can respond.

        forms_service.forms().setPublishSettings(
            formId=form_id,
            body={
                "publishSettings": {
                    "publishState": {
                        "isPublished": True,
                        "isAcceptingResponses": True
                    }
                }
            }
        ).execute()


        # Step 4: Read the finished form and verify that no upload item exists.
        final_form = forms_service.forms().get(
            formId=form_id
        ).execute()

        for item in final_form.get("items", []):
            question_body = (
                item.get("questionItem", {})
                .get("question", {})
            )

            if "fileUploadQuestion" in question_body:
                raise RuntimeError(
                    "Unexpected file-upload question found in the new form."
                )

        # Build a simple title -> question ID map for downstream processing.
        question_mapping = {}
          # Build question ID -> field name mapping.

        for index, item in enumerate(final_form.get("items", [])):
            question_body = (
                item.get("questionItem", {})
                .get("question", {})
            )

            question_id = question_body.get("questionId")

            if question_id:
                field_name = (
                    questions[index].get("field_name")
                    if index < len(questions)
                    else None
                )

        if field_name:
            question_mapping[question_id] = field_name
        else:
            question_mapping[question_id] = item.get("title")
        for item in final_form.get("items", []):
            question_body = (
                item.get("questionItem", {})
                .get("question", {})
            )
            question_id = question_body.get("questionId")
            item_title = item.get("title")

            if question_id and item_title:
                question_mapping[question_id] = field_name

        responder_uri = final_form.get("responderUri")
        if not responder_uri:
            responder_uri = (
                f"https://docs.google.com/forms/d/{form_id}/viewform"
            )

        return {
            "form_id": form_id,
            "title": title,
            "description": description,
            "form_url": responder_uri,
            "editor_url": f"https://docs.google.com/forms/d/{form_id}/edit",
            "drive_file_name": title,
            "skipped_questions": [],
            "question_mapping": question_mapping,
            "resume_upload_included": False,
        }

    except Exception:
        # If creation fails partway through, remove the incomplete form.
        if form_id:
            try:
                drive_service.files().delete(fileId=form_id).execute()
            except Exception:
                pass
        raise


def create_google_form_from_json(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience wrapper for Nexora's job_post/application_form JSON response.

    Expected shape:
    {
        "job_post": {"job_title": "Java Engineer", ...},
        "application_form": {
            "title": "Java Engineer - Application Form",
            "description": "...",
            "questions": [...]
        }
    }
    """
    if not isinstance(data, dict):
        raise ValueError("Input data must be a JSON object.")

    job_post = data.get("job_post") or {}
    application_form = data.get("application_form") or {}

    if not isinstance(application_form, dict):
        raise ValueError("'application_form' must be a JSON object.")

    job_title = (
        job_post.get("job_title")
        or job_post.get("title")
        or "Job Application"
    )

    form_title = (
        application_form.get("title")
        or f"{job_title} - Application Form"
    )

    form_description = (
        application_form.get("description")
        or f"Application form for the {job_title} position."
    )

    questions = application_form.get("questions") or []

    questions = ensure_resume_link_question(questions)

    # Deliberately do not inject a resume_file question.
    return create_google_form_from_scratch(
        title=form_title,
        description=form_description,
        questions=questions,
    )
