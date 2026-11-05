import base64

from fastapi import HTTPException

from repository.login import get_employee_by_email
from authen.auth import create_token


def login_user(email, password):

    # 1. Fetch employee from database
    employee = get_employee_by_email(email)

    if employee is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # 2. Verify password
    if employee["password"] != password:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # 3. Generate JWT token
    token = create_token(employee["email"])

    # 4. Convert image bytes into Base64
    profile_picture = employee["profile_picture"]

    if profile_picture is not None:
        profile_picture = base64.b64encode(
            bytes(profile_picture)
        ).decode("utf-8")

    # 5. Return employee details
    return {

        "message": "Login successful",

        "status_code": 200,

        "access_token": token,

        "token_type": "bearer",

        "employee_id": employee["employee_id"],

        "full_name": employee["full_name"],

        "email": employee["email"],

        "date_of_birth": str(employee["date_of_birth"])
        if employee["date_of_birth"] else None,

        "gender": employee["gender"],

        "profile_picture": profile_picture,

        "mobile": employee["mobile"],

        "designation": employee["designation"],

        "teamsmail": employee["teamsmail"]
    }