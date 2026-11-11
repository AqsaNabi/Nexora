JOB_POST_FIELDS = [
    "job_title",
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

        value = job_post.get(
            field,
            [] if field in LIST_FIELDS else ""
        )

        if field in LIST_FIELDS:

            if value is None:
                value = []

            if not isinstance(value, list):
                value = [value]

            prepared_job_post[field] = value

        else:

            if value is None:
                value = ""

            prepared_job_post[field] = value

    return prepared_job_post


def prepare_application_form(application_form):

    if not isinstance(application_form, dict):
        raise ValueError("Application form must be a JSON object.")

    form_title = application_form.get("form_title", "")

    if form_title is None:
        form_title = ""

    questions = application_form.get("questions", [])

    if questions is None:
        questions = []

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
        required = question.get("required", False)
        options = question.get("options", [])

        if question_text is None:
            question_text = ""

        if question_type is None:
            question_type = ""

        if not isinstance(question_text, str):
            raise ValueError(
                f"Invalid question text for question {index}."
            )

        if not isinstance(question_type, str):
            raise ValueError(
                f"Invalid question type for question {index}."
            )

        if not isinstance(required, bool):
            raise ValueError(
                f"Required must be true or false for question {index}."
            )

        if options is None:
            options = []

        if not isinstance(options, list):
            raise ValueError(
                f"Options must be a list for question {index}."
            )

        prepared_questions.append({
            "question": question_text,
            "type": question_type,
            "required": required,
            "options": options
        })

    return {
        "form_title": form_title,
        "questions": prepared_questions
    }