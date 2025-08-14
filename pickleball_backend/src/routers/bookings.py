"""
Booking endpoints implementing group size rules.

Rules:
- Minimum declared group size at creation is 2.
- A booking is 'confirmed' when 4 participants have joined (owner included).
- Prevent overlapping bookings on the same court and date.

Endpoints:
- POST /bookings
- GET /bookings/my
- GET /bookings/{booking_id}
- POST /bookings/{booking_id}/join
- DELETE /bookings/{booking_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.core.security import get_current_user
from src.schemas.booking import BookingCreate, BookingPublic, JoinBookingResponse
from src.schemas.user import UserPublic
from src.storage.db import db

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=BookingPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create booking",
    description="Create a booking with a declared group size (min 2, max 4). Initial status is pending.",
)
# PUBLIC_INTERFACE
def create_booking(payload: BookingCreate, current: UserPublic = Depends(get_current_user)) -> BookingPublic:
    """
    Create a new booking for a court.

    Parameters:
        payload: BookingCreate with court, date, start/end time, initial_group_size.
        current: The authenticated user creating the booking.

    Returns:
        BookingPublic representing the created booking.

    Raises:
        HTTPException 400: On validation or overlap conflicts.
        HTTPException 404: If the court does not exist.
    """
    try:
        booking = db.create_booking(
            court_id=payload.court_id,
            owner_id=current.id,
            booking_date=payload.date,
            start_time=payload.start_time,
            end_time=payload.end_time,
            initial_group_size=payload.initial_group_size,
        )
    except ValueError as exc:
        message = str(exc)
        if "Court" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return _to_public(booking)


@router.get(
    "/my",
    response_model=list[BookingPublic],
    summary="List my bookings",
    description="Return bookings that the current user participates in (including ownership).",
)
# PUBLIC_INTERFACE
def list_my_bookings(current: UserPublic = Depends(get_current_user)) -> list[BookingPublic]:
    """
    List bookings for the current user.
    """
    bookings = db.list_user_bookings(current.id)
    return [_to_public(b) for b in bookings]


@router.get(
    "/{booking_id}",
    response_model=BookingPublic,
    summary="Get booking details",
    description="Retrieve a booking by its identifier.",
)
# PUBLIC_INTERFACE
def get_booking(booking_id: int = Path(..., description="Booking identifier")) -> BookingPublic:
    """
    Retrieve a single booking by ID.
    """
    booking = db.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return _to_public(booking)


@router.post(
    "/{booking_id}/join",
    response_model=JoinBookingResponse,
    summary="Join a booking",
    description="Join an existing booking until the group reaches 4 to confirm.",
)
# PUBLIC_INTERFACE
def join_booking(
    booking_id: int = Path(..., description="Booking identifier"),
    current: UserPublic = Depends(get_current_user),
) -> JoinBookingResponse:
    """
    Join an existing booking as a participant.

    Parameters:
        booking_id: ID of the booking to join.
        current: Authenticated user joining the booking.

    Returns:
        JoinBookingResponse with updated booking and message.

    Raises:
        HTTPException 400: If already joined or full.
        HTTPException 404: If booking not found.
    """
    try:
        booking = db.join_booking(booking_id, current.id)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if "not found" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message) from exc

    msg = "Booking confirmed with 4 participants!" if booking["status"] == "confirmed" else "Joined booking successfully."
    return JoinBookingResponse(booking=_to_public(booking), message=msg)


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel booking",
    description="Delete a booking. Only the owner or an admin (via admin endpoints) may cancel.",
)
# PUBLIC_INTERFACE
def delete_booking(
    booking_id: int = Path(..., description="Booking identifier"),
    current: UserPublic = Depends(get_current_user),
) -> None:
    """
    Delete a booking if the current user is the owner.

    Raises:
        HTTPException 403: If the current user is not the owner.
        HTTPException 404: If booking not found.
    """
    booking = db.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if current.role != "admin" and booking["owner_id"] != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can cancel this booking")

    ok = db.delete_booking(booking_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return None


def _to_public(b: dict) -> BookingPublic:
    """Internal helper to map booking dict to public schema."""
    return BookingPublic(
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
