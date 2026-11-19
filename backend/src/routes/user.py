from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.db import SessionDep
from src.models import ProofUserRole, Users
from src.utils import (
    decodeToken,
    get_current_user,
    require_admin,
    verifyUserTokenSession,
)

router = APIRouter(prefix="/api/user", dependencies=[Depends(verifyUserTokenSession)])


class UpdateRoleRequest(BaseModel):
    role: ProofUserRole


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


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    data: UpdateRoleRequest,
    session: SessionDep,
    current_user: Users = Depends(get_current_user),
    _: Users = Depends(require_admin),
):
    user = session.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = data.role
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
    }


@router.get("/{user_id}")
def get_user_by_id(
    user_id: int,
    session: SessionDep,
    current_user: Users = Depends(get_current_user),
    _: Users = Depends(require_admin),
):
    user = session.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "created_at": user.created_at,
    }


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    session: SessionDep,
    current_user: Users = Depends(get_current_user),
    _: Users = Depends(require_admin),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = session.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()

    return {"message": f"User {user_id} deleted successfully"}
