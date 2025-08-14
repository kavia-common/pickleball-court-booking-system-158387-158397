"""Schemas for booking operations and responses."""

from datetime import date as Date, time as Time
from pydantic import BaseModel, Field, conint


class BookingCreate(BaseModel):
    """Payload to create a new booking."""

    court_id: int = Field(..., description="Court to book")
    date: Date = Field(..., description="Booking date (YYYY-MM-DD)")
    start_time: Time = Field(..., description="Start time for the reservation (HH:MM)")
    end_time: Time = Field(..., description="End time for the reservation (HH:MM)")
    initial_group_size: conint(ge=2, le=4) = Field(
        ..., description="Declared group size at booking time (min 2, max 4)"
    )


class BookingPublic(BaseModel):
    """Public representation of a booking."""

    id: int = Field(..., description="Booking identifier")
    court_id: int = Field(..., description="Court identifier")
    owner_id: int = Field(..., description="User ID of the booking owner")
    date: Date = Field(..., description="Booking date")
    start_time: Time = Field(..., description="Start time")
    end_time: Time = Field(..., description="End time")
    declared_group_size: int = Field(..., description="Declared group size at booking creation")
    participants: list[int] = Field(..., description="User IDs of participants who joined")
    status: str = Field(..., description="Booking status: 'pending' or 'confirmed'")


class JoinBookingResponse(BaseModel):
    """Response returned when a user joins a booking."""

    booking: BookingPublic = Field(..., description="Updated booking after joining")
    message: str = Field(..., description="Informational message about the join outcome")
