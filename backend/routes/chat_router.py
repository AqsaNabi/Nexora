import json

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends
)
from backend.authen.auth import (
    verify_token,
    SECRET_KEY,
    ALGORITHM
)

from starlette.concurrency import run_in_threadpool
from jose import jwt, JWTError



from backend.services.chat_service import ChatService

from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
)

from backend.model.post_gen.approved_payload_service import (
    create_approved_payload
)


router = APIRouter()


# Active conversations are stored in memory only.
active_sessions = {}


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):

    # ------------------------------------------
    # WEBSOCKET AUTHENTICATION
    # ------------------------------------------

    token = websocket.query_params.get("token")

    if not token:

        await websocket.close(code=1008)
        return

    try:

        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except JWTError:

        await websocket.close(code=1008)
        return

    # Accept connection only after authentication.
    await websocket.accept()

    if session_id not in active_sessions:
        active_sessions[session_id] = ChatService()

    chat_service = active_sessions[session_id]

    await websocket.send_json({
        "type": "connected",
        "session_id": session_id
    })

    try:

        while True:

            raw_message = await websocket.receive_text()

            try:

                event = json.loads(raw_message)

            except json.JSONDecodeError:

                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON event."
                })

                continue

            event_type = event.get("type")

            # ------------------------------------------
            # MESSAGE
            # ------------------------------------------

            if event_type == "message":

                user_message = event.get("message", "")

                response = await run_in_threadpool(
                    chat_service.process_message,
                    user_message
                )

                if response.get("type") == "error":

                    await websocket.send_json(response)

                else:

                    await websocket.send_json({
                        "type": "response",
                        "data": response.get("data", {})
                    })

            # ------------------------------------------
            # UPDATE DRAFTS
            # ------------------------------------------

            elif event_type == "update_drafts":

                try:

                    result = chat_service.update_drafts(
                        event.get("job_post", {}),
                        event.get("application_form", {})
                    )

                    await websocket.send_json({
                        "type": "drafts_updated",
                        "job_post": result["job_post"],
                        "application_form": result["application_form"]
                    })

                except Exception as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # ------------------------------------------
            # APPROVE
            # ------------------------------------------

            elif event_type == "approve":

                try:

                    if chat_service.is_approved:

                        raise ValueError(
                            "This job post has already been approved."
                        )

                    job_post = event.get("job_post")
                    application_form = event.get("application_form")

                    if not isinstance(job_post, dict):

                        raise ValueError(
                            "Job post must be a JSON object."
                        )

                    if not isinstance(application_form, dict):

                        raise ValueError(
                            "Application form must be a JSON object."
                        )

                    # Normalize the latest JSON sent by the frontend.
                    final_job_post = prepare_job_post(job_post)

                    final_application_form = prepare_application_form(
                        application_form
                    )

                    # Persist only after the Approve action.
                    approved_payload, saved_file = await run_in_threadpool(
                        create_approved_payload,
                        session_id,
                        final_job_post,
                        final_application_form
                    )

                    result = chat_service.approve(
                        final_job_post,
                        final_application_form,
                        approved_payload,
                        saved_file
                    )

                    await websocket.send_json({
                        "type": "approved",
                        "message": "Job post and application form approved successfully.",
                        "approved_payload": result["approved_payload"],
                        "saved_file": result["saved_file"]
                    })

                except Exception as error:

                    await websocket.send_json({
                        "type": "error",
                        "message": str(error)
                    })

            # ------------------------------------------
            # RESET
            # ------------------------------------------

            elif event_type == "reset":

                chat_service.reset()

                active_sessions.pop(session_id, None)

                await websocket.send_json({
                    "type": "reset",
                    "message": "Active conversation reset."
                })

                break

            else:

                await websocket.send_json({
                    "type": "error",
                    "message": "Unknown event type."
                })

    except WebSocketDisconnect:

        pass

    except Exception as error:

        print("WEBSOCKET ERROR:", str(error))

        try:

            await websocket.send_json({
                "type": "error",
                "message": "An unexpected backend error occurred."
            })

        except Exception:
            pass
