import asyncio
import hashlib
import html
import os
import random
import re
import secrets
from datetime import datetime, timedelta

import bcrypt
import jwt
import pyclamd
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, UploadFile, status
from passlib.context import CryptContext
from sqlmodel import select

from src.config import settings
from src.db import SessionDep
from src.models import ProofUserRole, Users

load_dotenv(verbose=True)
SECRET_KEY = os.getenv("SECRET_KEY", "")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_file_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def hashPassword(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verifyPassword(plainPassword, hashedPassword) -> bool:
    return bcrypt.checkpw(plainPassword.encode("utf-8"), hashedPassword.encode("utf-8"))


def generate6DigitCode():
    return random.randint(100000, 999999)


def nowPlusMinutes(n: int):
    return datetime.now() + timedelta(minutes=n)


def create_token() -> str:
    """Generate a random opaque refresh token string."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash the refresh token before storing it in the DB."""
    return hashlib.sha256(token.encode()).hexdigest()


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def createAccessToken(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decodeToken(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None


def getUserIdFromToken(token: str) -> int | None:
    payload = decodeToken(token)
    if payload:
        return payload.get("id")
    return None


async def verifyUserTokenSession(request: Request):
    jwtToken = request.cookies.get("jwt")
    if not jwtToken:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user = decodeToken(jwtToken)

    return user


async def get_current_user(request: Request, session: SessionDep):
    jwtToken = request.cookies.get("jwt")
    if not jwtToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )

    payload = decodeToken(jwtToken)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    stmt = select(Users).where(Users.id == user_id)
    userDb = session.exec(stmt).first()

    if not userDb:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return userDb


def sanitize_text(value: str, max_length: int = 1000) -> str:
    """
    Sanitize free-text user input before storing in DB or rendering on frontend.
    - Trims and collapses whitespace
    - Escapes HTML to prevent XSS
    - Removes null bytes and control characters
    - Enforces max length
    """
    if not value or not isinstance(value, str):
        return value

    value = " ".join(value.split())
    value = html.escape(value, quote=True)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)

    if len(value) > max_length:
        value = value[:max_length]

    return value


def sanitize_prompt(value: str, max_length: int = 4000) -> str:
    """
    Sanitize system_prompt / judge_model before sending to LLM.
    Strips common prompt-injection patterns and enforces max length.
    """
    if not value or not isinstance(value, str):
        return value

    value = value.strip()

    injection_patterns = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all\s+prior",
        r"you\s+are\s+now\s+a\s+different\s+model",
        r"system\s*:\s*",
        r"assistant\s*:\s*",
    ]
    for pattern in injection_patterns:
        value = re.sub(pattern, "", value, flags=re.IGNORECASE)

    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)

    if len(value) > max_length:
        value = value[:max_length]

    return value


async def scan_file(file: UploadFile):
    try:
        cd = pyclamd.ClamdUnixSocket()
        loop = asyncio.get_event_loop()
        content = await file.read()
        await file.seek(0)

        scan_result = await loop.run_in_executor(None, cd.scan_stream, content)
        if scan_result and scan_result.get("stream"):
            status = scan_result["stream"][0]
            if status == "FOUND":
                virus_name = scan_result["stream"][1]
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": f"Malicious file detected: {virus_name}",
                        "code": "virus_detected",
                    },
                )
    except ConnectionError:
        pass
    except Exception:
        pass


async def get_current_active_user(current_user: Users = Depends(get_current_user)):
    return current_user


def transformRole(role: ProofUserRole):
    if role == ProofUserRole.VIEWER:
        return 1
    elif role == ProofUserRole.MEMBER:
        return 2
    elif role == ProofUserRole.ADMIN:
        return 3


def require_role(required_role: ProofUserRole):
    """Dependency that requires a specific role or higher."""

    def role_checker(current_user: Users = Depends(get_current_user)):
        if current_user.role == ProofUserRole.ADMIN:
            return current_user

        if transformRole(current_user.role) < transformRole(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role",
            )
        return current_user

    return role_checker


require_admin = require_role(ProofUserRole.ADMIN)
require_member = require_role(ProofUserRole.MEMBER)
require_viewer = require_role(ProofUserRole.VIEWER)


def verify_csrf(request: Request):
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    allowed = settings.FRONTEND_URL

    if origin and origin != allowed:
        raise HTTPException(status_code=403, detail="Invalid origin")
    if referer and allowed and not referer.startswith(allowed):
        raise HTTPException(status_code=403, detail="Invalid referer")
