from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import select
from src.db import SessionDep
from src.models import RefreshToken, Users
import jwt
import os
from src.utils import create_refresh_token, createAccessToken, hash_refresh_token, hashPassword, verifyPassword
import requests

router = APIRouter(prefix="/api/auth")
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
REFRESH_TOKEN_EXPIRE_DAYS = 7

class LoginData(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginData, session: SessionDep, response: Response):
    stmt = select(Users).where(Users.email == data.email)
    user = session.exec(stmt).first()

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verifyPassword(data.password, user.password):
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    jwt = createAccessToken(
        data={
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    )
    refresh_plain = create_refresh_token()
    user.refresh_token = hash_refresh_token(refresh_plain)
    session.add(user)
    session.commit()

    response.set_cookie(
        key="refresh_token",
        value=refresh_plain,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * 7,
        path="/api/auth/refresh",
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
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password is too short")
    hashed_password = hashPassword(data.password)
    user = Users(email=data.email, password=hashed_password, name=data.name)
    session.add(user)
    session.commit()
    return {"message": "User registered successfully"}

@router.get("/google")
async def google(response: Response):
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile"
    )
    return RedirectResponse(url=google_auth_url)

@router.get("/google/callback")
def google_callback(code: str, session: SessionDep, response: Response):
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    token_res = requests.post(token_url, data=token_data)
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch tokens from Google")
    
    tokens = token_res.json()
    access_token = tokens.get("access_token")

    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    user_res = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")
    
    user_info = user_res.json()
    email = user_info.get("email")
    name = user_info.get("name")
    google_id = user_info.get("sub")
    
    userStmt = select(Users).where(Users.email == email);
    user = session.exec(userStmt).first()
    userFinal = None 

    if user and user.provider != "google":
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/login?error=This%20users%20can't%20be%20signed%20in%20with%20Google")
    elif user:
        userFinal = user
    else:
        userFinal = Users(email=email, name=name, provider="google")
        session.add(userFinal)
        session.commit()
        session.refresh(userFinal)
    

    jwt = createAccessToken(
        data={
            "id": userFinal.id,
            "email": userFinal.email,
            "name": userFinal.name,
        }
    )
    refresh_plain = create_refresh_token()
    userFinal.refresh_token = hash_refresh_token(refresh_plain)
    session.add(userFinal)
    session.commit()

    response.set_cookie(
        key="refresh_token",
        value=refresh_plain,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * 7,
        path="/api/auth/refresh",
    )
    response = RedirectResponse(url=f"{FRONTEND_URL}/dashboard/datasets")
    response.set_cookie(
        key="jwt",
        value=jwt,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24,
        path="/",
    )
    return response
    
@router.post("/logout")
def logout(request: Request, response: Response, session: SessionDep):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)
        stmt = select(Users).where(Users.refresh_token == token_hash)
        rt = session.exec(stmt).first()
        if rt:
            rt.refresh_token = None
            session.add(rt)
            session.commit()

    response.delete_cookie(key="jwt", path="/", secure=True, samesite="none")
    response.delete_cookie(
        key="refresh_token", path="/api/auth/refresh", secure=True, samesite="none"
    )
    return {"message": "Logged out successfully"}

@router.post("/refresh")
async def getRefreshToken(request: Request, response: Response, session: SessionDep):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    token_hash = hash_refresh_token(refresh_token)
    stmt = select(Users).where(Users.refresh_token == token_hash)
    rt = session.exec(stmt).first()

    if not rt:
        response.delete_cookie(key="jwt", path="/", secure=True, samesite="none")
        response.delete_cookie(
            key="refresh_token", path="/api/auth/refresh", secure=True, samesite="none"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_plain = create_refresh_token()
    new_hash = hash_refresh_token(new_plain)
    rt.refresh_token = new_hash
    session.add(rt)
    session.commit()

    new_jwt = createAccessToken(
        data={
            "id": rt.id,
            "email": rt.email,
            "name": rt.name,
        }
    )

    response.set_cookie(
        key="jwt",
        value=new_jwt,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=new_plain,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS,
        path="/api/auth/refresh",
    )

    return {"message": "Tokens refreshed"}
