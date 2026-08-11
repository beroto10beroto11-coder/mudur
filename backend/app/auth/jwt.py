"""
JWT token creation and verification.
"""
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


# ──────────────────────────────────────────────────────────────────────────────
# Token creation
# ──────────────────────────────────────────────────────────────────────────────

def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token() -> tuple[str, str]:
    """
    Create a refresh token.
    Returns (raw_token, token_hash).
    Only the hash is stored in the database.
    """
    raw_token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    """Hash a refresh token for storage/lookup."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Token verification
# ──────────────────────────────────────────────────────────────────────────────

def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    Raises UnauthorizedError on failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        raise UnauthorizedError(f"Geçersiz veya süresi dolmuş token: {e}") from e

    if payload.get("type") != "access":
        raise UnauthorizedError("Geçersiz token türü.")

    return payload


def get_token_expiry_datetime() -> datetime:
    """Returns when a new refresh token should expire."""
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
