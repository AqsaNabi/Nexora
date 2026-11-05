from datetime import datetime, timedelta, timezone
 
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
 
 
SECRET_KEY = "abd"
ALGORITHM = "HS256"
 
security = HTTPBearer()
 
 
def create_token(email):
 
    expire = (
        datetime.now(timezone.utc)
        + timedelta(hours=1)
    )
 
    data = {
        "sub": email,
        "exp": expire
    }
 
    token = jwt.encode(
        data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
 
    return token
 
 
def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
 
    token = credentials.credentials
 
    try:
 
        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
 
        return True
 
    except JWTError:
 
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )