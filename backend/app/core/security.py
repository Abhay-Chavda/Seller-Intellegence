from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# Keep password hashing simple and stable for this project.
# The local environment currently has a bcrypt/passlib compatibility problem,
# while pbkdf2_sha256 works reliably and remains fully supported by passlib.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        # Backward-compatibility for legacy plain-text rows.
        return plain_password == hashed_password


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
    normalized_subject = subject.strip().lower()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode = {"sub": normalized_subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        cleaned = token.strip()
        if cleaned.lower().startswith("bearer "):
            cleaned = cleaned[7:].strip()
        payload = jwt.decode(
            cleaned,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        subject = payload.get("sub")
        if not isinstance(subject, str):
            return None
        normalized_subject = subject.strip().lower()
        return normalized_subject or None
    except JWTError:
        return None
