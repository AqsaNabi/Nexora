
from fastapi import APIRouter, UploadFile, File,Form, HTTPException
from pydantic import BaseModel

from services.policy import upload_policy

router = APIRouter(
    prefix="/policies",
    tags=["HR Policy Management"]
)



    


@router.post("/upload")
def upload_policy_route(
    policy_name: str = Form(...),
    description: str = Form(...),       
    category: str = Form(...),
    file: UploadFile = File(...)
):

    result = upload_policy(
        policy_name=policy_name,
        description=description,
        category=category,
        file=file
    )

    return {
        "success": True,
        "message": "Policy uploaded successfully",
        "data": result
    }
