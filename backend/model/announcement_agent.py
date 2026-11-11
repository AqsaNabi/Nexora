
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from langchain_ollama import ChatOllama

from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


# ==========================================
# INITIALIZE OLLAMA
# ==========================================

llm = ChatOpenAI(
    model="gemma4:31b",
    base_url="https://ollama.com/v1",
    api_key=os.getenv("OLLAMA_API_KEY"),
    temperature=0.7,

    

)


# ==========================================
# GENERATE ANNOUNCEMENT PROMPT
# ==========================================

announcement_prompt = ChatPromptTemplate.from_messages(

    [

        (

            "system",

            """
            You are an intelligent HR announcement
            generation agent.

            Generate attractive, professional,
            engaging and clear company announcements.

            Requirements:

            1. Use a professional and engaging tone.
            2. Address the selected audience correctly.
            3. Include the details provided by HR.
            4. Create an attractive announcement title.
            5. Use appropriate emojis when useful.
            6. Include a clear call to action.
            7. Do not invent dates, locations,
               links or event information.
            8. Use only the information provided.
            9. Do not add unsupported details.

            Audience greetings:

            Managers:
            Dear Managers,

            Team Leaders:
            Dear Team Leaders,

            All Employees:
            Dear Employees,

            Return the announcement in this format:

            TITLE:
            ANNOUNCEMENT:

            Return the complete announcement
            suitable for an HR email.
            """

        ),

        (

            "human",

            """
            Selected audience:
            {designation}

            HR prompt:
            {prompt}

            Generate the announcement.
            """

        )

    ]

)


# ==========================================
# MODIFY ANNOUNCEMENT PROMPT
# ==========================================

modify_prompt = ChatPromptTemplate.from_messages(

    [

        (

            "system",

            """
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

        ),

        (

            "human",

            """
            Selected audience:
            {designation}

            Existing announcement:
            {announcement}

            HR modification instructions:
            {modification_prompt}

            Generate the revised announcement.
            """

        )

    ]

)


# ==========================================
# GENERATE ANNOUNCEMENT
# ==========================================

def generate_announcement(

    prompt: str,

    designation: str

):

    chain = announcement_prompt | llm

    response = chain.invoke(

        {

            "prompt": prompt,

            "designation": designation

        }

    )

    return response.content


# ==========================================
# MODIFY ANNOUNCEMENT
# ==========================================

def modify_announcement(

    announcement: str,

    modification_prompt: str,

    designation: str

):

    chain = modify_prompt | llm

    response = chain.invoke(

        {

            "announcement": announcement,

            "modification_prompt": modification_prompt,

            "designation": designation

        }

    )

    return response.content
