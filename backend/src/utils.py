import hashlib
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Request, WebSocket
from passlib.context import CryptContext
import random
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

load_dotenv(verbose=True)
SECRET_KEY = os.getenv("SECRET_KEY", "")
pwd_context = CryptContext(
    schemes=["sha256_crypt"], deprecated="auto", bcrypt__rounds=12
)

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
        return payload.get("userId")
    return None


async def verifyUserTokenSession(request: Request):
    jwtToken = request.cookies.get("jwt")
    if not jwtToken:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user = decodeToken(jwtToken)

    return user


