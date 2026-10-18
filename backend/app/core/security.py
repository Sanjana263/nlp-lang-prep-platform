from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# Used to burn the same CPU time when an email doesn't exist, so response timing
# doesn't reveal which emails are registered (FR-1.5).
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user_id: int, role: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=s.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, s.JWT_SECRET, algorithm=s.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError if invalid or expired."""
    s = get_settings()
    return jwt.decode(token, s.JWT_SECRET, algorithms=[s.JWT_ALGORITHM])
