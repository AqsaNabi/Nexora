
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from backend.services.chat_service import ChatService

from backend.services.approved_payload_service import (
    create_approved_payload
)

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
        application_form = prepare_application_form(raw_application_form)

        chat_service.current_job_post = job_post
        chat_service.current_application_form = application_form

        reset_creation_state()

    # ========================================================
    # CREATE RECRUITMENT POST AND GOOGLE FORM
    # ========================================================

    async def create_form_if_approved():

        if not (
            chat_service.job_post_approved
            and chat_service.application_form_approved
        ):
            return None

        if chat_service.form_creation_in_progress:
            raise ValueError("Recruitment form creation is already in progress.")

        chat_service.form_creation_in_progress = True

        try:

            # 1. Prepare approved payload.
            if not chat_service.approved_payload:

                chat_service.approved_payload = create_approved_payload(
                    session_id,
                    chat_service.current_job_post,
                    chat_service.current_application_form
                )

            payload = chat_service.approved_payload
            job_post = payload["job_post"]

            job_description = job_post.get("job_description", "")

            if not job_description.strip():
                raise ValueError("Job description cannot be empty.")

            # 2. Save recruitment post.
            if not chat_service.created_post_id:

                chat_service.created_post_id = await run_in_threadpool(
                    create_recruitment_post,
                    job_description
                )

            # 3. Create Google Form.
            if not chat_service.created_form_id:

                result = await run_in_threadpool(
                    create_google_form_from_json,
                    payload
                )

                chat_service.created_form_id = result["form_id"]
                chat_service.created_form_url = result["form_url"]
                chat_service.question_mapping = result["question_mapping"]

            # 4. Validate IDs before saving metadata.
            if not chat_service.created_post_id:
                raise ValueError("Recruitment post ID is missing.")

            if not chat_service.created_form_id:
                raise ValueError("Google Form ID is missing.")

            if not chat_service.created_form_url:
                raise ValueError("Google Form URL is missing.")

            # 5. Save complete Google Form metadata.
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

            # 6. Create response notification watch.
            if not chat_service.response_watch_created:

                await run_in_threadpool(
                    create_response_watch,
                    chat_service.created_form_id
                )

                chat_service.response_watch_created = True

            # 7. Return final response.
            return {
                "type": "approved",
                "message": "Recruitment post and Google Form created successfully.",
                "session_id": session_id,
                "post_id": chat_service.created_post_id,
                "form_id": chat_service.created_form_id,
                "form_url": chat_service.created_form_url,
                "question_mapping": chat_service.question_mapping,
                "approved_payload": payload
            }

        finally:
            chat_service.form_creation_in_progress = False

    # ========================================================
    # WEBSOCKET EVENT HANDLING
    # ========================================================

    try:

        while True:

            data = await websocket.receive_json()
            event_type = data.get("type")

            # 1. NORMAL CHAT MESSAGE
            if event_type == "message":

                try:

                    message = data.get("message", "")

                    if not isinstance(message, str) or not message.strip():
                        raise ValueError("Please enter a message.")

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

            # 2. UPDATE EDITED DRAFTS
            elif event_type == "update_drafts":

                try:

                    save_edited_drafts(
                        data.get("job_post", {}),
                        data.get("application_form", {})
                    )

                    await websocket.send_json({
                        "type": "drafts_updated",
                        "message": "Both edited drafts saved successfully."
                    })

                except Exception as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # 3. APPROVE BOTH DRAFTS
            elif event_type == "approve":

                try:

                    raw_job_post = data.get("job_post", {})
                    raw_application_form = data.get("application_form", {})

                    if not isinstance(raw_job_post, dict):
                        raise ValueError("Invalid job post.")

                    if not isinstance(raw_application_form, dict):
                        raise ValueError("Invalid application form.")

                    job_post = prepare_job_post(raw_job_post)
                    application_form = prepare_application_form(
                        raw_application_form
                    )

                    drafts_changed = (
                        job_post != chat_service.current_job_post
                        or application_form != chat_service.current_application_form
                    )

                    if drafts_changed:

                        chat_service.current_job_post = job_post
                        chat_service.current_application_form = application_form

                        reset_creation_state()

                    chat_service.job_post_approved = True
                    chat_service.application_form_approved = True

                    result = await create_form_if_approved()

                    if result:
                        await websocket.send_json(result)

                except Exception as error:

                    import traceback
                    traceback.print_exc()

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # 4. APPROVE JOB POST ONLY
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
                            await websocket.send_json(result)

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

            # 5. APPROVE APPLICATION FORM ONLY
            elif event_type == "approve_application_form":

                if not chat_service.current_application_form:

                    await websocket.send_json({
                        "type": "error",
                        "message": "No application form is available."
                    })

                    continue

                chat_service.application_form_approved = True

                if chat_service.job_post_approved:

                    try:

                        result = await create_form_if_approved()

                        if result:
                            await websocket.send_json(result)

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

            # 6. RESET CONVERSATION
            elif event_type == "reset":

                active_sessions[session_id] = ChatService()
                chat_service = active_sessions[session_id]

                await websocket.send_json({
                    "type": "reset",
                    "message": "Conversation reset successfully."
                })

            # 7. UNKNOWN EVENT
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

        print(f"WebSocket error for session {session_id}: {error}")
