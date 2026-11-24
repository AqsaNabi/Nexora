from fastapi import APIRouter, HTTPException, Depends
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from fastapi.responses import Response

from backend.repository.recruit_repo import (
    get_candidate_resume,
    get_dashboard_data,
    get_applications_data,
    submit_application_data
)
from backend.authen.auth import verify_token, SECRET_KEY, ALGORITHM


# =========================================================
# 1. CREATE ROUTERS
# =========================================================

# HTTP router — kept exactly as before.
# Applies Depends(verify_token) to every *HTTP* route only.
router = APIRouter(dependencies=[Depends(verify_token)])

# WebSocket router — NO router-level Depends.
# Auth is done manually via verify_token_ws inside the handler.
ws_router = APIRouter()


# =========================================================
# 1b. WEBSOCKET-SPECIFIC TOKEN VERIFIER
# =========================================================
# HTTPBearer (used by verify_token) can only read the Authorization
# header, and browsers cannot set that on a WebSocket handshake.
# So on WS we read the token from  ?token=<jwt>  instead.
# Uses the SAME SECRET_KEY / ALGORITHM as your friend's auth file,
# so tokens minted by create_token work here unchanged.

def verify_token_ws(websocket: WebSocket) -> str:

    from jose import jwt, JWTError

    token = websocket.query_params.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=401, detail="Token missing subject"
            )
        return email

    except JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )


# =========================================================
# 2. ATS WEBSOCKET CONNECTION MANAGER
# =========================================================

class ATSConnectionManager:

    def __init__(self):

        self.active_connections = []

    async def connect(self, websocket: WebSocket):

        await websocket.accept()

        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):

        if websocket in self.active_connections:

            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):

        disconnected_clients = []

        for connection in self.active_connections:

            try:

                await connection.send_json(message)

            except Exception:

                disconnected_clients.append(connection)

        for connection in disconnected_clients:

            self.disconnect(connection)


# Shared connection manager for ATS notifications
ats_manager = ATSConnectionManager()


# =========================================================
# 3. ATS WEBSOCKET ENDPOINT  (now on ws_router)
# =========================================================

@ws_router.websocket("/ws/ats/notifications")
async def ats_notifications(websocket: WebSocket):

    # ---- AUTH FIRST (before accept) ----
    try:
        verify_token_ws(websocket)
    except HTTPException:
        # 1008 = policy violation. Must close *before* accept().
        await websocket.close(code=1008)
        return

    # ---- Only now accept ----
    await ats_manager.connect(websocket)

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        ats_manager.disconnect(websocket)


# =========================================================
# 4. APPLICATION REQUEST MODEL
# =========================================================
# HTTPBearer (used by verify_token) can only read the Authorization
# header, and browsers cannot set that on a WebSocket handshake.
# So on WS we read the token from  ?token=<jwt>  instead.
# Uses the SAME SECRET_KEY / ALGORITHM as your friend's auth file,
# so tokens minted by create_token work here unchanged.
 
def verify_token_ws(websocket: WebSocket) -> str:
 
    from jose import jwt, JWTError
 
    token = websocket.query_params.get("token")
 
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=401, detail="Token missing subject"
            )
        return email
 
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token"
        )
 
 
# =========================================================
# 2. ATS WEBSOCKET CONNECTION MANAGER
# =========================================================
 
class ATSConnectionManager:
 
    def __init__(self):
 
        self.active_connections = []
 
    async def connect(self, websocket: WebSocket):
 
        await websocket.accept()
 
        self.active_connections.append(websocket)
 
    def disconnect(self, websocket: WebSocket):
 
        if websocket in self.active_connections:
 
            self.active_connections.remove(websocket)
 
    async def broadcast(self, message: dict):
 
        disconnected_clients = []
 
        for connection in self.active_connections:
 
            try:
 
                await connection.send_json(message)
 
            except Exception:
 
                disconnected_clients.append(connection)
 
        for connection in disconnected_clients:
 
            self.disconnect(connection)
 
 
# Shared connection manager for ATS notifications
ats_manager = ATSConnectionManager()
 
 
# =========================================================
# 3. ATS WEBSOCKET ENDPOINT  (now on ws_router)
# =========================================================
 
@ws_router.websocket("/ws/ats/notifications")
async def ats_notifications(websocket: WebSocket):
 
    # ---- AUTH FIRST (before accept) ----
    try:
        verify_token_ws(websocket)
    except HTTPException:
        # 1008 = policy violation. Must close *before* accept().
        await websocket.close(code=1008)
        return
 
    # ---- Only now accept ----
    await ats_manager.connect(websocket)
 
    try:
 
        while True:
 
            await websocket.receive_text()
 
    except WebSocketDisconnect:
 
        ats_manager.disconnect(websocket)
 
 
# =========================================================
# 4. APPLICATION REQUEST MODEL
# =========================================================
 
class ApplicationRequest(BaseModel):
 
    full_name: str
    email: str
    phone: Optional[str] = None
 
    resume_file: Optional[bytes] = None
    resume_filename: Optional[str] = None
    resume_content_type: Optional[str] = None
 
    resume_text: Optional[str] = None
 
    additional_data: Dict[str, Any] = Field(default_factory=dict)
 
 
# =========================================================
# 5. DASHBOARD ENDPOINT
# =========================================================
 
@router.get("/api/ats/dashboard")
def get_dashboard():
 
    try:
 
        return get_dashboard_data()
 
    except Exception as error:
 
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )
 
 
# =========================================================
# 6. GET CANDIDATE APPLICATIONS
# =========================================================
 
@router.get("/api/ats/jobs/{post_id}/applications")
def get_applications(post_id: str):
 
    try:
 
        return get_applications_data(post_id)
 
    except HTTPException:
        raise
 
    except Exception as error:
 
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )
 
 
# =========================================================
# 7. SUBMIT NEW CANDIDATE APPLICATION
# =========================================================
 
@router.post("/api/ats/jobs/{post_id}/applications")
async def submit_application(
    post_id: str,
    request: ApplicationRequest
):
 
    try:

        # Save application in PostgreSQL
        # Database function commits before returning

        result = await run_in_threadpool(
            submit_application_data,
            post_id,
            request
        )

        # Get saved application details

        application = result["application"]

        # Notify connected ATS dashboards
        # This happens only after successful database commit
        try:
            await ats_manager.broadcast({

                "type": "new_application",

                "post_id": post_id,

                "application_id": application["application_id"],

                "candidate_name": application["full_name"],

                "message": (
                    f'{application["full_name"]} has submitted '
                    f'a new application!'
                )

            })
        except Exception as error:

                print(f"ATS notification error: {error}")

        return result

    except HTTPException:

        raise
 
    except Exception as error:
 
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )


# =========================================================
# 8. VIEW CANDIDATE RESUME
# =========================================================
 
@router.get("/api/ats/applications/{application_id}/resume")
def view_candidate_resume(application_id: int):
 
    try:
 
        resume = get_candidate_resume(application_id)
 
        return Response(
            content=resume["resume_file"],
            media_type=resume["resume_content_type"],
            headers={
                "Content-Disposition": (
                    f'inline; filename="{resume["resume_filename"]}"'
                )
            }
        )
 
    except HTTPException:
        raise
 
    except Exception as error:
 
        raise HTTPException(
            status_code=500,
            detail=f"Resume retrieval error: {str(error)}"
        )