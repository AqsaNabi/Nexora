
from fastapi import APIRouter, Form, File, UploadFile,Depends
from authen.auth import verify_token
from services.policy import upload_policy

router = APIRouter(
    prefix="/policies",
    tags=["Employee Policy Assistant"],
    dependencies=[Depends(verify_token)]

)
 

@router.post("/upload")
async def upload_policy_route(
    description: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...)
):

    result = await upload_policy(
        description=description,
        category=category,
        file=file
    )

    return {
        "success": True,
        "message": "Policy uploaded successfully",
        "data": result
    }
