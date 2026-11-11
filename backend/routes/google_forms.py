
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.google_form_service import create_google_form


router = APIRouter(
    prefix="/google-forms",
    tags=["Google Forms"]
)


# Individual recruitment question
class QuestionRequest(BaseModel):
    question: str
    type: str
    required: bool = False
    options: list[str] = Field(default_factory=list)


# Recruitment form request
class FormRequest(BaseModel):
    job_title: str
    department: str | None = None
    questions: list[QuestionRequest]


@router.post("/create")
def create_form(request: FormRequest):

    try:

        # Validate job title
        if not request.job_title.strip():
            raise ValueError("Job title cannot be empty.")

        # Generate a relatable Google Form title
        if request.department:
            form_title = (
                f"Nexora - {request.job_title.strip()} "
                f"({request.department.strip()}) "
                "Recruitment Application"
            )
        else:
            form_title = (
                f"Nexora - {request.job_title.strip()} "
                "Recruitment Application"
            )

        # Convert question models into dictionaries
        questions = [
            question.model_dump()
            for question in request.questions
        ]

        # Generate Google Form
        result = create_google_form(
            title=form_title,
            questions=questions
        )

        return {
            "message": "Google Form created successfully!",
            "form_id": result["form_id"],
            "title": result["title"],
            "form_url": result["form_url"]
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
