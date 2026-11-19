
import json

from backend.services.ai_service import generate_ai_response

from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
)


class ChatService:

    def __init__(self):

        # Conversation history
        self.conversation = []

        # Current generated drafts
        self.current_job_post = None
        self.current_application_form = None

        # Approval status
        self.job_post_approved = False
        self.application_form_approved = False

        # Recruitment post and Google Form details
        self.created_post_id = None
        self.created_form_id = None
        self.created_form_url = None

        # Google Form question mapping
        self.question_mapping = None

        # Approved recruitment data
        self.approved_payload = None

        # Creation status
        self.form_creation_in_progress = False
        self.recruitment_metadata_saved = False
        self.response_watch_created = False

    # ========================================================
    # RESET APPROVAL AND CREATION STATUS
    # ========================================================

    def reset_creation_status(self):

        self.job_post_approved = False
        self.application_form_approved = False

        self.created_post_id = None
        self.created_form_id = None
        self.created_form_url = None

        self.question_mapping = None
        self.approved_payload = None

        self.form_creation_in_progress = False
        self.recruitment_metadata_saved = False
        self.response_watch_created = False

    # ========================================================
    # PROCESS USER MESSAGE
    # ========================================================

    def process_message(self, user_message):

        if not isinstance(user_message, str):
            raise ValueError("Message must be text.")

        user_message = user_message.strip()

        if not user_message:
            raise ValueError("Message cannot be empty.")

        # Save the user's message in conversation history.
        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        # Generate AI response.
        try:

            ai_response = generate_ai_response(
                self.conversation
            )

        except Exception:
            # Remove the message if AI generation failed.
            self.conversation.pop()
            raise

        action = ai_response.get("action")

        # ====================================================
        # 1. NORMAL CONVERSATIONAL ANSWER
        # ====================================================

        if action == "answer":

            answer = (
                ai_response.get("answer")
                or ai_response.get("message")
            )

            if not isinstance(answer, str) or not answer.strip():

                self.conversation.pop()

                raise ValueError(
                    "AI returned an empty answer."
                )

            # Save AI response in conversation history.
            self.conversation.append({
                "role": "assistant",
                "content": json.dumps(
                    ai_response,
                    ensure_ascii=False
                )
            })

            # Do not clear existing drafts or approvals
            # for an ordinary conversational question.
            return {
                "action": "answer",
                "answer": answer,
                "message": answer
            }

        # ====================================================
        # 2. JOB POST AND APPLICATION FORM DRAFT
        # ====================================================

        if action == "draft":

            job_post = prepare_job_post(
                ai_response.get("job_post", {})
            )

            application_form = prepare_application_form(
                ai_response.get("application_form", {})
            )

            # Both drafts must be available.
            if not job_post or not application_form:

                self.conversation.pop()

                raise ValueError(
                    "AI did not generate both required drafts."
                )

            if not job_post.get("job_description"):

                self.conversation.pop()

                raise ValueError(
                    "Generated job description is empty."
                )

            if not application_form.get("questions"):

                self.conversation.pop()

                raise ValueError(
                    "Generated application form has no questions."
                )

            # Store the newly generated drafts.
            self.current_job_post = job_post

            self.current_application_form = application_form

            # Reset previous approval and creation details.
            self.reset_creation_status()

            # Save AI response in conversation history.
            self.conversation.append({
                "role": "assistant",
                "content": json.dumps(
                    ai_response,
                    ensure_ascii=False
                )
            })

            return {
                "action": "draft",
                "message": (
                    ai_response.get("message")
                    or (
                        "Your job post and application "
                        "form are ready for review."
                    )
                ),
                "job_post": job_post,
                "application_form": application_form,
                "job_post_approved": False,
                "application_form_approved": False
            }

        # ====================================================
        # 3. UNSUPPORTED AI RESPONSE
        # ====================================================

        self.conversation.pop()

        raise ValueError(
            "AI returned an unsupported response action."
        )

    # ========================================================
    # RESET CHAT SESSION
    # ========================================================

    def reset(self):

        self.conversation = []

        self.current_job_post = None
        self.current_application_form = None

        self.reset_creation_status()
