
from fastapi import FastAPI

from backend.routes.chat_router import router as chat_router
from backend.routes import auth_routes
from backend.routes.google_forms import router as google_form_router
from backend.services.pubsub_listener import (
    start_pubsub_listener,
    stop_pubsub_listener
)




app = FastAPI(
    title="Nexora HR Job Post Generator",
    description="AI-powered HR Job Post and Application Form Generator",
    version="1.0.0"
)

app.include_router(chat_router)
app.include_router(auth_routes.router)
app.include_router(google_form_router)


@app.on_event("startup")
def startup_event():
    start_pubsub_listener()


@app.on_event("shutdown")
def shutdown_event():
    stop_pubsub_listener()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "message": "Nexora chatbot backend is working"
    }
