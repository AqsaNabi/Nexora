from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from services.user_policy import ask_policy_question

router = APIRouter(
    prefix="/user/policies",
    tags=["Employee Policy Assistant"]
)


class PolicyQuestionRequest(BaseModel):
    question: str
    category: Optional[str] = None


@router.post("/ask")
def ask_policy_route(request: PolicyQuestionRequest):

    result = ask_policy_question(
        question=request.question,
        category=request.category
    )

    return {
        "success": True,
        "message": "Policy question processed successfully",
        "data": result
    }