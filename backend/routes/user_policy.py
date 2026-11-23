from typing import Optional
from fastapi import APIRouter, Depends
from backend.authen.auth import verify_token
from pydantic import BaseModel
from backend.services.user_policy import ask_policy_question

router = APIRouter(
    prefix="/user/policies",
    tags=["Employee Policy Assistant"],
    dependencies=[Depends(verify_token)]
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