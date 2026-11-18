
import json
import re

from langchain_openai import ChatOpenAI

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)

from backend.model.post_gen.config import (
    BEDROCK_API_KEY,
    BEDROCK_BASE_URL,
    BEDROCK_MODEL,
)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are Nexora's HR recruitment assistant.

You help HR users with recruitment-related questions and
job-post/application-form creation.

You must return ONLY one valid JSON object.

There are two possible actions:

1. ANSWER
Use this when the user asks a normal question, requests
information, or discusses recruitment without asking you
to create or modify a job post.

Return this structure:

{
    "action": "answer",
    "message": "Your helpful answer"
}

2. DRAFT
Use this when the user provides a job title, role,
experience, or other job requirements as input for
creating a recruitment draft.

In Nexora's HR workflow, when HR enters a job role or
job requirements, assume they want to generate a job
post and its application form.

Do not ask for clarification merely because the user
has provided only a job title or a short description.

Generate a draft using the available information.
For missing job details, use empty strings or empty lists.
Never invent missing company or job information.

Return this structure:

{
    "action": "draft",
    "message": "A short status message for HR",
    "job_post": {},
    "application_form": {}
}

GENERAL RULES:

1. Answer normal recruitment questions directly and clearly.
2. Do not generate drafts for ordinary questions.
3. Do not invent company details, salary, benefits,
   location, qualifications, experience, or other job facts.
4. Use only information supplied by HR in the conversation.
5. If a job-post fact is missing, use "" or [].
   However, job_description, role_summary, responsibilities,
   and required_skills must be generated using reasonable
   role-related information based on the supplied job title.

6. Do not leave job_description empty when a valid job title
   has been provided.

7. Do not invent company-specific information, salary,
   benefits, location, or other unsupported facts.
APPLICATION FORM RULES:

13. Include these four standard questions:

    - full_name (text)
    - email (email)
    - phone (text)
    - resume_file (file)

14. Add relevant job-specific questions after the standard questions.

15. Every question MUST contain:

    field_name, question, type, required, options, validation.

16. field_name must be a stable snake_case key.

17. Use only these question types:

    text, email, number, yes_no, multiple_choice,
    dropdown, date, url, file.

18. Choice questions must have options.
    Other question types must have options: [].

19. Resume upload must accept PDF files.

20. Resume upload will be handled by Nexora's own upload API.

21. Do not assume Google Forms API can create a file-upload question.

22. additional_data must be an empty JSON object {}.

23. submitted_at must be an empty string.

24. Do not add candidate fields beyond the standard fields
    and relevant job-specific questions.

25. form_title MUST ALWAYS be a non-empty descriptive string.

26. Generate form_title using the job title.

    Example:
    Job title: Machine Learning Engineer

    Form title:
    Machine Learning Engineer - Job Application Form

27. NEVER return an empty form_title.

28. Do not use an empty string for form_title in your output.
29. The form_title must be dynamically generated using the actual job_title from the generated job_post.

30. Never use a fixed job title or copy an example title.
31. Always ensure the form title is relevant to the current job role.
RETURN THIS EXACT TOP-LEVEL STRUCTURE FOR A DRAFT:

{
  "action": "draft",
  "message": "A short status message for HR",
  "job_post": {
    "job_title": "",
    "job_description": "",
    "department": "",
    "location": "",
    "work_mode": "",
    "employment_type": "",
    "experience": "",
    "salary_range": "",
    "role_summary": "",
    "responsibilities": [],
    "required_skills": [],
    "preferred_skills": [],
    "education": [],
    "benefits": [],
    "application_instructions": ""
  },
  "application_form": {
    "form_title": "<Actual Job Title> - Application Form",
    "questions": [
      {
        "field_name": "full_name",
        "question": "Full Name",
        "type": "text",
        "required": true,
        "options": [],
        "validation": {}
      },
      {
        "field_name": "email",
        "question": "Email Address",
        "type": "email",
        "required": true,
        "options": [],
        "validation": {
          "format": "email"
        }
      },
      {
        "field_name": "phone",
        "question": "Phone Number",
        "type": "text",
        "required": true,
        "options": [],
        "validation": {}
      },
      {
        "field_name": "resume_file",
        "question": "Upload Resume (PDF)",
        "type": "file",
        "required": true,
        "options": [],
        "validation": {
          "accept": [".pdf"]
        }
      }
    ],
    "additional_data": {},
    "submitted_at": ""
  }
}

