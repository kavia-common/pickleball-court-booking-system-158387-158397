"""
Admin endpoints for managing users and bookings.

Admin-only routes:
- GET /admin/users
- GET /admin/bookings
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.security import require_admin
from src.schemas.booking import BookingPublic
from src.schemas.court import CourtPublic
from src.schemas.user import UserPublic
from src.storage.db import db

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    response_model=list[UserPublic],
    summary="List users (admin)",
    description="Return all registered users. Admin access required.",
)
# PUBLIC_INTERFACE
def list_users(_: UserPublic = Depends(require_admin)) -> list[UserPublic]:
    """
    List all users in the system (admin only).
    """
    users = db.list_users()
    return [UserPublic(id=u["id"], name=u["name"], email=u["email"], role="user") for u in users]


@router.get(
    "/bookings",
    response_model=list[BookingPublic],
    summary="List all bookings (admin)",
    description="Return all bookings across courts and users. Admin access required.",
)
# PUBLIC_INTERFACE
def list_bookings(_: UserPublic = Depends(require_admin)) -> list[BookingPublic]:
    """
    List all bookings (admin only).
    """
    bookings = db.list_bookings()
    return [
        BookingPublic(
            id=b["id"],
            court_id=b["court_id"],
            owner_id=b["owner_id"],
            date=b["date"],
            start_time=b["start_time"],
            end_time=b["end_time"],
            declared_group_size=b["declared_group_size"],
            participants=list(b.get("participants", [])),
            status=b.get("status", "pending"),
        )
        for b in bookings
    ]


@router.get(
    "/courts",
    response_model=list[CourtPublic],
    summary="List all courts (admin)",
    description="Return all courts including inactive ones. Admin access required.",
)
# PUBLIC_INTERFACE
def list_courts_admin(_: UserPublic = Depends(require_admin)) -> list[CourtPublic]:
    """
    List all courts without filtering by active status (admin only).
    """
    courts = db.list_courts(active_only=False)
    return [CourtPublic(**c) for c in courts]
