
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.services.resume_service import save_resume

router = APIRouter(
    prefix="/resumes",
    tags=["Resume Upload"]
)


@router.post("/upload")
async def upload_resume(
    post_id: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        result = await save_resume(
            file=file,
            post_id=post_id,
            email=email
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )

        return {
            "success": True,
            "message": result["message"],
            "application_id": result["application_id"]
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except HTTPException:
        raise

    except Exception as error:
        print(f"Resume upload failed: {error}")

        raise HTTPException(
            status_code=500,
            detail="An error occurred while uploading the resume."
        )
