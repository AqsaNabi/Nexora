from fastapi import FastAPI
from routes.login import router as login_router
from routes.register import router as register_router
from routes.details import router as details_router
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routes import router as auth_router
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
app.include_router(auth_router)
