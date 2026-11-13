
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.resume_service import save_resume


router = APIRouter(
    prefix="/resumes",
    tags=["Resume Upload"]
)


# ============================================================
# UPLOAD RESUME ENDPOINT
# ============================================================

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...)
):

    try:

        result = await save_resume(file)

        return {
            "success": True,
            "message": "Resume uploaded successfully.",
            "data": result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
