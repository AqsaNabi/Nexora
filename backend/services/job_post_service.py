
JOB_POST_FIELDS = [
    "job_title",
    "job_description",
    "department",
    "location",
    "work_mode",
    "employment_type",
    "experience",
    "salary_range",
    "role_summary",
    "responsibilities",
    "required_skills",
    "preferred_skills",
    "education",
    "benefits",
    "application_instructions"
]

LIST_FIELDS = [
    "responsibilities",
    "required_skills",
    "preferred_skills",
    "education",
    "benefits"
]


def prepare_job_post(job_post):

    if not isinstance(job_post, dict):
        raise ValueError("Job post must be a JSON object.")

    prepared_job_post = {}

    for field in JOB_POST_FIELDS:

        value = job_post.get(field)

        if field in LIST_FIELDS:

            if value is None:
                value = []

            if not isinstance(value, list):
                value = [value]

        else:

            if value is None:
                value = ""

            if not isinstance(value, str):
                value = str(value)

        prepared_job_post[field] = value

    return prepared_job_post


def prepare_application_form(application_form):

    if not isinstance(application_form, dict):
        raise ValueError("Application form must be a JSON object.")

    form_title = application_form.get("form_title", "")

    if not isinstance(form_title, str):
        raise ValueError("Form title must be text.")

    questions = application_form.get("questions", [])

    if not isinstance(questions, list):
        raise ValueError("Application questions must be a list.")

    prepared_questions = []

    for index, question in enumerate(questions, start=1):

        if not isinstance(question, dict):
            raise ValueError(
                f"Question {index} must be a JSON object."
            )

        question_text = question.get("question", "")
        question_type = question.get("type", "")
        field_name = question.get("field_name", "")
        required = question.get("required", False)
        options = question.get("options", [])
        validation = question.get("validation", {})

        if not isinstance(question_text, str):
            raise ValueError(
                f"Invalid question text at question {index}."
            )

        if not isinstance(question_type, str):
            raise ValueError(
                f"Invalid question type at question {index}."
            )

        if not isinstance(field_name, str):
            raise ValueError(
                f"Invalid field_name at question {index}."
            )

        if not isinstance(required, bool):
            raise ValueError(
                f"Required must be true or false at question {index}."
            )

        if not isinstance(options, list):
            raise ValueError(
                f"Options must be a list at question {index}."
            )

        if not isinstance(validation, dict):
            raise ValueError(
                f"Validation must be a JSON object at question {index}."
            )

        prepared_questions.append({
            "field_name": field_name,
            "question": question_text,
            "type": question_type,
            "required": required,
            "options": options,
            "validation": validation
        })

    return {
        "form_title": form_title,
        "questions": prepared_questions,
        "additional_data": application_form.get("additional_data", {}),
        "submitted_at": application_form.get("submitted_at", "")
    }
