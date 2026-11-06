
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from backend.services.chat_service import ChatService

from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
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

    try:

        while True:

            data = await websocket.receive_json()

            # ----------------------------------------
            # 1. GENERATE JOB POST AND APPLICATION FORM
            # ----------------------------------------

            if data.get("type") == "message":

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


            # ----------------------------------------
            # 2. SAVE EDITED DRAFTS
            # ----------------------------------------

            elif data.get("type") == "update_drafts":

                try:

                    job_post = prepare_job_post(
                        data.get("job_post", {})
                    )

                    application_form = prepare_application_form(
                        data.get("application_form", {})
                    )

                    chat_service.current_job_post = job_post
                    chat_service.current_application_form = application_form

                    chat_service.job_post_approved = False
                    chat_service.application_form_approved = False

                    await websocket.send_json({
                        "type": "drafts_updated",
                        "message": "Both edited drafts saved successfully."
                    })

                except Exception as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })


            # ----------------------------------------
            # 3. APPROVE JOB POST
            # ----------------------------------------

            elif data.get("type") == "approve_job_post":

                if not chat_service.current_job_post:

                    await websocket.send_json({
                        "type": "error",
                        "message": "No job post is available."
                    })

                    continue

                chat_service.job_post_approved = True

                await websocket.send_json({
                    "type": "approval",
                    "job_post_approved": True,
                    "application_form_approved": chat_service.application_form_approved,
                    "message": "Job post approved successfully."
                })


            # ----------------------------------------
            # 4. APPROVE APPLICATION FORM
            # ----------------------------------------

            elif data.get("type") == "approve_application_form":

                if not chat_service.current_application_form:

                    await websocket.send_json({
                        "type": "error",
                        "message": "No application form is available."
                    })

                    continue

                chat_service.application_form_approved = True

                await websocket.send_json({
                    "type": "approval",
                    "job_post_approved": chat_service.job_post_approved,
                    "application_form_approved": True,
                    "message": "Application questions approved successfully."
                })


            # ----------------------------------------
            # 5. RESET SESSION
            # ----------------------------------------

            elif data.get("type") == "reset":

                active_sessions[session_id] = ChatService()

                chat_service = active_sessions[session_id]

                await websocket.send_json({
                    "type": "reset",
                    "message": "Conversation reset successfully."
                })


    except WebSocketDisconnect:

        print(f"HR disconnected: {session_id}")


    except Exception as error:

        print(f"WebSocket error for {session_id}: {error}")
