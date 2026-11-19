
import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
TOKEN_FILE = BASE_DIR / "authen" / "token.json"

FORMS_SCOPE = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly"
]


# ============================================================
# STANDARD APPLICANT FIELDS
# ============================================================

STANDARD_FIELDS = {
    "full_name": "text",
    "email": "email",
    "phone": "text",
    "resume_link": "url"
}

STANDARD_FIELD_ORDER = [
    "full_name",
    "email",
    "phone",
    "resume_link"
]


# ============================================================
# GOOGLE AUTHENTICATION
# ============================================================

def get_credentials():

    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            "Google authentication token not found. "
            "Please authenticate with Google first."
        )

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        scopes=FORMS_SCOPE
    )

    if credentials.expired and credentials.refresh_token:

        credentials.refresh(Request())

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    if not credentials.valid:
        raise ValueError(
            "Google credentials are invalid. "
            "Please authenticate with Google again."
        )

    return credentials


def get_forms_service():

    return build(
        "forms",
        "v1",
        credentials=get_credentials()
    )


def get_drive_service():

    return build(
        "drive",
        "v3",
        credentials=get_credentials()
    )


# ============================================================
# PUBLISH GOOGLE FORM
# ============================================================

def publish_google_form(forms_service, form_id):

    response = forms_service.forms().setPublishSettings(
        formId=form_id,
        body={
            "publishSettings": {
                "publishState": {
                    "isPublished": True,
                    "isAcceptingResponses": True
                }
            },
            "updateMask": "publishState"
        }
    ).execute()

    publish_state = (
        response.get("publishSettings", {})
        .get("publishState", {})
    )

    if not publish_state.get("isPublished"):
        raise RuntimeError(
            "Google Form was not published."
        )

    if not publish_state.get("isAcceptingResponses"):
        raise RuntimeError(
            "Google Form is not accepting responses."
        )

    return publish_state


# ============================================================
# RENAME GOOGLE FORM DRIVE FILE
# ============================================================

def rename_form_in_drive(form_id, title):

    drive_service = get_drive_service()

    result = drive_service.files().update(
        fileId=form_id,
        body={
            "name": title.strip()
        },
        fields="id,name"
    ).execute()

    return result.get("name")


# ============================================================
# VALIDATE AND SEPARATE QUESTIONS
# ============================================================

def separate_questions(questions):

    if not isinstance(questions, list) or not questions:
        raise ValueError(
            "Questions must be a non-empty list."
        )

    question_map = {}

    for index, question in enumerate(questions):

        if not isinstance(question, dict):
            raise ValueError(
                f"Question {index + 1} must be a dictionary."
            )

        field_name = (
            question.get("field_name")
            or question.get("field")
        )

        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError(
                f"Question {index + 1} is missing field_name."
            )

        field_name = field_name.strip()

        if field_name in question_map:
            raise ValueError(
                f"Duplicate field name: {field_name}"
            )

        normalized_question = dict(question)
        normalized_question["field_name"] = field_name

        question_map[field_name] = normalized_question

    # Add missing standard fields where appropriate.
    required_defaults = {
        "resume_link": {
            "field_name": "resume_link",
            "question": "Paste Your Resume Google Drive Link",
            "type": "url",
            "required": True
        }
    }

    for field_name, default_question in required_defaults.items():

        if field_name not in question_map:
            question_map[field_name] = default_question

    required_fields = [
        "full_name",
        "email",
        "phone",
        "resume_link"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in question_map
    ]

    if missing_fields:
        raise ValueError(
            f"Missing standard applicant fields: {missing_fields}"
        )

    standard_questions = []

    for field_name in STANDARD_FIELD_ORDER:

        question = question_map[field_name]

        actual_type = (
            question.get("type", "")
            .lower()
            .strip()
            .replace("-", "_")
        )

        expected_type = STANDARD_FIELDS[field_name]

        if actual_type != expected_type:
            raise ValueError(
                f"Invalid type for {field_name}. "
                f"Expected '{expected_type}', got '{actual_type}'."
            )

        standard_questions.append(question)

    additional_questions = [
        question
        for field_name, question in question_map.items()
        if field_name not in STANDARD_FIELDS
    ]

    return standard_questions, additional_questions


