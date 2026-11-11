from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
from backend.routes.chat_router import router as chat_router
from fastapi.responses import RedirectResponse
from backend.routes import auth_routes
from backend.authen.google_oauth import (
    get_authorization_url,
    exchange_code_for_token
)
app = FastAPI(
    title="Nexora HR Job Post Generator",
    description="AI-powered HR Job Post and Application Form Generator",
    version="1.0.0"
)

app.include_router(chat_router)

app.include_router(auth_routes.router)
