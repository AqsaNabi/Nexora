from fastapi import WebSocket, HTTPException
from jose import jwt, JWTError

# import from HER file — single source of truth for secret + algorithm
from backend.authen import SECRET_KEY, ALGORITHM


def verify_token_ws(websocket: WebSocket) -> str:
    token = websocket.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")