# ============================================================
# PREPARE GOOGLE FORM QUESTIONS
# ============================================================

def prepare_google_form_questions(questions):

    if not isinstance(questions, list) or not questions:
        raise ValueError(
            "At least one application question is required."
        )

    requests = []
    question_field_names = []

    for index, question in enumerate(questions):

        question_text = question.get("question", "")

        if not isinstance(question_text, str):
            raise ValueError(
                f"Question {index + 1} has invalid question text."
            )

        question_text = question_text.strip()

        question_type = (
            question.get("type", "")
            .lower()
            .strip()
            .replace("-", "_")
        )

        field_name = question.get("field_name")

        required = question.get("required", False)
        options = question.get("options", [])

        if not question_text:
            raise ValueError(
                f"Question {index + 1} has no question text."
            )

        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError(
                f"Question {index + 1} has no field_name."
            )

        if not isinstance(required, bool):
            raise ValueError(
                f"Invalid required value for question {index + 1}."
            )

        if not isinstance(options, list):
            raise ValueError(
                f"Options must be a list for question {index + 1}."
            )

        # Short answer
        if question_type in (
            "text",
            "short_answer",
            "email",
            "number",
            "url"
        ):

            question_body = {
                "textQuestion": {
                    "paragraph": False
                }
            }

        # Paragraph
        elif question_type == "paragraph":

            question_body = {
                "textQuestion": {
                    "paragraph": True
                }
            }

        # Yes / No
        elif question_type == "yes_no":

            question_body = {
                "choiceQuestion": {
                    "type": "RADIO",
                    "options": [
                        {"value": "Yes"},
                        {"value": "No"}
                    ],
                    "shuffle": False
                }
            }

        # Multiple choice
        elif question_type == "multiple_choice":

            if not options:
                raise ValueError(
                    f"Multiple-choice question {index + 1} "
                    "must have options."
                )

            question_body = {
                "choiceQuestion": {
                    "type": "RADIO",
                    "options": [
                        {"value": str(option)}
                        for option in options
                    ],
                    "shuffle": False
                }
            }

        # Checkbox
        elif question_type == "checkbox":

            if not options:
                raise ValueError(
                    f"Checkbox question {index + 1} "
                    "must have options."
                )

            question_body = {
                "choiceQuestion": {
                    "type": "CHECKBOX",
                    "options": [
                        {"value": str(option)}
                        for option in options
                    ],
                    "shuffle": False
                }
            }

        # Dropdown
        elif question_type == "dropdown":

            if not options:
                raise ValueError(
                    f"Dropdown question {index + 1} "
                    "must have options."
                )

            question_body = {
                "choiceQuestion": {
                    "type": "DROP_DOWN",
                    "options": [
                        {"value": str(option)}
                        for option in options
                    ],
                    "shuffle": False
                }
            }

        # Date
        elif question_type == "date":

            question_body = {
                "dateQuestion": {
                    "includeTime": False,
                    "includeYear": True
                }
            }

        else:

            raise ValueError(
                f"Unsupported question type '{question_type}' "
                f"for question {index + 1}."
            )

        item = {
            "title": question_text,
            "questionItem": {
                "question": {
                    "required": required,
                    **question_body
                }
            }
        }

        requests.append({
            "createItem": {
                "item": item,
                "location": {
                    "index": len(requests)
                }
            }
        })

        question_field_names.append(field_name)

    return requests, question_field_names


# ============================================================
# CREATE GOOGLE FORM DIRECTLY
# ============================================================

