from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from backend.authen.google_oauth import (
    get_authorization_url,
    exchange_code_for_token
)
router = APIRouter(
    prefix="/auth/google",
    tags=["Google Authentication"]
)

# Temporary state storage for local development
oauth_states = {}

@router.get("/login")
def google_login():
    authorization_url, state, flow = get_authorization_url()

    oauth_states[state] = flow

    return RedirectResponse(url=authorization_url)


@router.get("/callback")
def google_callback(code: str, state: str):

    if state not in oauth_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state"
        )

    flow = oauth_states.pop(state)

    try:
        exchange_code_for_token(code, flow)

        return {
            "message": "Google authentication successful!",
            "authenticated": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Google authentication failed: {str(e)}"
        )