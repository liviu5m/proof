
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import select
from db import SessionDep
from models import Users
import jwt
import os
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth")

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginData, session: SessionDep):
    stmt = select(Users).where(Users.email == data.email)
    user = session.exec(stmt).first()

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

class RegisterData(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register")
async def register(data: RegisterData, session: SessionDep):
    stmt = select(Users).where(Users.email == data.email)
    user = session.exec(stmt).first()

    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(data.password[:72])
    if not pwd_context.verify(data.password, hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    user = Users(email=data.email, password=hashed_password, username=data.username)
    session.add(user)
    session.commit()
    return {"message": "User registered successfully"}
