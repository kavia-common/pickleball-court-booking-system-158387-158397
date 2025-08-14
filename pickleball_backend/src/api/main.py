from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import auth as auth_router
from src.routers import bookings as bookings_router
from src.routers import courts as courts_router
from src.routers import users as users_router
from src.routers import admin as admin_router

app = FastAPI(
    title="Pickleball Court Booking API",
    description=(
        "Backend service for managing pickleball courts, users, and bookings.\n\n"
        "Features:\n"
        "- User registration and login\n"
        "- Admin login and management endpoints\n"
        "- Courts listing and admin CRUD\n"
        "- Bookings with group size rules (min 2, confirmed at 4 participants)\n"
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "Auth", "description": "User and admin authentication"},
        {"name": "Users", "description": "User profile and account endpoints"},
        {"name": "Courts", "description": "Court browsing and admin management"},
        {"name": "Bookings", "description": "Booking creation, join, and management"},
        {"name": "Admin", "description": "Administrative endpoints"},
    ],
)

# CORS configuration - adjust origins in deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set specific origins from env or config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get(
    "/",
    summary="Health Check",
    description="Simple health check endpoint to verify the service is up.",
)
def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        JSON object indicating service health.
    """
    return {"message": "Healthy"}


# Include routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(courts_router.router)
app.include_router(bookings_router.router)
app.include_router(admin_router.router)
