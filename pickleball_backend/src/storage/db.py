"""
Simple in-memory data storage.

This is a thread-safe, ephemeral store intended for demo and development.
It can be replaced by a persistent database without changing the API surface.
"""

from __future__ import annotations

import threading
from datetime import date, time
from typing import Dict, List, Optional


class InMemoryDB:
    """Thread-safe in-memory database for users, courts, and bookings."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

        self._users: Dict[int, Dict] = {}
        self._users_by_email: Dict[str, int] = {}
        self._courts: Dict[int, Dict] = {}
        self._bookings: Dict[int, Dict] = {}

        self._user_id = 0
        self._court_id = 0
        self._booking_id = 0

        # Seed with sample courts for convenience
        self.create_court(name="Court A", location="Main Center")
        self.create_court(name="Court B", location="Main Center")
        self.create_court(name="Court C", location="Annex")

    # ------------- User operations -------------

    # PUBLIC_INTERFACE
    def create_user(self, name: str, email: str, password_hash: str, salt: str) -> Dict:
        """Create and store a new user. Raises ValueError if email exists."""
        with self._lock:
            if email.lower() in self._users_by_email:
                raise ValueError("Email already registered")
            self._user_id += 1
            user = {
                "id": self._user_id,
                "name": name,
                "email": email.lower(),
                "password_hash": password_hash,
                "salt": salt,
            }
            self._users[user["id"]] = user
            self._users_by_email[user["email"]] = user["id"]
            return user

    # PUBLIC_INTERFACE
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Return user dict by email if exists."""
        with self._lock:
            uid = self._users_by_email.get(email.lower())
            return self._users.get(uid) if uid else None

    # PUBLIC_INTERFACE
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Return user dict by ID if exists."""
        with self._lock:
            return self._users.get(user_id)

    # PUBLIC_INTERFACE
    def list_users(self) -> List[Dict]:
        """List all users."""
        with self._lock:
            return list(self._users.values())

    # ------------- Court operations -------------

    # PUBLIC_INTERFACE
    def create_court(self, name: str, location: Optional[str] = None, is_active: bool = True) -> Dict:
        """Create a new court."""
        with self._lock:
            self._court_id += 1
            court = {
                "id": self._court_id,
                "name": name,
                "location": location,
                "is_active": is_active,
            }
            self._courts[court["id"]] = court
            return court

    # PUBLIC_INTERFACE
    def update_court(self, court_id: int, **kwargs) -> Optional[Dict]:
        """Update fields of a court."""
        with self._lock:
            court = self._courts.get(court_id)
            if not court:
                return None
            court.update({k: v for k, v in kwargs.items() if k in {"name", "location", "is_active"}})
            return court

    # PUBLIC_INTERFACE
    def delete_court(self, court_id: int) -> bool:
        """Delete a court by ID. Returns True if deleted."""
        with self._lock:
            return self._courts.pop(court_id, None) is not None

    # PUBLIC_INTERFACE
    def get_court(self, court_id: int) -> Optional[Dict]:
        """Fetch a court by ID."""
        with self._lock:
            return self._courts.get(court_id)

    # PUBLIC_INTERFACE
    def list_courts(self, active_only: bool = True) -> List[Dict]:
        """List courts, optionally filtering for active ones."""
        with self._lock:
            courts = list(self._courts.values())
            return [c for c in courts if c["is_active"]] if active_only else courts

    # ------------- Booking operations -------------

    # PUBLIC_INTERFACE
    def create_booking(
        self,
        court_id: int,
        owner_id: int,
        booking_date: date,
        start_time: time,
        end_time: time,
        initial_group_size: int,
    ) -> Dict:
        """
        Create a booking with group size (min 2, pending until 4 people join).

        Raises:
            ValueError: on invalid court, time overlap, or constraints violation.
        """
        with self._lock:
            if court_id not in self._courts:
                raise ValueError("Court does not exist")

            if start_time >= end_time:
                raise ValueError("Start time must be before end time")

            # Prevent overlapping bookings on the same court and date
            for b in self._bookings.values():
                if b["court_id"] == court_id and b["date"] == booking_date:
                    s1, e1 = b["start_time"], b["end_time"]
                    if start_time < e1 and s1 < end_time:
                        raise ValueError("Time slot overlaps with an existing booking")

            if initial_group_size < 2 or initial_group_size > 4:
                raise ValueError("Group size must be between 2 and 4")

            self._booking_id += 1
            booking = {
                "id": self._booking_id,
                "court_id": court_id,
                "owner_id": owner_id,
                "date": booking_date,
                "start_time": start_time,
                "end_time": end_time,
                # Participants contain real user IDs that joined (owner included by default)
                "participants": [owner_id],
                # Declared group size at creation; informative; status derives from participants count
                "declared_group_size": initial_group_size,
                "status": "pending",
                "created_at": None,  # placeholder
            }
            self._bookings[booking["id"]] = booking
            return booking

    # PUBLIC_INTERFACE
    def get_booking(self, booking_id: int) -> Optional[Dict]:
        """Fetch a booking by ID."""
        with self._lock:
            return self._bookings.get(booking_id)

    # PUBLIC_INTERFACE
    def list_bookings(self) -> List[Dict]:
        """List all bookings."""
        with self._lock:
            return list(self._bookings.values())

    # PUBLIC_INTERFACE
    def list_user_bookings(self, user_id: int) -> List[Dict]:
        """List bookings where the user participates (including ownership)."""
        with self._lock:
            return [b for b in self._bookings.values() if user_id in b.get("participants", [])]

    # PUBLIC_INTERFACE
    def delete_booking(self, booking_id: int) -> bool:
        """Delete a booking by ID."""
        with self._lock:
            return self._bookings.pop(booking_id, None) is not None

    # PUBLIC_INTERFACE
    def join_booking(self, booking_id: int, user_id: int) -> Dict:
        """Add a user to the booking if capacity allows and user not already joined."""
        with self._lock:
            booking = self._bookings.get(booking_id)
            if not booking:
                raise ValueError("Booking not found")

            participants = booking["participants"]
            if user_id in participants:
                raise ValueError("User already joined this booking")

            if len(participants) >= 4:
                raise ValueError("Booking group is already full")

            participants.append(user_id)
            # Confirm booking when all 4 participants are present
            booking["status"] = "confirmed" if len(participants) >= 4 else "pending"
            return booking


# Module-level singleton DB instance for simplicity
db = InMemoryDB()
