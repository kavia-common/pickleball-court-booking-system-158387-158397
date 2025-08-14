# Pickleball Backend (FastAPI)

This service exposes REST APIs for user/admin authentication, court management, and bookings with group-size rules:
- Bookings require a minimum declared group size of 2.
- A reservation is only confirmed when the group reaches 4 participants (including the owner).
- Separate admin and user authentication.

## Run locally

1. Create and fill your `.env` from `.env.example`.
2. Install dependencies:
   pip install -r requirements.txt
3. Start the API (from project root of this container):
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

Open API docs at: http://localhost:8000/docs

## Auth

- User register: POST /auth/register
- User login: POST /auth/login
- Admin login: POST /auth/admin/login

Use the returned `access_token` as `Authorization: Bearer <token>` for subsequent requests.

## Courts

- Public list: GET /courts
- Get one: GET /courts/{id}
- Admin create: POST /courts
- Admin update: PATCH /courts/{id}
- Admin delete: DELETE /courts/{id}

## Bookings

- Create: POST /bookings
- My bookings: GET /bookings/my
- Get booking: GET /bookings/{id}
- Join booking: POST /bookings/{id}/join
- Cancel booking: DELETE /bookings/{id} (owner only or admin via admin privileges)

## Admin

- List users: GET /admin/users
- List courts (all): GET /admin/courts
- List bookings: GET /admin/bookings
