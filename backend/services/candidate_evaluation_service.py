import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_bedrock_client():

    api_key = os.getenv("BEDROCK_API_KEY")
    base_url = os.getenv("BEDROCK_BASE_URL")

    if not api_key or not base_url:
        raise ValueError(
            "BEDROCK_API_KEY or BEDROCK_BASE_URL is missing."
        )

    return OpenAI(
        api_key=api_key,
        base_url=base_url
    )


def evaluate_candidate(
    job_description,
    resume_text,
    application_answers
):

    if not job_description or not resume_text:
        raise ValueError(
            "Job description and resume text are required."
        )

    model = os.getenv(
        "BEDROCK_MODEL",
        "openai.gpt-oss-20b"
    )

    client = get_bedrock_client()

    prompt = f"""
You are an AI recruitment evaluation assistant.

Evaluate the candidate against the job description.

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

APPLICATION ANSWERS:
{json.dumps(application_answers, ensure_ascii=False)}

Evaluate only job-related criteria:

1. Relevant technical and professional skills.
2. Relevant work experience.
3. Education and qualifications where relevant.
4. Relevant projects and achievements.
5. Quality and relevance of application answers.

Award points only for evidence in the resume or answers.
Do not consider age, gender, religion, ethnicity,
photographs, or other protected personal characteristics.
Do not automatically reject candidates.

Return only a JSON object.

Do not explain your reasoning.
Do not include any additional text.

Required format:
{{"candidate_score": 85}}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=1000
    )

    choice = response.choices[0]
    message = choice.message

    if choice.finish_reason == "length":
        raise ValueError(
            "Model response was truncated. Increase max_tokens."
        )

    response_text = message.content

    if not response_text:
        raise ValueError(
            f"Model returned no final answer. Message: {message}"
        )

    response_text = response_text.strip()

   

    response_text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        response_text,
        flags=re.IGNORECASE
    ).strip()

    result = json.loads(response_text)

    score = result.get("candidate_score")

    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("Model returned an invalid candidate score.")

    score = int(round(score))

    if not 0 <= score <= 100:
        raise ValueError("Candidate score must be between 0 and 100.")

    return score