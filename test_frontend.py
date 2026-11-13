
import json
from urllib import response
import uuid
import os
import sys

import streamlit as st
import websocket


# Add this near the beginning of your Streamlit frontend file,
# after the imports and before displaying the page.

st.markdown("""
<style>

/* Main application background */
.stApp {
    background-color: #F7F5FF;
    color: #eef1f6;
}

/* Main content area */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1100px;
}

/* Headings */
h1, h2, h3, h4 {
    color: #26334A !important;
    font-weight: 700 !important;
}

/* General text */
.stMarkdown p,
.stMarkdown li,
.stMarkdown span,
.stMarkdown label {
    color: #26334A !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background-color: #FFFFFF;
    border: 1px solid #E5DDF8;
    border-radius: 14px;
    padding: 16px;
    color: #26334A !important;
}

/* Input fields */
.stTextInput input,
.stTextArea textarea {
    background-color: #FFFFFF !important;
    color: #26334A !important;
    border: 1px solid #CFC3EF !important;
    border-radius: 10px !important;
}

/* Input placeholders */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #7B8497 !important;
}

/* Buttons */
.stButton button {
    background-color: #7655D9 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.2rem !important;
}

/* Button hover */
.stButton button:hover {
    background-color: #6240C4 !important;
    color: #FFFFFF !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background-color: #FFFFFF;
    border: 1px solid #E5DDF8;
    border-radius: 12px;
}

/* Code boxes */
[data-testid="stCode"] {
    background-color: #F0ECFA !important;
    border-radius: 10px;
}

/* Dividers */
hr {
    border-color: #E2DCF0 !important;
}

/* Captions */
.stCaption {
    color: #64748B !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #F0ECFA;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/chat"
REQUEST_TIMEOUT = 600


# ============================================================
# STYLING
# ============================================================

def apply_styling():

    st.markdown(
        """
        <style>

        .stApp {
            background-color: #f4f7fb;
        }

        .block-container {
            max-width: 1250px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: #183B66 !important;
            font-weight: 750 !important;
        }

        hr {
            border-color: #dce5f0 !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                #142D4E 0%,
                #203F68 55%,
                #352D68 100%
            ) !important;

            border-right: 1px solid #304f78 !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stMarkdown {
            color: white !important;
        }

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
            color: #c6d5eb !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.22) !important;
        }

        [data-testid="stSidebar"] div.stButton > button {
            width: 100%;
            min-height: 44px;

            background: linear-gradient(
                135deg,
                #526FE8,
                #7656CE
            ) !important;

            color: white !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 11px !important;
            font-weight: 650 !important;
        }

        div.stButton > button {
            min-height: 44px;
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid #dce4ef;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(
                135deg,
                #526FE8,
                #7656CE
            ) !important;

            border: 1px solid #526FE8 !important;
            color: white !important;
        }

        div[data-testid="stChatInput"] {
            border-radius: 12px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SESSION STATE
# ============================================================
def initialize_session_state():
    defaults = {
        "session_id": str(uuid.uuid4()),
        "chat_messages": [],
        "current_job_post": {},
        "current_application_form": {},
        "is_approved": False,
        "google_form_url": None,
        "google_form_id": None,
        "recruitment_post_id": None,
        "pending_message": None,
        "page": "job_post_generator"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
# ============================================================
# WEBSOCKET COMMUNICATION
# ============================================================


def send_websocket_event(event):

    ws = None

    try:
        session_id = st.session_state.session_id
        ws_url = f"{WEBSOCKET_URL}/{session_id}"

        st.write("DEBUG: Connecting to backend...")

        ws = websocket.create_connection(
            ws_url,
            timeout=REQUEST_TIMEOUT
        )

        connection_message = json.loads(ws.recv())

        st.write("DEBUG: Connection:", connection_message)

        if connection_message.get("type") != "connected":
            st.error(f"Unexpected connection response: {connection_message}")
            return None

        st.write("DEBUG: Sending event:", event)

        ws.send(json.dumps(event))

        st.write("DEBUG: Waiting for backend response...")

        raw_response = ws.recv()
        response = json.loads(raw_response)

        st.write("DEBUG: Backend response received:")
        st.json(response)

        return response

    except websocket.WebSocketTimeoutException:
        st.error("The AI response timed out. Please try again.")

    except websocket.WebSocketException as error:
        st.error(f"WebSocket connection error: {error}")

    except json.JSONDecodeError:
        st.error("The backend returned an invalid JSON response.")

    except Exception as error:
        st.error(f"Something went wrong: {error}")

    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

    return None

# ============================================================
# UPDATE GENERATED DRAFTS
# ============================================================

def update_drafts_from_response(response):

    data = response.get("data", response)

    if not isinstance(data, dict):
        return

    job_post = data.get("job_post")
    application_form = data.get("application_form")

    if (
        isinstance(job_post, dict)
        and isinstance(application_form, dict)
    ):

        st.session_state.current_job_post = job_post

        st.session_state.current_application_form = (
            application_form
        )

        # A new draft requires fresh approval.
        st.session_state.is_approved = False

        st.session_state.google_form_url = None
        st.session_state.google_form_id = None
        st.session_state.recruitment_post_id = None


# ============================================================
# SEND MESSAGE
# ============================================================

def send_message(message):
    message = message.strip()

    if not message:
        return

    st.session_state.chat_messages.append({
        "role": "user",
        "content": message
    })

    st.session_state.pending_message = message
    st.rerun()


# ============================================================
# PROCESS PENDING MESSAGE
# ============================================================


def process_pending_message():

    st.write("DEBUG 1: process_pending_message started")

    message = st.session_state.get("pending_message")

    st.write("DEBUG 2: Pending message:", message)

    if not message:
        return

    st.session_state.pending_message = None

    with st.spinner("Generating job post..."):

        st.write("DEBUG 3: Calling WebSocket")

        response = send_websocket_event({
            "type": "message",
            "message": message
        })

        st.write("DEBUG 4: WebSocket returned")

        if response is None:
            st.error("No response received from backend.")
            return

        st.write("DEBUG 5: Response:")
        st.json(response)

        if response.get("type") == "error":
            st.error(response.get("message", "Backend error"))
            return

        data = response.get("data", response)

        if not isinstance(data, dict):
            st.error("Invalid backend response format.")
            return

        st.write("DEBUG 6: Action:", data.get("action"))

        if data.get("action") == "draft":
            update_drafts_from_response(data)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": data.get("message", "Job post generated.")
            })
        else:
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": data.get("message", "Response received.")
            })

    st.rerun()


