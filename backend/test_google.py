from fastapi import FastAPI
from routes.auth_routes import router as auth_router
from routes.google_forms import router as google_forms_router

app = FastAPI(
    title="Nexora API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(google_forms_router)