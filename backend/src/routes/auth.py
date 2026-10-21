from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import select
from db import SessionDep
from models import Users
import jwt
import os
from passlib.context import CryptContext
from utils import createAccessToken, hashPassword
import bcrypt
import requests

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/api/auth")

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
REDIRECT_URI = "http://localhost:8000/api/auth/google/callback"

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
    
