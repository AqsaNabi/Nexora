from fastapi import APIRouter, Depends
from pydantic import BaseModel 
from authen.auth import verify_token 
from services.details import count_employees,get_employee_details

router = APIRouter(dependencies=[Depends(verify_token)])

@router.get("/count")
def get_employee_count():
    return {"count": count_employees()}
@router.get("/details")
def get_employee_detail():
    return get_employee_details()