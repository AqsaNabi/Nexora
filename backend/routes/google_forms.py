
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.services.google_form_service import create_google_form_from_json

from backend.authen.auth import verify_token 
router = APIRouter(
    prefix="/google-forms",
    tags=["Google Forms"],
    dependencies=[Depends(verify_token)]
)


# Individual recruitment question
class QuestionRequest(BaseModel):
    question: str
    type: str
    required: bool = False
    options: list[str] = Field(default_factory=list)


# Recruitment form request
class FormRequest(BaseModel):
    job_post: dict
    application_form: dict


@router.post("/create")
def create_form(request: FormRequest):
    try:
        data = request.model_dump()

        result = create_google_form_from_json(data)

        return {
            "message": "Google Form created successfully!",
            "form_id": result["form_id"],
            "title": result["title"],
            "description": result["description"],
            "form_url": result["form_url"],
            "question_mapping": result["question_mapping"],
            "skipped_questions": result["skipped_questions"]
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
