
import json
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
    "https://www.googleapis.com/auth/drive.file"
]


# ============================================================
# STANDARD APPLICANT FIELDS
# ============================================================

STANDARD_FIELDS = {
    "full_name": "text",
    "email": "email",
    "phone": "text",
    "resume_file": "file"
}

STANDARD_FIELD_ORDER = [
    "full_name",
    "email",
    "phone",
    "resume_file"
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

    credentials = get_credentials()

    return build(
        "forms",
        "v1",
        credentials=credentials
    )


def get_drive_service():

    credentials = get_credentials()

    return build(
        "drive",
        "v3",
        credentials=credentials
    )


# ============================================================
# RENAME GOOGLE FORM
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

        field_name = question.get("field_name")

        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError(
                f"Question {index + 1} is missing field_name."
            )

        field_name = field_name.strip()

        if field_name in question_map:
            raise ValueError(
                f"Duplicate field_name: {field_name}"
            )

        question_map[field_name] = question

    missing_fields = [
        field
        for field in STANDARD_FIELD_ORDER
        if field not in question_map
    ]

    if missing_fields:
        raise ValueError(
            f"Missing standard applicant fields: {missing_fields}"
        )

    standard_questions = []
    additional_questions = []

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

    for field_name, question in question_map.items():

        if field_name not in STANDARD_FIELDS:
            additional_questions.append(question)

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
    skipped_questions = []
    question_field_names = []

    for index, question in enumerate(questions):

        question_text = question.get("question", "").strip()

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

        # FILE UPLOAD

        if question_type in ("file", "file_upload"):

            skipped_questions.append({
                "field_name": field_name,
                "question": question_text,
                "reason": "Handled separately through FastAPI."
            })

            continue

        # SHORT ANSWER

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

        # PARAGRAPH

        elif question_type == "paragraph":

            question_body = {
                "textQuestion": {
                    "paragraph": True
                }
            }

        # YES / NO

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

        # MULTIPLE CHOICE

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

        # CHECKBOX

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

        # DROPDOWN

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

        # DATE

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

    if not requests:
        raise ValueError(
            "No supported Google Form questions found."
        )

    return requests, skipped_questions, question_field_names


# ============================================================
# CREATE GOOGLE FORM
# ============================================================

def create_google_form(title, questions, job_description):

    if not isinstance(title, str) or not title.strip():
        raise ValueError(
            "A valid Google Form title is required."
        )

    if (
        not isinstance(job_description, str)
        or not job_description.strip()
    ):
        raise ValueError(
            "A valid job description is required."
        )

    # Validate questions

    standard_questions, additional_questions = separate_questions(
        questions
    )

    ordered_questions = (
        standard_questions + additional_questions
    )

    # Prepare Google API requests

    requests, skipped_questions, question_field_names = (
        prepare_google_form_questions(ordered_questions)
    )

    service = get_forms_service()

    # --------------------------------------------------------
    # 1. CREATE GOOGLE FORM
    # --------------------------------------------------------

    form_response = service.forms().create(
        body={
            "info": {
                "title": title.strip()
            }
        }
    ).execute()

    form_id = form_response.get("formId")

    if not form_id:
        raise RuntimeError(
            "Google Form creation did not return a form ID."
        )

    # --------------------------------------------------------
    # 2. RENAME GOOGLE DRIVE FILE
    # --------------------------------------------------------

    drive_file_name = rename_form_in_drive(
        form_id,
        title
    )

    # --------------------------------------------------------
    # 3. ADD DESCRIPTION AND QUESTIONS
    # --------------------------------------------------------

    batch_requests = [
        {
            "updateFormInfo": {
                "info": {
                    "description": job_description.strip()
                },
                "updateMask": "description"
            }
        }
    ]

    batch_requests.extend(requests)

    batch_response = service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": batch_requests
        }
    ).execute()

    replies = batch_response.get("replies", [])

    if len(replies) != len(requests) + 1:
        raise RuntimeError(
            "Google Forms returned an unexpected number of replies."
        )

    # --------------------------------------------------------
    # 4. CREATE QUESTION ID TO FIELD NAME MAPPING
    # --------------------------------------------------------

    question_mapping = {}

    for index, field_name in enumerate(
        question_field_names,
        start=1
    ):

        create_item_response = (
            replies[index].get("createItem", {})
        )

        question_ids = create_item_response.get(
            "questionId",
            []
        )

        if not question_ids:
            raise RuntimeError(
                f"Google did not return a question ID for {field_name}."
            )

        question_mapping[question_ids[0]] = field_name

    # --------------------------------------------------------
    # 5. RETRIEVE COMPLETED FORM
    # --------------------------------------------------------
    
    # 5. RETRIEVE COMPLETED FORM

    form_details = service.forms().get(
        formId=form_id
    ).execute()

    form_url = form_details.get("responderUri")

    if not form_url:
        raise RuntimeError(
            "Google Form was created, but its responder URL "
            "could not be retrieved."
        )

    return {
        "form_id": form_id,
        "title": form_details.get("info", {}).get("title"),
        "description": form_details.get("info", {}).get("description"),
        "form_url": form_url,
        "drive_file_name": drive_file_name,
        "skipped_questions": skipped_questions,
        "question_mapping": question_mapping
    }


# ============================================================
# CREATE GOOGLE FORM DIRECTLY FROM APPROVED JSON
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

    job_description = job_post.get("job_description")

    questions = application_form.get("questions")

    if not isinstance(questions, list):
        raise ValueError(
            "Application questions must be a list."
        )

    return create_google_form(
        title=form_title,
        questions=questions,
        job_description=job_description
    )
