"""Authentication related schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.schemas.user import UserPublic


class TokenResponse(BaseModel):
    """Response returned after successful authentication."""

    access_token: str = Field(..., description="Bearer token to use in Authorization header")
    token_type: str = Field(default="bearer", description="Type of token")
    user: UserPublic = Field(..., description="Authenticated user information")
