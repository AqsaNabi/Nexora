
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.google_form_service import create_google_form

router = APIRouter(
    prefix="/google-forms",
    tags=["Google Forms"]
)


class FormRequest(BaseModel):
    title: str


@router.post("/create")
def create_form(request: FormRequest):

    try:
        result = create_google_form(request.title)

        return {
            "message": "Google Form created successfully!",
            "form_id": result["form_id"],
            "title": result["title"],
            "form_url": result["form_url"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
