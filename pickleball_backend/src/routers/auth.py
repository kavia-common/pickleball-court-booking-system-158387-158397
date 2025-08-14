"""
Authentication routes for users and admins.

Provides:
- POST /auth/register
- POST /auth/login
- POST /auth/admin/login
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.core.config import get_settings
from src.core.security import create_access_token, generate_salt, hash_password, verify_password
from src.schemas.auth import TokenResponse
from src.schemas.user import AdminLogin, UserCreate, UserLogin, UserPublic
from src.storage.db import db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account and receive an access token for subsequent requests.",
)
# PUBLIC_INTERFACE
def register(payload: UserCreate) -> TokenResponse:
    """
    Register a user.

    Parameters:
        payload: UserCreate containing name, email, and password.

    Returns:
        TokenResponse with access_token and user details.

    Raises:
        HTTPException 400: If the email is already registered.
    """
    salt = generate_salt()
    password_hash = hash_password(payload.password, salt)
    try:
        user = db.create_user(name=payload.name, email=payload.email, password_hash=password_hash, salt=salt)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token = create_access_token(user_id=user["id"], role="user")
    return TokenResponse(
        access_token=token,
        user=UserPublic(id=user["id"], name=user["name"], email=user["email"], role="user"),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login as a user",
    description="Authenticate with email and password to receive a bearer token.",
)
# PUBLIC_INTERFACE
def login(payload: UserLogin) -> TokenResponse:
    """
    User login.

    Parameters:
        payload: UserLogin with email and password.

    Returns:
        TokenResponse upon successful authentication.

    Raises:
        HTTPException 401: If credentials are invalid.
    """
    user = db.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user["salt"], user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user_id=user["id"], role="user")
    return TokenResponse(
        access_token=token,
        user=UserPublic(id=user["id"], name=user["name"], email=user["email"], role="user"),
    )


@router.post(
    "/admin/login",
    response_model=TokenResponse,
    summary="Login as admin",
    description="Admin authentication with credentials provided via environment variables.",
)
# PUBLIC_INTERFACE
def admin_login(payload: AdminLogin) -> TokenResponse:
    """
    Admin login using environment-provisioned credentials.

    Parameters:
        payload: AdminLogin with username and password.

    Returns:
        TokenResponse with admin role on success.

    Raises:
        HTTPException 401: If credentials are invalid or not configured.
    """
    settings = get_settings()
    if not settings.admin_username or not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin credentials not configured. Set ADMIN_USERNAME and ADMIN_PASSWORD.",
        )

    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    token = create_access_token(user_id=None, role="admin")
    return TokenResponse(
        access_token=token,
        user=UserPublic(id=0, name="Administrator", email="admin@system.local", role="admin"),
    )
