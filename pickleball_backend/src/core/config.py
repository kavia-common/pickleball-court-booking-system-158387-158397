"""
Application configuration utilities for the Pickleball Backend.

This module centralizes configuration values and environment variable access.
It does not read or write .env files directly; orchestration will handle
environment setup. Use os.getenv to access variables.

Env variables used:
- SECRET_KEY: Secret key for signing tokens.
- ACCESS_TOKEN_EXPIRE_MINUTES: Token lifetime in minutes (default: 120).
- ADMIN_USERNAME: Username for the built-in admin user (no registration).
- ADMIN_PASSWORD: Password for the built-in admin user.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Container for application settings loaded from environment variables."""

    secret_key: str
    access_token_expire_minutes: int
    admin_username: str | None
    admin_password: str | None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """
    Load and return application settings from environment.

    Returns:
        Settings: Immutable configuration including secrets and token expiry.

    Notes:
        - SECRET_KEY should be provided in the environment for production use.
        - ADMIN_USERNAME and ADMIN_PASSWORD must be set to enable admin login.
    """
    secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")  # For development only
    expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    admin_username = os.getenv("ADMIN_USERNAME") or os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    return Settings(
        secret_key=secret_key,
        access_token_expire_minutes=expire,
        admin_username=admin_username,
        admin_password=admin_password,
    )
