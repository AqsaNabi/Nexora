from fastapi import FastAPI
from backend.routes.chat_router import router as chat_router

app = FastAPI(
    title="Nexora HR Job Post Generator",
    description="AI-powered HR Job Post and Application Form Generator",
    version="1.0.0"
)

app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Chatbot backend is working"
    }