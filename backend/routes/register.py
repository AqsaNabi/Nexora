from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from pydantic import EmailStr
from datetime import date

from services.register import register_employee_service

router = APIRouter(
)


@router.post("/register")
async def register_employee(

    full_name: str = Form(..., min_length=2, max_length=100),

    email: EmailStr = Form(...),

    password: str = Form(..., min_length=8, max_length=128),

    designation: str = Form(..., min_length=2, max_length=100),

    gender: str = Form(...),

    date_of_birth: date = Form(...),

    mobile: str = Form(..., min_length=10, max_length=10),

    teamsmail: str = Form(""),

    profile_picture: UploadFile | None = File(None)

):

    # Read profile picture

    image_data = None

    if profile_picture is not None:

        # Check image format

        if profile_picture.content_type not in [
            "image/jpeg",
            "image/png"
        ]:

            raise HTTPException(
                status_code=400,
                detail="Only JPG and PNG images are allowed"
            )

        # Read image as bytes

        image_data = await profile_picture.read(
            10 * 1024 * 1024 + 1
        )

        # Check image size (10 MB)

        if len(image_data) > 10 * 1024 * 1024:

            raise HTTPException(
                status_code=413,
                detail="Profile picture must not exceed 10 MB"
            )

        if not image_data:

            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty"
            )

    # Prepare employee dictionary

    employee = {

        "full_name": full_name.strip(),

        "email": str(email).strip().lower(),

        "password": password,

        "designation": designation.strip(),

        "gender": gender.strip(),

        "date_of_birth": date_of_birth,

        "mobile": mobile.strip(),

        "teamsmail": teamsmail.strip().lower() or None

    }

    # Call service

    return register_employee_service(
        employee,
        image_data
    )