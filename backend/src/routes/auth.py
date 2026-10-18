from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import select
from db import SessionDep
from models import Users
import jwt
import os
from passlib.context import CryptContext

from utils import createAccessToken, hashPassword
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
import bcrypt
router = APIRouter(prefix="/auth")

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginData, session: SessionDep, response: Response):
    stmt = select(Users).where(Users.email == data.email)
    user = session.exec(stmt).first()

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    jwt = createAccessToken(
        data={
            "userId": user.id,
            "email": user.email,
            "name": user.name,
        }
    )
    response.set_cookie(
        key="jwt",
        value=jwt,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24,
        path="/",
    )
    return {"message": "User logged in successfully"}

class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    passwordConfirmation: str

@router.post("/register")
async def register(data: RegisterData, session: SessionDep):
    stmt = select(Users).where(Users.email == data.email)
    user = session.exec(stmt).first()
    if data.password != data.passwordConfirmation:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hashPassword(data.password)
    user = Users(email=data.email, password=hashed_password, name=data.name)
    session.add(user)
    session.commit()
    return {"message": "User registered successfully"}
