import os
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


def verify_django_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify a Django SimpleJWT access token.
    Shared across FastAPI services for authentication via Django-issued JWTs.
    """
    if credentials is None:
        raise HTTPException(401, "Missing authorization header")
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv("DJANGO_SECRET_KEY", ""),
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