# ============================================================
# APPROVE JOB POST AND APPLICATION FORM
# ============================================================

def approve_both_drafts():

    if not st.session_state.current_job_post:

        st.warning(
            "Please generate a job post before approving."
        )

        return

    if not st.session_state.current_application_form:

        st.warning(
            "Please generate an application form before approving."
        )

        return

    with st.spinner(
        "Creating recruitment post and Google Form..."
    ):

        response = send_websocket_event({
            "type": "approve",
            "job_post": st.session_state.current_job_post,
            "application_form": (
                st.session_state.current_application_form
            )
        })

    if not response:
        return

    if response.get("type") == "error":

        st.error(
            response.get(
                "message",
                "Approval failed."
            )
        )

        return

    if response.get("type") in ["approval", "approved"]:

        st.session_state.is_approved = True

        st.session_state.google_form_url = (
            response.get("form_url")
            or response.get("google_form_url")
            or response.get("created_form_url")
        )

        st.session_state.google_form_id = (
            response.get("form_id")
            or response.get("created_form_id")
        )

        st.session_state.recruitment_post_id = (
            response.get("post_id")
            or response.get("created_post_id")
        )

        st.rerun()

    st.error(
        response.get(
            "message",
            "The backend did not confirm approval."
        )
    )


# ============================================================
# START NEW JOB POST
# ============================================================

def start_new_job_post():

    st.session_state.session_id = str(uuid.uuid4())

    st.session_state.chat_messages = []

    st.session_state.current_job_post = {}

    st.session_state.current_application_form = {}

    st.session_state.is_approved = False

    st.session_state.google_form_url = None
    st.session_state.google_form_id = None
    st.session_state.recruitment_post_id = None

    st.session_state.pending_message = None

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def display_sidebar():

    with st.sidebar:

        st.markdown("## HELLO HR!")

        st.caption("HR Department")

        st.divider()

        if st.button(
            "← Back to Main Dashboard",
            key="back_to_dashboard",
            use_container_width=True
        ):

            st.session_state.page = "dashboard"

            st.rerun()

        st.divider()

        st.markdown("### Form Link Generator")

        if st.button(
            "＋ Start New Job Post",
            key="sidebar_new_job",
            use_container_width=True
        ):

            start_new_job_post()


# ============================================================
# CHAT DISPLAY
# ============================================================

def display_chat_messages():

    for message in st.session_state.chat_messages:

        role = message.get("role", "assistant")

        content = message.get("content", "")

        if role not in ["user", "assistant"]:
            continue

        if not content:
            continue

        with st.chat_message(role):

            st.markdown(content)


# ============================================================
# WELCOME SECTION
# ============================================================

