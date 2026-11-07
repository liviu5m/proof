import hashlib
import os
import re
import html
from dotenv import load_dotenv
from fastapi import HTTPException, Request, UploadFile, status, WebSocket
from passlib.context import CryptContext
import random
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from sqlmodel import select
from src.db import SessionDep
from src.models import Users
import pyclamd
import asyncio

load_dotenv(verbose=True)
SECRET_KEY = os.getenv("SECRET_KEY", "")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_file_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def hashPassword(password: str):
    return pwd_context.hash(password)


def verifyPassword(plainPassword, hashedPassword):
    return pwd_context.verify(plainPassword, hashedPassword)


def generate6DigitCode():
    return random.randint(100000, 999999)


def nowPlusMinutes(n: int):
    return datetime.now() + timedelta(minutes=n)


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def createAccessToken(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decodeToken(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None


def getUserIdFromToken(token: str) -> Optional[int]:
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

    payload = decodeToken(jwtToken)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    stmt = select(Users).where(Users.id == user_id)
    userDb = session.exec(stmt).first()

    if not userDb:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

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
    cd = pyclamd.ClamDUnixSocket() 
    loop = asyncio.get_event_loop()
    content = await file.read()
    await file.seek(0) 
    
    scan_result = await loop.run_in_executor(None, cd.scan_stream, content)
    if scan_result and scan_result.get('stream'):
        status = scan_result['stream'][0]
        if status == 'FOUND':
            virus_name = scan_result['stream'][1]
            raise HTTPException(
                status_code=400,
                detail={"error": f"Malicious file detected: {virus_name}", "code": "virus_detected"}
            )
