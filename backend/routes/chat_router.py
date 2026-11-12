
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from backend.services.chat_service import ChatService
from backend.services.google_watch_service import create_response_watch
from backend.services.job_post_service import (
    prepare_job_post,
    prepare_application_form
)

from backend.services.google_form_service import create_google_form
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

    # ----------------------------------------
    # CREATE GOOGLE FORM AFTER BOTH APPROVALS
    # ----------------------------------------

    
    async def create_form_if_approved():

        if not (
            chat_service.job_post_approved
            and chat_service.application_form_approved
        ):
            return

        if getattr(chat_service, "recruitment_metadata_saved", False):
            return

        if chat_service.form_creation_in_progress:
            return

        chat_service.form_creation_in_progress = True

        try:
            job_post = chat_service.current_job_post
            application_form = chat_service.current_application_form

            job_description = job_post.get("job_description", "").strip()

            if not job_description:
                raise ValueError(
                    "Job description is missing from the approved job post."
                )

            form_title = application_form.get("form_title", "").strip()

            if not form_title:
                job_title = job_post.get("job_title", "").strip()

                form_title = (
                    f"{job_title} - Job Application - Nexora"
                    if job_title
                    else "Nexora Job Application Form"
                )
            
            # 1. Create the recruitment post only once
            if not getattr(chat_service, "created_post_id", None):

                chat_service.created_post_id = await run_in_threadpool(
                    create_recruitment_post,
                    job_description
                )

            # 2. Create the Google Form only once
            if not chat_service.created_form_id:

                result = await run_in_threadpool(
                    create_google_form,
                    form_title,
                    application_form.get("questions", []),
                    job_description
                )

                # Save these immediately so a metadata failure
                # does not cause another Google Form to be created.
                chat_service.created_form_id = result["form_id"]
                chat_service.created_form_url = result["form_url"]

                chat_service.question_mapping = result["question_mapping"]

            # 3. Save Google Form metadata in PostgreSQL
            await run_in_threadpool(
                save_recruitment_metadata,
                chat_service.created_post_id,
                chat_service.created_form_id,
                chat_service.created_form_url,
                None,
                chat_service.question_mapping
            )
            #  Register automatic Google Forms response notifications
            await run_in_threadpool(
                create_response_watch,
                chat_service.created_form_id
            )
            chat_service.recruitment_metadata_saved = True

            # 4. Notify the frontend
            await websocket.send_json({
                "type": "form_created",
                "message": "Google Form created and saved successfully!",
                "post_id": chat_service.created_post_id,
                "form_id": chat_service.created_form_id,
                "form_url": chat_service.created_form_url
            })

        except Exception as error:

            await websocket.send_json({
                "type": "error",
                "message": f"Recruitment form creation failed: {str(error)}"
            })

        finally:
            chat_service.form_creation_in_progress = False


    #####################################
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

                    chat_service.created_post_id = None
                    chat_service.question_mapping = None
                    chat_service.recruitment_metadata_saved = False

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
            # 2. UPDATE EDITED DRAFTS
            # ----------------------------------------

            elif data.get("type") == "update_drafts":

                try:
                    raw_job_post = data.get("job_post", {})
                    raw_application_form = data.get("application_form", {})

                    job_post = prepare_job_post(raw_job_post)

                    # Restore job_description
                    job_post["job_description"] = raw_job_post.get(
                        "job_description", ""
                    )

                    application_form = prepare_application_form(
                        raw_application_form
                    )

                    # Restore field_name and validation
                    original_questions = raw_application_form.get("questions", [])

                    for prepared_question, original_question in zip(
                        application_form["questions"],
                        original_questions
                    ):
                        prepared_question["field_name"] = original_question.get(
                            "field_name"
                        )
                        prepared_question["validation"] = original_question.get(
                            "validation", {}
                        )

                    chat_service.current_job_post = job_post
                    chat_service.current_application_form = application_form

                    chat_service.job_post_approved = False
                    chat_service.application_form_approved = False

                    # Reset previous form tracking
                    chat_service.created_form_id = None
                    chat_service.created_form_url = None
                    chat_service.form_creation_in_progress = False
                    chat_service.created_post_id = None
                    chat_service.question_mapping = None
                    chat_service.recruitment_metadata_saved = False

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
                    "application_form_approved":
                        chat_service.application_form_approved,
                    "message": "Job post approved successfully."
                })

                await create_form_if_approved()


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
                    "job_post_approved":
                        chat_service.job_post_approved,
                    "application_form_approved": True,
                    "message": "Application questions approved successfully."
                })

                await create_form_if_approved()


            # ----------------------------------------
            # 5. RESET SESSION
            # ----------------------------------------

            elif data.get("type") == "reset":

                active_sessions[session_id] = ChatService()

                chat_service = active_sessions[session_id]
                chat_service.created_post_id = None
                chat_service.question_mapping = None
                chat_service.recruitment_metadata_saved = False
                await websocket.send_json({
                    "type": "reset",
                    "message": "Conversation reset successfully."
                })


    except WebSocketDisconnect:

        print(f"HR disconnected: {session_id}")


    except Exception as error:

        print(f"WebSocket error for {session_id}: {error}")
