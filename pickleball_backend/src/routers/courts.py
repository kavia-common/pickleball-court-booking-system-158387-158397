"""
Court management endpoints.

Public:
- GET /courts
- GET /courts/{court_id}

Admin-only:
- POST /courts
- PATCH /courts/{court_id}
- DELETE /courts/{court_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.core.security import require_admin
from src.schemas.court import CourtCreate, CourtPublic, CourtUpdate
from src.schemas.user import UserPublic
from src.storage.db import db

router = APIRouter(prefix="/courts", tags=["Courts"])


@router.get(
    "",
    response_model=list[CourtPublic],
    summary="List courts",
    description="List available courts. By default, only active courts are returned.",
)
# PUBLIC_INTERFACE
def list_courts(active_only: bool = Query(True, description="Only return active courts")) -> list[CourtPublic]:
    """
    List courts in the system.

    Parameters:
        active_only: Filter for active courts only.

    Returns:
        List of CourtPublic objects.
    """
    courts = db.list_courts(active_only=active_only)
    return [CourtPublic(**c) for c in courts]


@router.get(
    "/{court_id}",
    response_model=CourtPublic,
    summary="Get court details",
    description="Retrieve a single court by its identifier.",
)
# PUBLIC_INTERFACE
def get_court(court_id: int = Path(..., description="Court identifier")) -> CourtPublic:
    """
    Get a single court by ID.
    """
    court = db.get_court(court_id)
    if not court:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    return CourtPublic(**court)


@router.post(
    "",
    response_model=CourtPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create court (admin)",
    description="Create a new court. Admin access required.",
)
# PUBLIC_INTERFACE
def create_court(payload: CourtCreate, _: UserPublic = Depends(require_admin)) -> CourtPublic:
    """
    Create a new court (admin only).
    """
    court = db.create_court(name=payload.name, location=payload.location, is_active=payload.is_active)
    return CourtPublic(**court)


@router.patch(
    "/{court_id}",
    response_model=CourtPublic,
    summary="Update court (admin)",
    description="Update an existing court's details. Admin access required.",
)
# PUBLIC_INTERFACE
def update_court(
    payload: CourtUpdate,
    _: UserPublic = Depends(require_admin),
    court_id: int = Path(..., description="Court identifier"),
) -> CourtPublic:
    """
    Update a court (admin only).
    """
    updated = db.update_court(court_id, **payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    return CourtPublic(**updated)


@router.delete(
    "/{court_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete court (admin)",
    description="Remove a court by ID. Admin access required.",
)
# PUBLIC_INTERFACE
def delete_court(
    _: UserPublic = Depends(require_admin),
    court_id: int = Path(..., description="Court identifier"),
) -> None:
    """
    Delete a court (admin only).
    """
    ok = db.delete_court(court_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court not found")
    return None
