
import json
import re

from langchain_openai import ChatOpenAI

from backend.model.post_gen.config import (
    OLLAMA_API_KEY,
    OLLAMA_API_URL,
    OLLAMA_MODEL
)


# ------------------------------------------------
# 1. INITIALIZE OLLAMA CLOUD MODEL
# ------------------------------------------------

llm = ChatOpenAI(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_API_URL,
    api_key=OLLAMA_API_KEY,
    temperature=0.2,
    timeout=600,
    max_retries=1
)


# ------------------------------------------------
# 2. SYSTEM PROMPT
# ------------------------------------------------

SYSTEM_PROMPT = """
You are an expert HR Job Description and Application Form Generator.

Generate TWO outputs from the HR user's job requirements:

1. A job description.
2. A candidate application form.

IMPORTANT RULES:

- Generate both outputs immediately.
- Do not ask follow-up questions.
- Use only information explicitly provided by the user.
- Never invent company information, salary, benefits,
  qualifications, or experience requirements.
- Leave missing text fields as empty strings.
- Leave missing list fields as empty lists.
- Keep the content professional and clear.
- Do not make optional qualifications mandatory.

JOB DESCRIPTION STRUCTURE:

{
    "job_title": "",
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
}

APPLICATION FORM STRUCTURE:

{
    "form_title": "",
    "questions": [
        {
            "question": "",
            "type": "",
            "required": false,
            "options": []
        }
    ]
}

APPLICATION FORM RULES:

- Include relevant candidate details.
- Include name, email, phone number and relevant
  professional information where appropriate.
- Include role-specific questions.
- Use suitable question types:
  short_answer, paragraph, multiple_choice,
  checkbox and file_upload.
- Use an empty options list when options are unnecessary.
- The required field must always be true or false.
- Do not ask irrelevant questions.

OUTPUT FORMAT:

Return ONLY valid JSON.

Use exactly this outer structure:

{
    "action": "draft",
    "message": "Both drafts have been generated successfully.",
    "job_post": {
        "job_title": "",
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
        "form_title": "",
        "questions": []
    }
}

Do not return Markdown or explanations outside the JSON.
"""


# ------------------------------------------------
# 3. GENERATE AI RESPONSE
# ------------------------------------------------

def generate_ai_response(conversation):

    try:

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        for message in conversation:

            role = message.get("role")

            if role not in ["user", "assistant"]:
                continue

            messages.append({
                "role": role,
                "content": message.get("content", "")
            })

        # Call Ollama Cloud
        response = llm.invoke(messages)

        ai_content = response.content

        # Handle list-based responses
        if isinstance(ai_content, list):

            text_parts = []

            for block in ai_content:

                if isinstance(block, dict):
                    text_parts.append(block.get("text", ""))

                elif isinstance(block, str):
                    text_parts.append(block)

            ai_content = "".join(text_parts)

        if not isinstance(ai_content, str):
            raise ValueError("AI returned an unexpected response format.")

        # Remove Markdown code fences if present
        ai_content = ai_content.strip()

        ai_content = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            ai_content,
            flags=re.IGNORECASE
        ).strip()

        # Parse JSON
        ai_response = json.loads(ai_content)

        if not isinstance(ai_response, dict):
            raise ValueError("AI response must be a JSON object.")

        # Validate required keys
        required_keys = [
            "action",
            "message",
            "job_post",
            "application_form"
        ]

        for key in required_keys:

            if key not in ai_response:
                raise ValueError(
                    f"AI response is missing the '{key}' field."
                )

        if ai_response["action"] != "draft":
            raise ValueError("AI did not generate the drafts correctly.")

        return ai_response

    except Exception as error:

        raise RuntimeError(
            f"Ollama Cloud generation failed: {str(error)}"
        ) from error
