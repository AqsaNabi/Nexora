
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from backend.services.chat_service import ChatService

from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
)

from backend.model.post_gen.approved_payload_service import (
    create_approved_payload,
    delete_approved_payload
)


router = APIRouter()

# Store active ChatService objects using session IDs
active_sessions = {}


def update_session_drafts(
    session_id,
    chat_service,
    job_post,
    application_form
):
    """
    Validate and update both drafts.

    If the content has changed, reset previous approvals
    and remove the previous approved JSON file.
    """

    updated_job_post = prepare_job_post(job_post)

    updated_application_form = prepare_application_form(
        application_form
    )

    if (
        not chat_service.current_job_post
        or not chat_service.current_application_form
    ):
        raise ValueError(
            "Generate both drafts before saving or approving."
        )

    drafts_changed = (
        updated_job_post != chat_service.current_job_post
        or updated_application_form
        != chat_service.current_application_form
    )

    chat_service.current_job_post = updated_job_post
    chat_service.current_application_form = updated_application_form

    if drafts_changed:

        chat_service.job_post_approved = False
        chat_service.application_form_approved = False

        chat_service.approved_payload = None
        chat_service.approved_json_path = None

        # Remove an older approved JSON if the drafts changed
        delete_approved_payload(session_id)

    return drafts_changed


async def approve_draft(
    websocket,
    session_id,
    chat_service,
    approval_type,
    job_post=None,
    application_form=None
):
    """
    Save the latest frontend drafts, approve the requested
    item, and create the combined JSON if both are approved.
    """

    try:

        # First, save the latest edited versions.
        # This does not reset approvals if the content is unchanged.
        update_session_drafts(
            session_id,
            chat_service,
            job_post,
            application_form
        )

        # Approve the requested item
        if approval_type == "approve_job_post":

            chat_service.job_post_approved = True

        elif approval_type == "approve_application_form":

            chat_service.application_form_approved = True

        # Check whether both drafts are approved
        both_approved = (
            chat_service.job_post_approved
            and chat_service.application_form_approved
        )

        if both_approved:

            # Create and save ONE combined JSON file
            approved_payload, saved_file = (
                await run_in_threadpool(
                    create_approved_payload,
                    session_id,
                    chat_service.current_job_post,
                    chat_service.current_application_form
                )
            )

            chat_service.approved_payload = approved_payload
            chat_service.approved_json_path = saved_file

            await websocket.send_json({
                "type": "approval",
                "job_post_approved": True,
                "application_form_approved": True,
                "approved_payload": approved_payload,
                "saved_file": saved_file,
                "message": (
                    "Both drafts approved. "
                    "Combined JSON saved successfully."
                )
            })

        else:

            await websocket.send_json({
                "type": "approval",
                "job_post_approved": (
                    chat_service.job_post_approved
                ),
                "application_form_approved": (
                    chat_service.application_form_approved
                ),
                "message": (
                    "Approval recorded successfully. "
                    "The other draft is still awaiting approval."
                )
            })

    except Exception as error:

        await websocket.send_json({
            "type": "error",
            "message": str(error)
        })


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):

    await websocket.accept()

    # Create a new session if this session ID is not active
    if session_id not in active_sessions:
        active_sessions[session_id] = ChatService()

    chat_service = active_sessions[session_id]

    await websocket.send_json({
        "type": "connected",
        "message": "WebSocket connected successfully."
    })

    try:

        while True:

            data = await websocket.receive_json()

            event_type = data.get("type")

            # -----------------------------------------
            # 1. GENERATE JOB POST AND APPLICATION FORM
            # -----------------------------------------

            if event_type == "message":

                try:

                    response = await run_in_threadpool(
                        chat_service.process_message,
                        data.get("message", "")
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

            # -----------------------------------------
            # 2. SAVE BOTH EDITED DRAFTS
            # -----------------------------------------

            elif event_type == "update_drafts":

                try:

                    update_session_drafts(
                        session_id,
                        chat_service,
                        data.get("job_post", {}),
                        data.get("application_form", {})
                    )

                    await websocket.send_json({
                        "type": "drafts_updated",
                        "message": (
                            "Both edited drafts saved successfully."
                        ),
                        "job_post_approved": (
                            chat_service.job_post_approved
                        ),
                        "application_form_approved": (
                            chat_service.application_form_approved
                        )
                    })

                except Exception as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # -----------------------------------------
            # 3. APPROVE JOB POST
            # -----------------------------------------

            elif event_type == "approve_job_post":

                await approve_draft(
                    websocket=websocket,
                    session_id=session_id,
                    chat_service=chat_service,
                    approval_type="approve_job_post",
                    job_post=data.get("job_post", {}),
                    application_form=data.get(
                        "application_form", {}
                    )
                )

            # -----------------------------------------
            # 4. APPROVE APPLICATION FORM
            # -----------------------------------------

            elif event_type == "approve_application_form":

                await approve_draft(
                    websocket=websocket,
                    session_id=session_id,
                    chat_service=chat_service,
                    approval_type="approve_application_form",
                    job_post=data.get("job_post", {}),
                    application_form=data.get(
                        "application_form", {}
                    )
                )

            # -----------------------------------------
            # 5. RESET SESSION
            # -----------------------------------------

            elif event_type == "reset":

                active_sessions[session_id] = ChatService()
                chat_service = active_sessions[session_id]

                await websocket.send_json({
                    "type": "reset",
                    "message": "Conversation reset successfully."
                })

    except WebSocketDisconnect:

        print(f"HR disconnected: {session_id}")

    except Exception as error:

        print(
            f"WebSocket error for {session_id}: {error}"
        )
