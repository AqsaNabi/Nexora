
import re

JOB_POST_FIELDS = [
    "job_title",
    "job_description",
    "department",
    "location",
    "work_mode",
    "employment_type",
    "experience",
    "role_summary",
    "responsibilities",
    "required_skills",
    "preferred_skills",
    "education",
    "benefits",
    "application_instructions",
]

LIST_FIELDS = [
    "responsibilities",
    "required_skills",
    "preferred_skills",
    "education",
    "benefits",
]

ALLOWED_QUESTION_TYPES = {
    "text", "email", "number", "yes_no",
    "multiple_choice", "dropdown", "date", "url", "file", "tel",
}

STANDARD_QUESTIONS = [
    {
        "field_name": "full_name",
        "question": "Full Name",
        "type": "text",
        "required": True,
        "options": [],
        "validation": {},
    },
    {
        "field_name": "email",
        "question": "Email Address",
        "type": "email",
        "required": True,
        "options": [],
        "validation": {"format": "email"},
    },
    {
        "field_name": "phone",
        "question": "Phone Number",
        "type": "text",
        "required": True,
        "options": [],
        "validation": {},
    },
    {
        "field_name": "resume_file",
        "question": "Upload Resume (PDF)",
        "type": "file",
        "required": True,
        "options": [],
        "validation": {
            "accept": [".pdf"],
            "storage_field": "resume_file",
        },
    },
]


# ============================================================
# HELPERS
# ============================================================

def _as_text(value):

    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return ""

    return str(value).strip()


def _as_list(value):

    if value is None or value == "":
        return []

    if isinstance(value, list):
        return value

    return [value]


def _normalize(value):

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


# ============================================================
# DUPLICATE QUESTION DETECTION
# ============================================================

STANDARD_FIELD_ALIASES = {

    "full_name": {
        "fullname",
        "name",
        "applicantname",
        "candidatefullname",
    },

    "email": {
        "email",
        "emailaddress",
        "applicantemail",
        "candidateemail",
    },

    "phone": {
        "phone",
        "phonenumber",
        "mobile",
        "mobilenumber",
        "contactnumber",
        "contactphone",
    },

    "resume_file": {
        "resume",
        "resumefile",
        "uploadresume",
        "resumeurl",
        "resumelink",
        "resumeurlorfilelink",
        "cv",
        "cvfile",
        "uploadcv",
    },
}


STANDARD_QUESTION_ALIASES = {

    "full_name": {
        "fullname",
        "yourfullname",
        "enterfullname",
        "applicantname",
        "candidatename",
    },

    "email": {
        "email",
        "emailaddress",
        "youremail",
        "youremailaddress",
        "enteremailaddress",
    },

    "phone": {
        "phone",
        "phonenumber",
        "mobilenumber",
        "contactnumber",
        "yourphonenumber",
        "yourcontactnumber",
    },

    "resume_file": {
        "resume",
        "resumepdf",
        "uploadresume",
        "uploadresumepdf",
        "uploadyourresume",
        "uploadyourresumepdf",
        "resumefile",
        "resumelink",
        "resumeurlorfilelink",
        "cv",
        "uploadcv",
    },
}


def _is_standard_duplicate(field_name, question_text):

    normalized_field = _normalize(field_name)
    normalized_question = _normalize(question_text)

    for standard_field, aliases in STANDARD_FIELD_ALIASES.items():

        if normalized_field == standard_field:
            return True

        if normalized_field in aliases:
            return True

    for standard_field, aliases in STANDARD_QUESTION_ALIASES.items():

        if normalized_question in aliases:
            return True

    # Catch common resume URL/file wording.
    if (
        "resume" in normalized_question
        and any(
            word in normalized_question
            for word in ("upload", "file", "url", "link")
        )
    ):
        return True

    if normalized_question in {"cv", "uploadcv", "cvfile"}:
        return True

    return False


# ============================================================
# JOB DESCRIPTION
# ============================================================

