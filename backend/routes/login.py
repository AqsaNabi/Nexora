from fastapi import APIRouter
from pydantic import BaseModel, EmailStr
from services.login import login_user

class LoginData(BaseModel):

    email: EmailStr
    password: str
router = APIRouter()


@router.post("/login")
def login(data: LoginData):

    return login_user(data.email, data.password)