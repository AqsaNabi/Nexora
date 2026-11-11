
import json

from backend.services.ai_service import generate_ai_response

from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
)


class ChatService:

    def __init__(self):

        self.conversation = []

        self.current_job_post = {}
        self.current_application_form = {}

        self.is_approved = False

        self.approved_payload = None
        self.approved_file = None

    # --------------------------------------------------
    # PROCESS CHAT MESSAGE
    # --------------------------------------------------

    def process_message(self, user_message):

        if self.is_approved:

            return {
                "type": "error",
                "message": (
                    "This job post has already been approved. "
                    "Please start a new job post."
                )
            }

        if not isinstance(user_message, str) or not user_message.strip():

            return {
                "type": "error",
                "message": "Please enter a message."
            }

        user_message = user_message.strip()

        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        try:

            ai_response = generate_ai_response(
                conversation=self.conversation,
                current_job_post=self.current_job_post,
                current_application_form=self.current_application_form
            )

            # ------------------------------------------
            # NORMAL QUESTION
            # ------------------------------------------

            if ai_response.get("action") == "answer":

                answer = ai_response.get(
                    "answer",
                    "I don't know the answer to that."
                )

                self.conversation.append({
                    "role": "assistant",
                    "content": answer
                })

                return {
                    "type": "response",
                    "data": {
                        "action": "answer",
                        "answer": answer
                    }
                }

            # ------------------------------------------
            # GENERATE OR MODIFY DRAFTS
            # ------------------------------------------

            if ai_response.get("action") == "draft":

                job_post = prepare_job_post(
                    ai_response.get("job_post", {})
                )

                application_form = prepare_application_form(
                    ai_response.get("application_form", {})
                )

                self.current_job_post = job_post
                self.current_application_form = application_form

                self.is_approved = False
                self.approved_payload = None
                self.approved_file = None

                assistant_message = ai_response.get(
                    "message",
                    "Both drafts have been generated successfully."
                )

                self.conversation.append({
                    "role": "assistant",
                    "content": (
                        assistant_message
                        + "\n\nUpdated drafts:\n"
                        + json.dumps(
                            {
                                "job_post": job_post,
                                "application_form": application_form
                            },
                            ensure_ascii=False
                        )
                    )
                })

                return {
                    "type": "response",
                    "data": {
                        "action": "draft",
                        "message": assistant_message,
                        "job_post": job_post,
                        "application_form": application_form
                    }
                }

            raise ValueError(
                "Unsupported AI response."
            )

        except Exception as error:

            if self.conversation:
                self.conversation.pop()

            print("CHAT SERVICE ERROR:", str(error))

            return {
                "type": "error",
                "message": str(error)
            }

    # --------------------------------------------------
    # UPDATE DRAFTS FROM FRONTEND JSON EDITOR
    # --------------------------------------------------

    def update_drafts(self, job_post, application_form):

        if self.is_approved:

            raise ValueError(
                "Approved drafts cannot be edited."
            )

        if not isinstance(job_post, dict):

            raise ValueError(
                "Job post must be a JSON object."
            )

        if not isinstance(application_form, dict):

            raise ValueError(
                "Application form must be a JSON object."
            )

        self.current_job_post = prepare_job_post(job_post)

        self.current_application_form = prepare_application_form(
            application_form
        )

        self.is_approved = False
        self.approved_payload = None
        self.approved_file = None

        return {
            "job_post": self.current_job_post,
            "application_form": self.current_application_form
        }

    # --------------------------------------------------
    # APPROVE FINAL DRAFTS
    # --------------------------------------------------

    def approve(self, job_post, application_form, payload, file_path):

        if self.is_approved:

            raise ValueError(
                "This job post has already been approved."
            )

        if not isinstance(job_post, dict):

            raise ValueError(
                "Invalid job post."
            )

        if not isinstance(application_form, dict):

            raise ValueError(
                "Invalid application form."
            )

        self.current_job_post = job_post
        self.current_application_form = application_form

        self.approved_payload = payload
        self.approved_file = file_path

        self.is_approved = True

        return {
            "approved": True,
            "approved_payload": self.approved_payload,
            "saved_file": self.approved_file
        }

    # --------------------------------------------------
    # RESET ACTIVE SESSION
    # --------------------------------------------------

    def reset(self):

        self.conversation = []

        self.current_job_post = {}
        self.current_application_form = {}

        self.is_approved = False

        self.approved_payload = None
        self.approved_file = None
