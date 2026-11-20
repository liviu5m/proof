import os
from datetime import UTC, datetime, timedelta

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import select

from src.db import SessionDep
from src.mailer import send_email_verification, send_password_reset_email
from src.models import EmailVerifications, PasswordResetTokens, RefreshTokens, Users
from src.utils import (
    create_token,
    createAccessToken,
    hash_token,
    hashPassword,
    verify_csrf,
    verifyPassword,
)

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
    try:
        stmt = select(Users).where(Users.email == data.email)
        user = session.exec(stmt).first()

        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        if user.provider != "credentials":
            raise HTTPException(
                status_code=400,
                detail=f"This account was created with {user.provider}. Please sign in with {user.provider}.",
            )

        if not user.password:
            raise HTTPException(
                status_code=400,
                detail="No password set for this account. Please reset your password.",
            )

        if not verifyPassword(data.password, user.password):
            raise HTTPException(status_code=400, detail="Passwords do not match.")

        if not user.verified:
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please verify your email before logging in.",
            )

        assert user.id is not None, "User ID should not be None for existing user"
        jwt = createAccessToken(
            data={
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
            }
        )
        refresh_plain = create_token()
        refresh_token_row = RefreshTokens(
            user_id=user.id,  # type: ignore[arg-type]
            token_hash=hash_token(refresh_plain),
            expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False,
        )
        session.add(refresh_token_row)
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"LOGIN ERROR: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500, detail="Login failed. Please try again."
        ) from None


class RegisterData(BaseModel):
    name: str
    email: str
    password: str
    passwordConfirmation: str


