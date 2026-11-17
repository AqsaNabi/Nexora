from fastapi import FastAPI
from routes.login import router as login_router
from routes.register import router as register_router
from routes.details import router as details_router
from routes.announcements import router as announcements_router
from routes.policy import router as policy_router
from routes.user_policy import router as user_policy_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(register_router)
app.include_router(login_router)
app.include_router(details_router)
app.include_router(announcements_router)
app.include_router(policy_router)
app.include_router(user_policy_router)