def display_welcome_section():

    if st.session_state.chat_messages:
        return

    _, center_content, _ = st.columns([1, 5, 1])

    with center_content:

        st.markdown(
            """
            <h3 style='text-align:center; color:#526FE8;'>
                Let's Get Started!
            </h3>

            <h2 style='text-align:center; color:#183B66;'>
                Your hiring journey starts here.
            </h2>

            <p style="
                text-align:center;
                color:#64748B;
                font-size:16px;
                line-height:1.8;
            ">
                Tell us about the position you're hiring for.
                We'll help you create a professional job
                description and candidate application form.
            </p>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# HUMAN-READABLE JOB POST PREVIEW
# ============================================================

def display_job_post():

    job_post = st.session_state.current_job_post

    if not job_post:
        return

    st.subheader("Job Description")

    if job_post.get("job_title"):

        st.markdown(f"### {job_post['job_title']}")

    fields = [
        ("Department", "department"),
        ("Location", "location"),
        ("Work Mode", "work_mode"),
        ("Employment Type", "employment_type"),
        ("Experience", "experience"),
        ("Salary Range", "salary_range"),
        ("Role Summary", "role_summary"),
        ("Job Description", "job_description"),
        ("Responsibilities", "responsibilities"),
        ("Required Skills", "required_skills"),
        ("Preferred Skills", "preferred_skills"),
        ("Education", "education"),
        ("Benefits", "benefits"),
        ("Application Instructions", "application_instructions")
    ]

    for label, key in fields:

        value = job_post.get(key)

        if not value:
            continue

        st.markdown(f"**{label}**")

        if isinstance(value, list):

            for item in value:
                st.markdown(f"- {item}")

        else:

            st.write(value)


# ============================================================
# HUMAN-READABLE APPLICATION FORM PREVIEW
# ============================================================

def display_application_form():

    application_form = (
        st.session_state.current_application_form
    )

    if not application_form:
        return

    st.subheader("Application Form")

    form_title = application_form.get("form_title")

    if form_title:

        st.markdown(f"### {form_title}")

    questions = application_form.get("questions", [])

    if not isinstance(questions, list):
        st.warning("The generated application questions are invalid.")
        return

    for index, question in enumerate(
        questions,
        start=1
    ):

        if not isinstance(question, dict):
            continue

        with st.container(border=True):

            question_text = question.get(
                "question",
                question.get("field_name", "")
            )

            st.markdown(
                f"**{index}. {question_text}**"
            )

            field_type = question.get("type", "text")

            st.caption(
                f"Answer type: {field_type.replace('_', ' ').title()}"
            )

            if question.get("required"):

                st.caption("Required")

            options = question.get("options", [])

            if options:

                st.caption(
                    "Options: " + ", ".join(map(str, options))
                )


# ============================================================
# GENERATED CONTENT AND APPROVAL
# ============================================================

def display_review_section():

    job_post = st.session_state.current_job_post

    application_form = (
        st.session_state.current_application_form
    )

    if not job_post or not application_form:
        return

    st.divider()

    st.header("Review Your Recruitment Content")

    with st.expander(
        "Job Description",
        expanded=True
    ):

        display_job_post()

    with st.expander(
        "Application Form",
        expanded=True
    ):

        display_application_form()

    st.divider()

    if st.session_state.is_approved:

        st.success(
            "The job post and application form have "
            "been approved successfully."
        )

        if st.session_state.recruitment_post_id:

            st.write(
                "Recruitment Post ID: "
                f"{st.session_state.recruitment_post_id}"
            )

        if st.session_state.google_form_url:

            st.subheader("Candidate Application Link")

            st.markdown(
                f"[Open Google Application Form]"
                f"({st.session_state.google_form_url})"
            )

            st.code(
                st.session_state.google_form_url,
                language=None
            )

        else:

            st.warning(
                "Approval was confirmed, but the backend "
                "did not return a Google Form URL."
            )

        return

    st.subheader("Final Approval")

    st.write(
        "Review both sections above. Once everything "
        "is correct, approve them to create the recruitment "
        "post and candidate application form."
    )

    if st.button(
        "Approve Job Post & Application Form",
        type="primary",
        use_container_width=True
    ):

        approve_both_drafts()


# ============================================================
# MAIN CHATBOT PAGE
# ============================================================


def job_post_generator():

    # 1. Initialize Streamlit session state
    initialize_session_state()

    # 2. Apply existing styling
    apply_styling()

    # 3. Display sidebar
    display_sidebar()

    st.title("Nexora HR Job Post Generator")
    st.caption("AI-powered job post and application form generator")
    st.divider()

    st.write("DEBUG: Job post generator started")

    # 4. Process pending user message BEFORE displaying chat
    process_pending_message()

    st.write("DEBUG: Pending message processing completed")

    # 5. Display welcome message
    display_welcome_section()

    # 6. Display conversation messages
    display_chat_messages()

    # 7. Display generated job post and application form
    display_review_section()

    # 8. Accept new user input
    if not st.session_state.is_approved:

        user_message = st.chat_input(
            "Describe the job position you want to create..."
        )

        if user_message:
            send_message(user_message)

    else:
        st.success("Job post and application form approved.")

        if st.session_state.google_form_url:
            st.markdown("### Google Application Form")

            st.link_button(
                "Open Google Form",
                st.session_state.google_form_url
            )


# Run application
if __name__ == "__main__":
    job_post_generator()
