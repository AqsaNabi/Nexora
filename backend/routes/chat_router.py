
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from backend.services.chat_service import ChatService

from backend.services.google_form_service import (
    create_google_form_from_json
)

from backend.services.google_watch_service import (
    create_response_watch
)

from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
)

from backend.repository.recruitment_repository import (
    create_recruitment_post,
    save_recruitment_metadata
)


router = APIRouter()
active_sessions = {}


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):

    await websocket.accept()

    if session_id not in active_sessions:
        active_sessions[session_id] = ChatService()

    chat_service = active_sessions[session_id]

    await websocket.send_json({
        "type": "connected",
        "message": "WebSocket connected successfully."
    })

    # ========================================================
    # RESET CREATION STATE
    # ========================================================

    def reset_creation_state():

        chat_service.job_post_approved = False
        chat_service.application_form_approved = False

        chat_service.created_post_id = None
        chat_service.created_form_id = None
        chat_service.created_form_url = None

        chat_service.question_mapping = None
        chat_service.approved_payload = None

        chat_service.recruitment_metadata_saved = False
        chat_service.response_watch_created = False
        chat_service.form_creation_in_progress = False

    # ========================================================
    # SAVE EDITED DRAFTS
    # ========================================================

    def save_edited_drafts(raw_job_post, raw_application_form):

        if not isinstance(raw_job_post, dict):
            raise ValueError("Job post must be a JSON object.")

        if not isinstance(raw_application_form, dict):
            raise ValueError("Application form must be a JSON object.")

        job_post = prepare_job_post(raw_job_post)

        application_form = prepare_application_form(
            raw_application_form
        )

        # Remove only the old file-upload question.
        # Preserve resume_link and other URL questions.

        application_form["questions"] = [
            question
            for question in application_form.get("questions", [])
            if question.get("type", "").lower() != "file"
            and question.get("field_name") != "resume_file"
            and "upload resume" not in question.get(
                "question", ""
            ).lower()
        ]

        chat_service.current_job_post = job_post
        chat_service.current_application_form = application_form

        reset_creation_state()

    # ========================================================
    # CREATE RECRUITMENT POST AND GOOGLE FORM
    # ========================================================

    async def create_form_if_approved():

        if not chat_service.current_job_post:
            raise ValueError("Job post data is missing.")

        if not chat_service.current_application_form:
            raise ValueError("Application form data is missing.")

        job_title = chat_service.current_job_post.get("job_title")

        job_description = chat_service.current_job_post.get(
            "job_description"
        )

        if not job_title or not job_description:
            raise ValueError(
                "Job title or job description is missing."
            )

        # Prevent duplicate creation within this session.
        if (
            chat_service.created_post_id
            and chat_service.created_form_id
            and chat_service.recruitment_metadata_saved
            and chat_service.response_watch_created
        ):

            return {
                "post_id": chat_service.created_post_id,
                "form_id": chat_service.created_form_id,
                "form_url": chat_service.created_form_url,
                "question_mapping": chat_service.question_mapping or {}
            }

        if chat_service.form_creation_in_progress:
            raise ValueError(
                "Form creation is already in progress."
            )

        chat_service.form_creation_in_progress = True

        try:

            # ------------------------------------------------
            # STEP 1: SAVE RECRUITMENT POST
            # ------------------------------------------------

            if not chat_service.created_post_id:

                chat_service.created_post_id = await run_in_threadpool(
                    create_recruitment_post,
                    job_title,
                    job_description
                )

            # ------------------------------------------------
            # STEP 2: CREATE GOOGLE FORM
            # ------------------------------------------------

            if not chat_service.created_form_id:

                # IMPORTANT:
                # google_form_service expects BOTH objects
                # inside one dictionary.

                approved_data = {
                    "job_post": chat_service.current_job_post,
                    "application_form": chat_service.current_application_form
                }

                result = await run_in_threadpool(
                    create_google_form_from_json,
                    approved_data
                )

                if not result or not result.get("form_id"):
                    raise ValueError(
                        "Google Form creation failed."
                    )

                chat_service.created_form_id = result.get("form_id")

                chat_service.created_form_url = result.get(
                    "form_url"
                )

                chat_service.question_mapping = result.get(
                    "question_mapping", {}
                )

            # ------------------------------------------------
            # STEP 3: SAVE RECRUITMENT METADATA
            # ------------------------------------------------

            if not chat_service.recruitment_metadata_saved:

                await run_in_threadpool(
                    save_recruitment_metadata,
                    chat_service.created_post_id,
                    chat_service.created_form_id,
                    chat_service.created_form_url,
                    None,
                    chat_service.question_mapping,
                    chat_service.current_application_form
                )

                chat_service.recruitment_metadata_saved = True

            # ------------------------------------------------
            # STEP 4: CREATE GOOGLE FORMS RESPONSE WATCH
            # ------------------------------------------------

            if not chat_service.response_watch_created:

                await run_in_threadpool(
                    create_response_watch,
                    chat_service.created_form_id
                )

                chat_service.response_watch_created = True

            # ------------------------------------------------
            # STEP 5: RETURN FINAL RESULT
            # ------------------------------------------------

            return {
                "post_id": chat_service.created_post_id,
                "form_id": chat_service.created_form_id,
                "form_url": chat_service.created_form_url,
                "question_mapping": chat_service.question_mapping or {},
                "skipped_questions": []
            }

        finally:

            chat_service.form_creation_in_progress = False

    # ========================================================
    # SEND APPROVAL RESPONSE TO FRONTEND
    # ========================================================

    async def send_approval_response(result):

        await websocket.send_json({
            "type": "approval",
            "message": (
                "Recruitment post and Google Form "
                "created successfully."
            ),
            "post_id": result.get("post_id"),
            "form_id": result.get("form_id"),
            "form_url": result.get("form_url"),
            "question_mapping": result.get(
                "question_mapping", {}
            ),
            "skipped_questions": result.get(
                "skipped_questions", []
            )
        })

    # ========================================================
    # WEBSOCKET EVENT HANDLING
    # ========================================================

    try:

        while True:

            data = await websocket.receive_json()

            event_type = data.get("type")

            # =================================================
            # 1. NORMAL CHAT MESSAGE
            # =================================================

            if event_type == "message":

                try:

                    message = data.get("message", "")

                    if (
                        not isinstance(message, str)
                        or not message.strip()
                    ):
                        raise ValueError(
                            "Please enter a message."
                        )

                    response = await run_in_threadpool(
                        chat_service.process_message,
                        message
                    )

                    await websocket.send_json({
                        "type": "response",
                        "data": response
                    })

                except Exception as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # =================================================
            # 2. UPDATE EDITED DRAFTS
            # =================================================

            elif event_type == "update_drafts":

                try:

                    save_edited_drafts(
                        data.get("job_post", {}),
                        data.get("application_form", {})
                    )

                    await websocket.send_json({
                        "type": "drafts_updated",
                        "message": (
                            "Both edited drafts saved successfully."
                        )
                    })

                except Exception as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # =================================================
            # 3. APPROVE BOTH DRAFTS
            # =================================================

            elif event_type == "approve":

                try:

                    raw_job_post = data.get("job_post", {})

                    raw_application_form = data.get(
                        "application_form", {}
                    )

                    if not isinstance(raw_job_post, dict):
                        raise ValueError("Invalid job post.")

                    if not isinstance(raw_application_form, dict):
                        raise ValueError(
                            "Invalid application form."
                        )

                    job_post = prepare_job_post(raw_job_post)

                    application_form = prepare_application_form(
                        raw_application_form
                    )

                    # Preserve resume_link and other URL questions.

                    application_form["questions"] = [
                        question
                        for question in application_form.get(
                            "questions", []
                        )
                        if question.get("type", "").lower() != "file"
                        and question.get("field_name") != "resume_file"
                        and "upload resume" not in question.get(
                            "question", ""
                        ).lower()
                    ]

                    drafts_changed = (
                        job_post != chat_service.current_job_post
                        or application_form
                        != chat_service.current_application_form
                    )

                    if drafts_changed:

                        chat_service.current_job_post = job_post

                        chat_service.current_application_form = (
                            application_form
                        )

                        reset_creation_state()

                    chat_service.job_post_approved = True

                    chat_service.application_form_approved = True

                    result = await create_form_if_approved()

                    if result:
                        await send_approval_response(result)

                except Exception as error:

                    import traceback
                    traceback.print_exc()

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # =================================================
            # 4. APPROVE JOB POST ONLY
            # =================================================

            elif event_type == "approve_job_post":

                if not chat_service.current_job_post:

                    await websocket.send_json({
                        "type": "error",
                        "message": "No job post is available."
                    })

                    continue

                chat_service.job_post_approved = True

                if chat_service.application_form_approved:

                    try:

                        result = await create_form_if_approved()

                        if result:
                            await send_approval_response(result)

                    except Exception as error:

                        import traceback
                        traceback.print_exc()

                        await websocket.send_json({
                            "type": "error",
                            "message": str(error)
                        })

                else:

                    await websocket.send_json({
                        "type": "approval",
                        "job_post_approved": True,
                        "application_form_approved": False
                    })

            # =================================================
            # 5. APPROVE APPLICATION FORM ONLY
            # =================================================

            elif event_type == "approve_application_form":

                if not chat_service.current_application_form:

                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            "No application form is available."
                        )
                    })

                    continue

                chat_service.application_form_approved = True

                if chat_service.job_post_approved:

                    try:

                        result = await create_form_if_approved()

                        if result:
                            await send_approval_response(result)

                    except Exception as error:

                        import traceback
                        traceback.print_exc()

                        await websocket.send_json({
                            "type": "error",
                            "message": str(error)
                        })

                else:

                    await websocket.send_json({
                        "type": "approval",
                        "job_post_approved": False,
                        "application_form_approved": True
                    })

            # =================================================
            # 6. RESET CONVERSATION
            # =================================================

            elif event_type == "reset":

                active_sessions[session_id] = ChatService()

                chat_service = active_sessions[session_id]

                await websocket.send_json({
                    "type": "reset",
                    "message": "Conversation reset successfully."
                })

            # =================================================
            # 7. UNKNOWN EVENT
            # =================================================

            else:

                await websocket.send_json({
                    "type": "error",
                    "message": "Unsupported WebSocket event."
                })

    except WebSocketDisconnect:

        print(f"HR disconnected: {session_id}")

    except Exception as error:

        import traceback
        traceback.print_exc()

        print(
            f"WebSocket error for session {session_id}: {error}"
        )
