
from fastapi import APIRouter, Depends, HTTPException, Request

from src.db import SessionDep
from src.models import Users
from src.utils import decodeToken, verifyUserTokenSession


router = APIRouter(prefix="/api/user", dependencies=[Depends(verifyUserTokenSession)])

@router.get("/jwt")
def getAuthUser(request: Request, session: SessionDep):
    token = request.cookies.get("jwt")
    print(token)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decodeToken(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    userId = payload.get("id")
    if not userId:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.get(Users, userId)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "createdAt": user.created_at,
    }
