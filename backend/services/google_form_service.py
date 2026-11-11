
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


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
# GOOGLE FORMS AUTHENTICATION
# ============================================================

def get_forms_service():

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

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(credentials.to_json())

    return build(
        "forms",
        "v1",
        credentials=credentials
    )


def rename_form_in_drive(form_id, title):

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        scopes=FORMS_SCOPE
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(credentials.to_json())

    drive_service = build(
        "drive",
        "v3",
        credentials=credentials
    )

    renamed_file = drive_service.files().update(
        fileId=form_id,
        body={
            "name": title.strip()
        },
        fields="id, name"
    ).execute()

    return renamed_file.get("name")
# ============================================================
# VALIDATE AND SEPARATE STANDARD / ADDITIONAL QUESTIONS
# ============================================================

def separate_questions(questions):

    if not isinstance(questions, list) or not questions:
        raise ValueError("Questions must be a non-empty list.")

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
                f"Duplicate field_name found: {field_name}"
            )

        question_map[field_name] = question

    # Check that all standard fields exist
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

    # Keep standard fields in a predictable order
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

    # Everything else is job-specific
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

    for index, question in enumerate(questions):

        question_text = question.get("question", "").strip()
        question_type = question.get("type", "").lower().strip()
        question_type = question_type.replace("-", "_")

        required = question.get("required", False)
        options = question.get("options", [])

        if not question_text:
            raise ValueError(
                f"Question {index + 1} has no question text."
            )

        if not isinstance(required, bool):
            raise ValueError(
                f"Invalid required value for question {index + 1}."
            )

        if not isinstance(options, list):
            raise ValueError(
                f"Options must be a list for question {index + 1}."
            )

        # ----------------------------------------------------
        # FILE UPLOAD
        # ----------------------------------------------------

        if question_type in ("file", "file_upload"):

            skipped_questions.append({
                "field_name": question.get("field_name"),
                "question": question_text,
                "reason": "Handled separately through FastAPI."
            })

            continue

        # ----------------------------------------------------
        # SHORT ANSWER
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # PARAGRAPH
        # ----------------------------------------------------

        elif question_type == "paragraph":

            question_body = {
                "textQuestion": {
                    "paragraph": True
                }
            }

        # ----------------------------------------------------
        # YES / NO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # MULTIPLE CHOICE
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # CHECKBOX
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DROPDOWN
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

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

    if not requests:
        raise ValueError(
            "No supported Google Form questions found."
        )

    return requests, skipped_questions


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

    # Prepare questions before creating the form
    standard_questions, additional_questions = separate_questions(
    questions
    )

    ordered_questions = standard_questions + additional_questions

    requests, skipped_questions = prepare_google_form_questions(
    ordered_questions
    )

    service = get_forms_service()

    # --------------------------------------------------------
    # 1. CREATE GOOGLE FORM
    # --------------------------------------------------------

    form_body = {
        "info": {
            "title": title.strip()
        }
    }

    response = service.forms().create(
        body=form_body
    ).execute()

    form_id = response.get("formId")

    if not form_id:
        raise RuntimeError(
            "Google Form creation did not return a form ID."
        )
    # Rename the Google Drive file using the form title
    rename_form_in_drive(form_id, title)
    # --------------------------------------------------------
    # 2. ADD DESCRIPTION AND APPLICATION QUESTIONS
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

    service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": batch_requests
        }
    ).execute()

    # --------------------------------------------------------
    # 3. RETRIEVE COMPLETED FORM
    # --------------------------------------------------------

    form_details = service.forms().get(
        formId=form_id
    ).execute()

    return {
    "form_id": form_id,
    "title": form_details.get("info", {}).get("title"),
    "description": form_details.get("info", {}).get("description"),
    "form_url": form_details.get("responderUri"),
    "drive_file_name": drive_file_name,
    "skipped_questions": skipped_questions
}
# ============================================================
# CREATE GOOGLE FORM DIRECTLY FROM JSON
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
    job_description = job_post.get("job_description")
    questions = application_form.get("questions")

    if not isinstance(questions, list):
        raise ValueError("Application questions must be a list.")

    return create_google_form(
        title=form_title,
        questions=questions,
        job_description=job_description
    )