def build_job_description(job_post):

    sections = []

    role_summary = _as_text(
        job_post.get("role_summary")
    )

    if role_summary:

        sections.extend([
            "Role Summary",
            role_summary
        ])

    for field, heading in (
        ("responsibilities", "Responsibilities"),
        ("required_skills", "Required Skills"),
        ("preferred_skills", "Preferred Skills"),
        ("education", "Education"),
        ("benefits", "Benefits"),
    ):

        values = _as_list(
            job_post.get(field)
        )

        values = [
            _as_text(item)
            for item in values
            if _as_text(item)
        ]

        if values:

            sections.append(heading)

            sections.extend(
                f"- {item}"
                for item in values
            )

    for field, heading in (
        ("department", "Department"),
        ("location", "Location"),
        ("work_mode", "Work Mode"),
        ("employment_type", "Employment Type"),
        ("experience", "Experience"),
    ):

        value = _as_text(
            job_post.get(field)
        )

        if value:
            sections.append(f"{heading}: {value}")

    instructions = _as_text(
        job_post.get("application_instructions")
    )

    if instructions:

        sections.extend([
            "Application Instructions",
            instructions
        ])

    return "\n\n".join(sections)


def prepare_job_post(job_post):

    if not isinstance(job_post, dict):
        raise ValueError("Job post must be a JSON object.")

    prepared = {}

    for field in JOB_POST_FIELDS:

        value = job_post.get(
            field,
            [] if field in LIST_FIELDS else ""
        )

        if field in LIST_FIELDS:

            prepared[field] = _as_list(value)

        else:

            prepared[field] = _as_text(value)

    if not prepared["job_description"]:

        prepared["job_description"] = build_job_description(
            prepared
        )

    return prepared


# ============================================================
# APPLICATION FORM
# ============================================================

def _make_field_name(question, index):

    words = re.findall(
        r"[a-zA-Z0-9]+",
        question.lower()
    )

    return "_".join(words) or f"custom_question_{index}"


def prepare_application_form(application_form):

    if not isinstance(application_form, dict):

        raise ValueError(
            "Application form must be a JSON object."
        )

    form_title = _as_text(
        application_form.get("form_title")
    )

    raw_questions = application_form.get(
        "questions",
        []
    )

    if raw_questions is None:
        raw_questions = []

    if not isinstance(raw_questions, list):

        raise ValueError(
            "Application questions must be a list."
        )

    prepared_questions = []

    used_names = set()

    # Standard applicant questions always appear first.

    for field in STANDARD_QUESTIONS:

        prepared_questions.append(dict(field))

        used_names.add(
            field["field_name"]
        )

    # Add job-specific questions without duplicates.

    for index, question in enumerate(
        raw_questions,
        start=1
    ):

        if not isinstance(question, dict):

            raise ValueError(
                f"Question {index} must be a JSON object."
            )

        question_text = _as_text(
            question.get("question")
        )

        if not question_text:
            continue

        field_name = _as_text(
            question.get("field_name")
        )

        if not field_name:

            field_name = _make_field_name(
                question_text,
                index
            )

        field_name = re.sub(
            r"[^a-zA-Z0-9_]",
            "_",
            field_name.lower()
        )

        # Filter duplicates of standard questions.
        if _is_standard_duplicate(
            field_name,
            question_text
        ):
            continue

        # Filter duplicate custom field names.
        if field_name in used_names:
            continue

        question_type = _as_text(
            question.get("type")
        ).lower() or "text"

        if question_type not in ALLOWED_QUESTION_TYPES:
            question_type = "text"

        required = question.get(
            "required",
            False
        )

        if not isinstance(required, bool):
            required = False

        options = question.get(
            "options",
            []
        )

        if not isinstance(options, list):
            options = []

        validation = question.get(
            "validation",
            {}
        )

        if not isinstance(validation, dict):
            validation = {}

        prepared_questions.append({

            "field_name": field_name,

            "question": question_text,

            "type": question_type,

            "required": required,

            "options": options,

            "validation": validation,

        })

        used_names.add(field_name)

    additional_data = application_form.get(
        "additional_data",
        {}
    )

    if not isinstance(additional_data, dict):
        additional_data = {}

    submitted_at = _as_text(
        application_form.get("submitted_at")
    )

    return {

        "form_title": form_title,

        "questions": prepared_questions,

        "additional_data": additional_data,

        "submitted_at": submitted_at,

    }
