
import json

from backend.services.ai_service import generate_ai_response

from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
)


class ChatService:

    def __init__(self):

        self.conversation = []

        self.current_job_post = None
        self.current_application_form = None

        self.job_post_approved = False
        self.application_form_approved = False


    def process_message(self, user_message):

        self.job_post_approved = False
        self.application_form_approved = False

        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        ai_response = generate_ai_response(self.conversation)

        if ai_response.get("action") != "draft":
            raise ValueError("AI did not generate both drafts.")

        job_post = prepare_job_post(
            ai_response.get("job_post", {})
        )

        application_form = prepare_application_form(
            ai_response.get("application_form", {})
        )

        self.current_job_post = job_post
        self.current_application_form = application_form

        self.conversation.append({
            "role": "assistant",
            "content": json.dumps(ai_response)
        })

        return {
            "type": "draft",
            "message": "Your job post and application form are ready for review.",
            "job_post": job_post,
            "application_form": application_form,
            "job_post_approved": False,
            "application_form_approved": False
        }


    def reset(self):

        self.conversation = []

        self.current_job_post = None
        self.current_application_form = None

        self.job_post_approved = False
        self.application_form_approved = False
