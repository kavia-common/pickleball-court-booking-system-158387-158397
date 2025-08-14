"""Pydantic schemas for user-related payloads and responses."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Common fields for a user."""

    name: str = Field(..., description="Full name of the user")
    email: EmailStr = Field(..., description="Email address used for login")


class UserCreate(UserBase):
    """Payload for creating a new user (registration)."""

    password: str = Field(..., min_length=6, description="Password for the account")


class UserLogin(BaseModel):
    """Payload for user login."""

    email: EmailStr = Field(..., description="Registered email")
    password: str = Field(..., min_length=6, description="Password")


class AdminLogin(BaseModel):
    """Payload for admin login using environment-provisioned credentials."""

    username: str = Field(..., description="Admin username (ADMIN_USERNAME or ADMIN_EMAIL)")
    password: str = Field(..., min_length=6, description="Admin password (ADMIN_PASSWORD)")


class UserPublic(BaseModel):
    """Public representation of a user for responses."""

    id: int = Field(..., description="User identifier")
    name: str = Field(..., description="Display name")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field(..., description="Role of the principal (user or admin)")
