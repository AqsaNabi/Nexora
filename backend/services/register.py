import uuid
from datetime import date
from fastapi import HTTPException

from repository.register import create_employee


def register_employee_service(employee, image_data=None):

    # 1. Validate gender
    allowed_genders = ["Male", "Female", "Other"]

    if employee["gender"] not in allowed_genders:
        raise HTTPException(
            status_code=400,
            detail="Invalid gender"
        )

    # 2. Validate mobile number
    if not employee["mobile"].isdigit() or len(employee["mobile"]) != 10:
        raise HTTPException(
            status_code=400,
            detail="Mobile number must contain exactly 10 digits"
        )

    # 3. Validate date of birth
    if employee["date_of_birth"] >= date.today():
        raise HTTPException(
            status_code=400,
            detail="Date of birth must be in the past"
        )

    # 4. Validate password
    if len(employee["password"]) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    # 5. Generate employee ID
    employee_id = str(uuid.uuid4())

    # 6. Prepare employee data
    employee_data = {
        "employee_id": employee_id,
        "full_name": employee["full_name"],
        "email": employee["email"],
        "designation": employee["designation"],
        "date_of_birth": employee["date_of_birth"],
        "gender": employee["gender"],
        "profile_picture": image_data,
        "mobile": employee["mobile"],
        "password": employee["password"],
        "teamsmail": employee["teamsmail"]
    }

    # 7. Call repository
    try:
        create_employee(employee_data)

        return {
            "message": "Employee registered successfully"
        }

    except Exception as e:

        import psycopg2

        if isinstance(e, psycopg2.errors.UniqueViolation):
            raise HTTPException(
                status_code=409,
                detail="Employee with this email already exists"
            )

        raise HTTPException(
            status_code=500,
            detail="Employee registration failed"
        )