@router.post("/register")
async def register(
    data: RegisterData, session: SessionDep, _: Request = Depends(verify_csrf)
):
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
    token = create_token()
    session.add(user)
    session.commit()
    session.refresh(user)
    assert user.id is not None, "User ID should not be None after commit"
    token = create_token()
    email_verification = EmailVerifications(
        user_id=user.id,  # type: ignore[arg-type]
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    session.add(email_verification)
    session.commit()
    try:
        await send_email_verification(user, token)
    except Exception as e:
        print(f"Email send failed: {e}")
    return {"message": "User registered successfully"}


class ResendData(BaseModel):
    email: str


class PasswordResetRequest(BaseModel):
    email: str


class ConfirmResetData(BaseModel):
    token: str
    new_password: str


@router.post("/resend-verification")
async def resend(
    data: ResendData, session: SessionDep, _: Request = Depends(verify_csrf)
):
    stmt = select(Users).where(Users.email == data.email)
    user = session.exec(stmt).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    assert user.id is not None, "User ID should not be None for existing user"
    token = create_token()
    email_verification = EmailVerifications(
        user_id=user.id,  # type: ignore[arg-type]
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    session.add(email_verification)
    session.commit()

    try:
        await send_email_verification(user, token)
    except Exception as e:
        print(f"Email send failed: {e}")
    return {"message": "Email sent successfully"}


@router.post("/password-reset/request")
async def request_password_reset(
    data: PasswordResetRequest, session: SessionDep, _: Request = Depends(verify_csrf)
):
    stmt = select(Users).where(Users.email == data.email)
    user = session.exec(stmt).first()
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}

    assert user.id is not None, "User ID should not be None for existing user"
    token = create_token()
    reset_token = PasswordResetTokens(
        user_id=user.id,  # type: ignore[arg-type]
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    session.add(reset_token)
    session.commit()

    try:
        await send_password_reset_email(user, token)
    except Exception as e:
        print(f"Password reset email send failed: {e}")

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    data: ConfirmResetData, session: SessionDep, _: Request = Depends(verify_csrf)
):
    token_hash = hash_token(data.token)
    stmt = select(PasswordResetTokens).where(
        PasswordResetTokens.token_hash == token_hash
    )
    reset_token = session.exec(stmt).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if reset_token.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Token expired")
    if reset_token.used:
        raise HTTPException(status_code=400, detail="Token already used")

    user = session.get(Users, reset_token.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.password = hashPassword(data.new_password)
    reset_token.used = True
    session.add(user)
    session.add(reset_token)
    session.commit()

    return {"message": "Password reset successfully"}


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
        raise HTTPException(
            status_code=400, detail="Failed to fetch tokens from Google"
        )

    tokens = token_res.json()
    access_token = tokens.get("access_token")

    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    user_res = requests.get(
        user_info_url, headers={"Authorization": f"Bearer {access_token}"}
    )
    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    user_info = user_res.json()
    email = user_info.get("email")
    name = user_info.get("name")
    user_info.get("sub")

    userStmt = select(Users).where(Users.email == email)
    user = session.exec(userStmt).first()
    userFinal = None

    if user and user.provider != "google":
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth/login?error=This%20users%20can't%20be%20signed%20in%20with%20Google"
        )
    elif user:
        userFinal = user
    else:
        userFinal = Users(email=email, name=name, provider="google", verified=True)
        session.add(userFinal)
        session.commit()
        session.refresh(userFinal)
    assert userFinal.id is not None, "User ID should not be None for existing user"

    jwt = createAccessToken(
        data={
            "id": userFinal.id,
            "email": userFinal.email,
            "name": userFinal.name,
            "role": userFinal.role.value,
        }
    )
    refresh_plain = create_token()
    refresh_token_row = RefreshTokens(
        user_id=userFinal.id,  # type: ignore[arg-type]
        token_hash=hash_token(refresh_plain),
        expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    session.add(refresh_token_row)
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
        token_hash = hash_token(refresh_token)
        stmt = select(RefreshTokens).where(RefreshTokens.token_hash == token_hash)
        rt = session.exec(stmt).first()
        if rt:
            rt.revoked = True
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

    token_hash = hash_token(refresh_token)
    stmt = select(RefreshTokens).where(RefreshTokens.token_hash == token_hash)
    rt = session.exec(stmt).first()

    if not rt or rt.revoked:
        response.delete_cookie(key="jwt", path="/", secure=True, samesite="none")
        response.delete_cookie(
            key="refresh_token", path="/api/auth/refresh", secure=True, samesite="none"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check expiry
    if rt.expires_at < datetime.now(UTC):
        rt.revoked = True
        session.add(rt)
        session.commit()
        response.delete_cookie(key="jwt", path="/", secure=True, samesite="none")
        response.delete_cookie(
            key="refresh_token", path="/api/auth/refresh", secure=True, samesite="none"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    user = session.get(Users, rt.user_id)
    if not user:
        response.delete_cookie(key="jwt", path="/", secure=True, samesite="none")
        response.delete_cookie(
            key="refresh_token", path="/api/auth/refresh", secure=True, samesite="none"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    assert user.id is not None, "User ID should not be None for existing user"
    # Revoke old token and create new one (rotation)
    rt.revoked = True
    session.add(rt)

    new_plain = create_token()
    new_hash = hash_token(new_plain)
    new_rt = RefreshTokens(
        user_id=user.id,  # type: ignore[arg-type]
        token_hash=new_hash,
        expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    session.add(new_rt)
    session.commit()

    new_jwt = createAccessToken(
        data={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
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


@router.post("/email-verification")
async def verify_email(data: dict, session: SessionDep):
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token required")

    token_hash = hash_token(token)
    stmt = select(EmailVerifications).where(EmailVerifications.token_hash == token_hash)
    ev = session.exec(stmt).first()

    if not ev or ev.used:
        raise HTTPException(status_code=400, detail="Invalid or used token")
    if ev.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Token expired")

    user = session.get(Users, ev.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    user.verified = True
    ev.used = True
    session.add(user)
    session.add(ev)
    session.commit()

    return {"message": "Email verified successfully. You can now log in."}
