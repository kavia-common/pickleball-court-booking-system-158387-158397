"""
Security helpers for authentication and authorization.

This module provides:
- Password hashing and verification (salted SHA-256).
- HMAC-signed token generation and decoding (JWT-like structure).
- FastAPI dependencies to retrieve the current user and enforce roles.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.config import get_settings
from src.storage.db import db
from src.schemas.user import UserPublic

# HTTP Bearer security scheme for OpenAPI and dependency injection
http_bearer = HTTPBearer(auto_error=True)


def _b64url_encode(data: bytes) -> str:
    """Encode bytes to base64url string without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    """Decode base64url string without padding into bytes."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


# PUBLIC_INTERFACE
def generate_salt() -> str:
    """Generate a random salt as a base64url string."""
    return _b64url_encode(hashlib.sha256(str(dt.datetime.utcnow().timestamp()).encode()).digest())[:16]


# PUBLIC_INTERFACE
def hash_password(password: str, salt: str) -> str:
    """
    Hash a password with a given salt using SHA-256.

    Args:
        password: Plaintext password.
        salt: Salt to use for hashing.

    Returns:
        Hex digest string of the salted hash.
    """
    return hashlib.sha256((salt + ":" + password).encode("utf-8")).hexdigest()


# PUBLIC_INTERFACE
def verify_password(plain_password: str, salt: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a salted hash.

    Args:
        plain_password: The provided password.
        salt: The stored salt for the user.
        password_hash: The stored salted hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return hmac.compare_digest(hash_password(plain_password, salt), password_hash)


# PUBLIC_INTERFACE
def create_access_token(user_id: int | None, role: str, expires_minutes: Optional[int] = None) -> str:
    """
    Create an HMAC-signed token (JWT-like) for a user/admin.

    Args:
        user_id: The user's ID (None for built-in admin if not stored).
        role: 'user' or 'admin'.
        expires_minutes: Optional override for expiration time.

    Returns:
        A compact token string.

    The token structure: base64url(header).base64url(payload).base64url(signature)
    where signature = HMAC_SHA256(secret, header.payload)
    """
    settings = get_settings()
    exp_minutes = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes

    header = {"alg": "HS256", "typ": "JWT"}
    now = int(dt.datetime.utcnow().timestamp())
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + exp_minutes * 60,
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(settings.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


# PUBLIC_INTERFACE
def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify an HMAC-signed token.

    Args:
        token: The token string.

    Returns:
        The decoded payload dict.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    settings = get_settings()
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = _b64url_encode(
        hmac.new(settings.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    )

    if not hmac.compare_digest(expected_sig, signature_b64):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload") from exc

    now = int(dt.datetime.utcnow().timestamp())
    if int(payload.get("exp", 0)) < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")

    return payload


# PUBLIC_INTERFACE
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> UserPublic:
    """
    FastAPI dependency that returns the current authenticated user.

    Args:
        credentials: Parsed Authorization header (Bearer token).

    Returns:
        UserPublic for the current session.

    Notes:
        - Admin tokens are supported and will return a pseudo-user with role 'admin'.
    """
    payload = decode_token(credentials.credentials)
    role = payload.get("role")
    sub = payload.get("sub")

    if role == "admin":
        # Pseudo admin user
        return UserPublic(id=0, name="Administrator", email="admin@system.local", role="admin")

    if role != "user" or sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    user = db.get_user_by_id(int(sub))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return UserPublic(id=user["id"], name=user["name"], email=user["email"], role="user")


# PUBLIC_INTERFACE
def require_admin(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """
    FastAPI dependency to ensure the current principal is an admin.

    Args:
        user: The current authenticated user.

    Returns:
        The same user if admin.

    Raises:
        HTTPException: If the user is not an admin.
    """
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
