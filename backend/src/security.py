from cryptography.fernet import Fernet

from .config import settings

_ENCRYPTION_KEY = settings.ENCRYPTION_KEY
if not _ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is required")

_fernet = Fernet(
    _ENCRYPTION_KEY.encode() if isinstance(_ENCRYPTION_KEY, str) else _ENCRYPTION_KEY
)


def encrypt_api_key(api_key: str) -> str:
    return _fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_api_key: str) -> str:
    return _fernet.decrypt(encrypted_api_key.encode()).decode()
