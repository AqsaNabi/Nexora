
 
from fastapi import FastAPI

from backend.routes.login import router as login_router
from backend.routes.register import router as register_router
from backend.routes.details import router as details_router
from backend.routes.announcements import router as announcements_router
from backend.routes.policy import router as policy_router
from backend.routes.user_policy import router as user_policy_router
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.auth_routes import router as auth_router
from backend.routes.detail_router import router as ats_router
from backend.routes.chat_router import router as chat_router
from backend.routes import auth_routes
from backend.routes.google_forms import router as google_form_router
from backend.services.pubsub_listener import (
    start_pubsub_listener,
    stop_pubsub_listener
)

from backend.routes.detail_router import router as detail_router, ws_router as detail_ws
from backend.routes.chat_router    import router as ats_router,    ws_router as ats_ws

 

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(detail_router)
app.include_router(detail_ws)
app.include_router(ats_ws)
app.include_router(ats_router)
app.include_router(register_router)
app.include_router(login_router)
app.include_router(details_router)
app.include_router(announcements_router)
app.include_router(policy_router)
app.include_router(user_policy_router)
app.include_router(chat_router)
app.include_router(auth_routes.router)
app.include_router(google_form_router)
@app.get("/")
def home():

    return {
        "message": "ATS testing backend is running"
    }

@app.on_event("startup")
def startup_event():
    start_pubsub_listener()


@app.on_event("shutdown")
def shutdown_event():
    stop_pubsub_listener()