def create_google_form(title, questions, job_description):

    if not isinstance(title, str) or not title.strip():
        raise ValueError(
            "A valid Google Form title is required."
        )

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError(
            "A valid job description is required."
        )

    standard_questions, additional_questions = separate_questions(
        questions
    )

    # Put standard questions first.
    questions_to_create = (
        standard_questions + additional_questions
    )

    question_requests, question_field_names = (
        prepare_google_form_questions(questions_to_create)
    )

    forms_service = get_forms_service()
    drive_service = get_drive_service()

    form_id = None

    try:

        # Create a completely new form.
        created_form = forms_service.forms().create(
            body={
                "info": {
                    "title": title.strip(),
                    "documentTitle": title.strip()
                }
            }
        ).execute()

        form_id = created_form.get("formId")

        if not form_id:
            raise RuntimeError(
                "Google Forms did not return a form ID."
            )

        # Add generated questions.
        batch_requests = [
            {
                "updateFormInfo": {
                    "info": {
                        "title": title.strip(),
                        "description": job_description.strip()
                    },
                    "updateMask": "title,description"
                }
            }
        ]

        batch_requests.extend(question_requests)

        forms_service.forms().batchUpdate(
            formId=form_id,
            body={
                "requests": batch_requests
            }
        ).execute()

        # Retrieve the completed form.
        completed_form = forms_service.forms().get(
            formId=form_id
        ).execute()

        completed_items = completed_form.get("items", [])

        if len(completed_items) != len(question_field_names):
            raise RuntimeError(
                "The number of created questions does not match "
                "the expected number."
            )

        # Map Google Forms question IDs to backend field names.
        question_mapping = {}

        for index, field_name in enumerate(question_field_names):

            item = completed_items[index]

            question = (
                item.get("questionItem", {})
                .get("question", {})
            )

            question_id = question.get("questionId")

            if not question_id:
                raise RuntimeError(
                    f"Question ID missing for {field_name}."
                )

            question_mapping[question_id] = field_name

        # Publish the form.
        publish_google_form(
            forms_service,
            form_id
        )

        # Retrieve the published form.
        completed_form = forms_service.forms().get(
            formId=form_id
        ).execute()

        publish_state = (
            completed_form.get("publishSettings", {})
            .get("publishState", {})
        )

        if (
            not publish_state.get("isPublished")
            or not publish_state.get("isAcceptingResponses")
        ):
            raise RuntimeError(
                "Google Form publication could not be verified."
            )

        form_url = completed_form.get("responderUri")

        if not form_url:
            raise RuntimeError(
                "Google Form responder URL could not be retrieved."
            )

        # Get Drive file title.
        drive_file = drive_service.files().get(
            fileId=form_id,
            fields="id,name"
        ).execute()

        return {
            "form_id": form_id,
            "title": completed_form.get("info", {}).get("title"),
            "description": completed_form.get("info", {}).get("description"),
            "form_url": form_url,
            "drive_file_name": drive_file.get("name"),
            "skipped_questions": [],
            "question_mapping": question_mapping
        }

    except Exception:

        # Delete a partially created form if configuration fails.
        if form_id:
            try:
                drive_service.files().delete(
                    fileId=form_id
                ).execute()
            except Exception:
                pass

        raise


# ============================================================
# CREATE GOOGLE FORM FROM APPROVED JSON
# ============================================================

def create_google_form_from_json(data):

    if not isinstance(data, dict):
        raise ValueError(
            "Input must be a JSON dictionary."
        )

    job_post = data.get("job_post")
    application_form = data.get("application_form")

    if not isinstance(job_post, dict):
        raise ValueError(
            "Missing or invalid job_post object."
        )

    if not isinstance(application_form, dict):
        raise ValueError(
            "Missing or invalid application_form object."
        )

    form_title = application_form.get("form_title")

    job_description = (
        job_post.get("job_description")
        or job_post.get("description")
        or application_form.get("job_description")
    )

    questions = application_form.get("questions")

    if not isinstance(form_title, str) or not form_title.strip():
        raise ValueError(
            "A valid application form title is required."
        )

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError(
            "A valid job description is required."
        )

    if not isinstance(questions, list) or not questions:
        raise ValueError(
            "Application questions must be a non-empty list."
        )

    return create_google_form(
        title=form_title,
        questions=questions,
        job_description=job_description
    )