Return one JSON object only.
"""


# ============================================================
# EXTRACT JSON FROM MODEL RESPONSE
# ============================================================

def extract_json(response_text):

    if isinstance(response_text, list):
        response_text = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in response_text
        )

    if not isinstance(response_text, str):
        raise ValueError(
            "Model returned an invalid response."
        )

    response_text = response_text.strip()

    response_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        response_text,
        flags=re.IGNORECASE
    )

    response_text = re.sub(
        r"\s*```$",
        "",
        response_text
    )

    try:
        return json.loads(response_text)

    except json.JSONDecodeError:

        start = response_text.find("{")
        end = response_text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "The AI did not return valid JSON."
            )

        try:
            return json.loads(
                response_text[start:end + 1]
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                f"AI returned invalid JSON: {error}"
            )


# ============================================================
# BUILD CONVERSATION MESSAGES
# ============================================================

def build_conversation_messages(conversation):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ]

    for item in conversation[-40:]:

        role = item.get("role")
        content = item.get("content", "")

        if not isinstance(content, str):
            continue

        if role == "user":
            messages.append(
                HumanMessage(content=content)
            )

        elif role == "assistant":
            messages.append(
                AIMessage(content=content)
            )

    return messages


# ============================================================
# VALIDATE AI RESPONSE
# ============================================================

def validate_ai_response(result):

    if not isinstance(result, dict):
        raise ValueError(
            "AI response must be a JSON object."
        )

    action = result.get("action")

    # --------------------------------------------------------
    # NORMAL CONVERSATION ANSWER
    # --------------------------------------------------------

    if action == "answer":

        message = result.get("message")

        if not isinstance(message, str) or not message.strip():
            raise ValueError(
                "AI returned an empty conversational answer."
            )

        return result

    # --------------------------------------------------------
    # JOB POST AND APPLICATION FORM DRAFT
    # --------------------------------------------------------

    if action != "draft":
        raise ValueError(
            "AI returned an unsupported action."
        )

    job_post = result.get("job_post")
    application_form = result.get("application_form")

    if not isinstance(job_post, dict):
        raise ValueError(
            "AI did not return a valid job post."
        )

    if not isinstance(application_form, dict):
        raise ValueError(
            "AI did not return a valid application form."
        )

    # Validate job description
    job_description = job_post.get("job_description")

    if (
        not isinstance(job_description, str)
        or not job_description.strip()
    ):
        raise ValueError(
            "AI response must contain a valid job_description."
        )

    # Validate job title
    job_title = job_post.get("job_title")

    if (
        not isinstance(job_title, str)
        or not job_title.strip()
    ):
        raise ValueError(
            "AI response must contain a valid job_title."
        )

    questions = application_form.get("questions")

    if not isinstance(questions, list) or not questions:
        raise ValueError(
            "Application form questions must be a non-empty list."
        )

    # Standard applicant fields
    required_fields = {
        "full_name",
        "email",
        "phone",
        "resume_file"
    }

    returned_fields = set()

    allowed_types = {
        "text",
        "email",
        "number",
        "yes_no",
        "multiple_choice",
        "dropdown",
        "date",
        "url",
        "file"
    }

    for question in questions:

        if not isinstance(question, dict):
            raise ValueError(
                "Invalid application form question."
            )

        required_keys = {
            "field_name",
            "question",
            "type",
            "required",
            "options",
            "validation"
        }

        missing_keys = required_keys - question.keys()

        if missing_keys:
            raise ValueError(
                "Application question is missing fields: "
                + ", ".join(sorted(missing_keys))
            )

        field_name = question["field_name"]
        question_text = question["question"]
        question_type = question["type"]

        if (
            not isinstance(field_name, str)
            or not field_name.strip()
        ):
            raise ValueError(
                "Every question must have a valid field_name."
            )

        if field_name in returned_fields:
            raise ValueError(
                f"Duplicate application field: {field_name}"
            )

        returned_fields.add(field_name)

        if (
            not isinstance(question_text, str)
            or not question_text.strip()
        ):
            raise ValueError(
                f"Invalid question text for {field_name}."
            )

        if question_type not in allowed_types:
            raise ValueError(
                f"Unsupported question type: {question_type}"
            )

        if not isinstance(question["required"], bool):
            raise ValueError(
                f"Invalid required value for {field_name}."
            )

        if not isinstance(question["options"], list):
            raise ValueError(
                f"Options must be a list for {field_name}."
            )

        if not isinstance(question["validation"], dict):
            raise ValueError(
                f"Validation must be an object for {field_name}."
            )

        if (
            question_type in {"multiple_choice", "dropdown"}
            and not question["options"]
        ):
            raise ValueError(
                f"{question_type} question {field_name} "
                "must contain options."
            )

        if (
            question_type not in {"multiple_choice", "dropdown"}
            and question["options"]
        ):
            raise ValueError(
                f"Question {field_name} must have options: []."
            )

    missing_fields = required_fields - returned_fields

    if missing_fields:
        raise ValueError(
            "Application form is missing standard questions: "
            + ", ".join(sorted(missing_fields))
        )

    return result


# ============================================================
# GENERATE AI RESPONSE
# ============================================================

def generate_ai_response(conversation):

    llm = ChatOpenAI(
        model=BEDROCK_MODEL,
        base_url=BEDROCK_BASE_URL,
        api_key=BEDROCK_API_KEY,
        temperature=0.2,
        timeout=600,
        max_retries=1
    )

    response = llm.invoke(
        build_conversation_messages(conversation)
    )



    result = extract_json(response.content)



    result = validate_ai_response(result)

    return result