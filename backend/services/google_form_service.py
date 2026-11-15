
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
    "https://www.googleapis.com/auth/drive.file"
]
# ============================================================
# STANDARD APPLICANT FIELDS
# ============================================================

TEMPLATE_FORM_ID = os.getenv(
    "GOOGLE_FORM_TEMPLATE_ID",
    "1jmk_g30IxPnBDXGGIRDkxokXLuqS7OlKeJRYQIhiWD4"
)

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

    """Publish a completed form and enable applicant responses."""

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
            "Google Forms did not confirm that the form was published."
        )

    if not publish_state.get("isAcceptingResponses"):
        raise RuntimeError(
            "The form was published but is not accepting responses."
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

        # Support both "field" and "field_name"
        field_name = (
            question.get("field_name")
            or question.get("field")
        )

        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError(
                f"Question {index + 1} is missing field or field_name."
            )

        field_name = field_name.strip()

        if field_name in question_map:
            raise ValueError(
                f"Duplicate field name: {field_name}"
            )

        # Normalize the question so the rest of the service
        # consistently uses field_name.
        normalized_question = dict(question)
        normalized_question["field_name"] = field_name

        question_map[field_name] = normalized_question

    # These three fields must be supplied by the AI JSON.
    required_fields = ["full_name", "email", "phone"]

    missing_fields = [
        field
        for field in required_fields
        if field not in question_map
    ]

    if missing_fields:
        raise ValueError(
            f"Missing standard applicant fields: {missing_fields}"
        )

    # The resume upload already exists in the master template.
    # Add its internal mapping if the AI JSON did not provide it.
    if "resume_file" not in question_map:
        question_map["resume_file"] = {
            "field_name": "resume_file",
            "question": "Upload Your Resume (PDF)",
            "type": "file",
            "required": True
        }

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
# RESUME QUESTION TITLE
# ============================================================

def get_resume_question_title(resume_question):

    question_text = resume_question.get("question", "")

    if not isinstance(question_text, str):
        question_text = ""

    question_text = question_text.strip()

    generic_titles = {
        "please upload a file",
        "upload a file",
        "resume upload",
        "upload resume",
        "please upload your resume"
    }

    if question_text.lower() in generic_titles:
        return "Upload Your Resume (PDF)"

    return question_text


# ============================================================
# COPY MASTER GOOGLE FORM
# ============================================================

def copy_master_form(title):

    if not TEMPLATE_FORM_ID:
        raise ValueError(
            "Google Form template ID is not configured."
        )

    drive_service = get_drive_service()

    copied_form = drive_service.files().copy(
        fileId=TEMPLATE_FORM_ID,
        body={
            "name": title.strip()
        },
        fields="id,name"
    ).execute()

    form_id = copied_form.get("id")

    if not form_id:
        raise RuntimeError(
            "Google Drive did not return the copied form ID."
        )

    return form_id, copied_form.get("name")


# ============================================================
# FIND TEMPLATE RESUME UPLOAD QUESTION
# ============================================================

def find_resume_upload_question(form_details):

    items = form_details.get("items", [])

    if not items:
        raise ValueError(
            "The master template contains no questions."
        )

    upload_questions = []

    for index, item in enumerate(items):

        question_item = item.get("questionItem", {})
        question = question_item.get("question", {})

        if "fileUploadQuestion" in question:
            upload_questions.append({
                "index": index,
                "item_id": item.get("itemId"),
                "question_id": question.get("questionId")
            })

    if len(upload_questions) != 1:
        raise ValueError(
            "The master template must contain exactly one "
            "file-upload question."
        )

    upload_question = upload_questions[0]

    if upload_question["index"] != len(items) - 1:
        raise ValueError(
            "The resume upload question must be the last "
            "question in the master template."
        )

    if not upload_question["item_id"]:
        raise ValueError(
            "The template resume question has no item ID."
        )

    if not upload_question["question_id"]:
        raise ValueError(
            "The template resume question has no question ID."
        )

    return upload_question


# ============================================================
# CREATE GOOGLE FORM FROM MASTER TEMPLATE
# ============================================================

def create_google_form(title, questions, job_description):

    if not isinstance(title, str) or not title.strip():
        raise ValueError("A valid Google Form title is required.")

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("A valid job description is required.")

    # Validate and normalize the standard and job-specific questions.
    standard_questions, additional_questions = separate_questions(questions)

    resume_question = next(
        question
        for question in standard_questions
        if question["field_name"] == "resume_file"
    )

    # The master template already contains the required file-upload question.
    # Create all other questions before it; do not update the upload item.
    questions_to_create = [
        question
        for question in standard_questions
        if question["field_name"] != "resume_file"
    ]

    # Skip optional file-upload questions such as portfolio_file.
    # Resume upload is already handled by the master template.
    skipped_questions = []
    supported_additional_questions = []

    for question in additional_questions:

        question_type = (
            question.get("type", "")
            .lower()
            .strip()
            .replace("-", "_")
        )

        if question_type == "file":

            if question.get("required", False):
                raise ValueError(
                    f"Required file upload '{question.get('field_name')}' "
                    "is not supported dynamically. "
                    "Use the master Google Form template instead."
                )

            skipped_questions.append({
                "field_name": question.get("field_name"),
                "question": question.get("question"),
                "reason": "Optional file upload is not supported dynamically."
            })

            continue

        supported_additional_questions.append(question)

    questions_to_create.extend(supported_additional_questions)
    # Prepare Google Forms API requests for supported questions.
    question_requests, question_field_names = (
        prepare_google_form_questions(questions_to_create)
    )
    # Copy the master form so the original template remains unchanged.
    form_id, drive_file_name = copy_master_form(title)
    forms_service = get_forms_service()
    drive_service = get_drive_service()

    try:
        # Verify the copied template has exactly one final file-upload item.
        initial_form = forms_service.forms().get(
            formId=form_id
        ).execute()

        upload_question = find_resume_upload_question(initial_form)

        # Update form metadata and insert generated questions.
        # IMPORTANT: Do not use updateItem on the file-upload question.
        # Google Forms rejects updates that alter the QuestionItem type.
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

        for index, request in enumerate(question_requests):
            request["createItem"]["location"]["index"] = index
            batch_requests.append(request)

        forms_service.forms().batchUpdate(
            formId=form_id,
            body={"requests": batch_requests}
        ).execute()

        # Read the completed form to obtain the actual question IDs.
        completed_form = forms_service.forms().get(
            formId=form_id
        ).execute()

        completed_items = completed_form.get("items", [])

        # The generated questions are inserted at the beginning.
        if len(completed_items) < len(question_field_names) + 1:
            raise RuntimeError(
                "The completed form is missing one or more questions."
            )

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
                    f"Google Forms did not return a question ID for "
                    f"'{field_name}'."
                )

            question_mapping[question_id] = field_name

        # Confirm that the original template upload question remains last.
        final_upload_question = find_resume_upload_question(completed_form)
        question_mapping[final_upload_question["question_id"]] = "resume_file"

        # Publish only after all generated questions have been added and verified.
        publish_google_form(forms_service, form_id)

        # Read the form again so the returned URL and state reflect publication.
        completed_form = forms_service.forms().get(
            formId=form_id
        ).execute()

        publish_state = (
            completed_form.get("publishSettings", {})
            .get("publishState", {})
        )

        if not publish_state.get("isPublished") or not publish_state.get("isAcceptingResponses"):
            raise RuntimeError(
                "Google Form was configured, but publication could not be verified."
            )

        form_url = completed_form.get("responderUri")
        if not form_url:
            raise RuntimeError(
                "Google Form was created, but its responder URL "
                "could not be retrieved."
            )

        return {
            "form_id": form_id,
            "title": completed_form.get("info", {}).get("title"),
            "description": completed_form.get("info", {}).get("description"),
            "form_url": form_url,
            "drive_file_name": drive_file_name,
            "skipped_questions": skipped_questions,
            "question_mapping": question_mapping
        }

    except Exception:
        # Avoid leaving behind a partially configured copied form.
        try:
            drive_service.files().delete(fileId=form_id).execute()
        except Exception:
            pass
        raise


# ============================================================
# CREATE GOOGLE FORM DIRECTLY FROM APPROVED JSON
# ============================================================

def create_google_form_from_json(data):

    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON dictionary.")

    job_post = data.get("job_post")
    application_form = data.get("application_form")

    if not isinstance(job_post, dict):
        raise ValueError("Missing or invalid job_post object.")

    if not isinstance(application_form, dict):
        raise ValueError("Missing or invalid application_form object.")

    form_title = application_form.get("form_title")

    # Accept either key used by the job-post payload.
    job_description = (
        job_post.get("job_description")
        or job_post.get("description")
        or application_form.get("job_description")
    )

    questions = application_form.get("questions")

    if not isinstance(form_title, str) or not form_title.strip():
        raise ValueError("A valid application form title is required.")

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("A valid job description is required.")

    if not isinstance(questions, list) or not questions:
        raise ValueError("Application questions must be a non-empty list.")

    return create_google_form(
        title=form_title,
        questions=questions,
        job_description=job_description
    )
