"""
User endpoints for profile and management.

Currently exposes:
- GET /users/me
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.security import get_current_user
from src.schemas.user import UserPublic

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user",
    description="Returns the currently authenticated user or admin.",
)
# PUBLIC_INTERFACE
def get_me(current: UserPublic = Depends(get_current_user)) -> UserPublic:
    """
    Retrieve the principal info for the current session.

    Parameters:
        current: Injected principal from bearer token.

    Returns:
        UserPublic representing the logged-in user or admin.
    """
    return current
