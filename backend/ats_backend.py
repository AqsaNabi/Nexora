
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.ats_router import router as ats_router


# =========================================================
# 1. FASTAPI CONFIGURATION
# =========================================================

app = FastAPI(
    title="ATS Testing Backend"
)


# =========================================================
# 2. CORS CONFIGURATION
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 3. REGISTER ATS ROUTER
# =========================================================

app.include_router(ats_router)


# =========================================================
# 4. HOME ENDPOINT
# =========================================================

@app.get("/")
def home():

    return {
        "message": "ATS testing backend is running"
    }
