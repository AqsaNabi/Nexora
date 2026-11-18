
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from fastapi.responses import Response
from backend.repository.recruit_repo import get_candidate_resume
from backend.repository.recruit_repo import  (
    get_dashboard_data,
    get_applications_data,
    submit_application_data
)


# =========================================================
# 1. CREATE ROUTER
# =========================================================

router = APIRouter()


# =========================================================
# 2. APPLICATION REQUEST MODEL
# =========================================================

class ApplicationRequest(BaseModel):

    full_name: str
    email: str
    phone: Optional[str] = None

    resume_file: Optional[bytes] = None
    resume_filename: Optional[str] = None
    resume_content_type: Optional[str] = None

    resume_text: Optional[str] = None

    additional_data: Dict[str, Any] = Field(default_factory=dict)


# =========================================================
# 3. DASHBOARD ENDPOINT
# =========================================================

@router.get("/api/ats/dashboard")
def get_dashboard():

    try:

        return get_dashboard_data()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )


# =========================================================
# 4. GET CANDIDATE APPLICATIONS
# =========================================================

@router.get("/api/ats/jobs/{post_id}/applications")
def get_applications(post_id: str):

    try:

        return get_applications_data(post_id)

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )


# =========================================================
# 5. SUBMIT NEW CANDIDATE APPLICATION
# =========================================================

@router.post("/api/ats/jobs/{post_id}/applications")
def submit_application(
    post_id: str,
    request: ApplicationRequest
):

    try:

        return submit_application_data(
            post_id,
            request
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )

# =========================================================
# 6. VIEW CANDIDATE RESUME
# =========================================================

@router.get("/api/ats/applications/{application_id}/resume")
def view_candidate_resume(application_id: int):

    try:

        resume = get_candidate_resume(application_id)

        return Response(
            content=resume["resume_file"],
            media_type=resume["resume_content_type"],
            headers={
                "Content-Disposition": (
                    f'inline; filename="{resume["resume_filename"]}"'
                )
            }
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Resume retrieval error: {str(error)}"
        )