
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# =====================================================
# BEDROCK CLIENT
# =====================================================

client = OpenAI(
    api_key=os.getenv("BEDROCK_API_KEY"),
    base_url=os.getenv("BEDROCK_BASE_URL")
)


# =====================================================
# BEDROCK LLM FUNCTION
# =====================================================

def call_bedrock(system_prompt: str, user_prompt: str):

    model_id = os.getenv("BEDROCK_MODEL")

    if not model_id:
        raise ValueError("BEDROCK_MODEL is missing in .env")

    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.7,
        max_tokens=1500
    )

    return response.choices[0].message.content.strip()


# =====================================================
# GENERATE ANNOUNCEMENT
# =====================================================

def generate_announcement(
    prompt: str,
    designation: str
):

    system_prompt = """
You are an intelligent HR announcement generation agent.

Generate attractive, professional, engaging and clear
company announcements.

Requirements:

1. Use a professional and engaging tone.
2. Address the selected audience appropriately.
3. Include the details provided by HR.
4. Create an attractive announcement title.
5. Use appropriate emojis when useful.
6. Include a clear call to action.
7. Do not invent dates, locations, links or event information.
8. Use only the information provided.
9. Do not add unsupported details.

Return the announcement in this format:

TITLE:
ANNOUNCEMENT:

Return the complete announcement suitable for an HR email.
"""

    user_prompt = f"""
Selected audience:
{designation}

HR prompt:
{prompt}

Generate the announcement.
"""

    return call_bedrock(system_prompt, user_prompt)


# =====================================================
# MODIFY ANNOUNCEMENT
# =====================================================

def modify_announcement(
    announcement: str,
    modification_prompt: str,
    designation: str
):

    system_prompt = """
You are an HR announcement modification agent.

Modify the existing announcement according
to HR's instructions.

Requirements:

1. Preserve existing important details.
2. Apply the requested modifications.
3. Keep the announcement professional.
4. Keep the announcement engaging.
5. Never invent missing information.
6. Do not remove important details unless
   HR explicitly requests it.
7. Return the complete revised announcement.

Return:

TITLE:
ANNOUNCEMENT:
"""

    user_prompt = f"""
Selected audience:
{designation}

Existing announcement:
{announcement}

HR modification instructions:
{modification_prompt}

Generate the revised announcement.
"""

    return call_bedrock(system_prompt, user_prompt)
