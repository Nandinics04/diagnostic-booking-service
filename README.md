# Diagnostic Booking API

Backend service for diagnostic-test bookings and simulated payments.

A patient signs up, browses diagnostic centres and tests, books an appointment, and pays through a mock payment flow. A separate webhook accepts the payment result from a simulated provider. There is no real payment gateway and no frontend. The API is exercised from the interactive docs.

Stack: Python 3.13, FastAPI, PostgreSQL, SQLAlchemy, JWT, pytest.

## How to run locally

1. Install Python 3.13 and PostgreSQL 16 or newer. This project was developed with PostgreSQL 18. The `psql` tools directory must be on your `PATH`.

2. Create the application database:

```powershell
psql -U postgres -h localhost -c "CREATE DATABASE eve_booking;"
```

3. From the project root, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

4. Create a `.env` file in the project root. Do not commit it. `.gitignore` already excludes `.env`.

```text
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/eve_booking
JWT_SECRET_KEY=paste_a_long_random_string_here
```

Generate a secret with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

If the database password contains `@`, `#`, `%`, or `/`, URL-encode that character inside `DATABASE_URL`.

5. Start the API:

```powershell
uvicorn main:app --reload
```

Tables are created on startup from the SQLAlchemy models. Open:

- http://127.0.0.1:8000 for the health message
- http://127.0.0.1:8000/docs for Swagger UI
- http://127.0.0.1:8000/health/db to confirm PostgreSQL answers

### Tests

Tests use a second database so they can drop tables without touching `eve_booking`.

```powershell
psql -U postgres -h localhost -c "CREATE DATABASE eve_booking_test;"
python -m pytest -q
```

`tests/conftest.py` rewrites `DATABASE_URL` to `eve_booking_test` before the app starts. The suite covers signup and the current-user route, a booking call with no token, a second payment on an already confirmed booking, and a webhook sent twice with the same event id.

## Authentication

Passwords are stored as Argon2 hashes. Login returns a JWT signed with HS256. The token expires after 30 minutes. Protected routes expect:

```text
Authorization: Bearer <access_token>
```

In Swagger, call `POST /auth/login`, copy `access_token`, click **Authorize**, and paste the token. The login form field is named `username`; put the user's email there.

## API endpoints

### Health

| Method | Path | Auth | Success |
|---|---|---|---|
| GET | `/` | No | 200 |
| GET | `/health/db` | No | 200 when PostgreSQL accepts `SELECT 1` |

### Auth

| Method | Path | Auth | Success |
|---|---|---|---|
| POST | `/auth/signup` | No | 201 |
| POST | `/auth/login` | No | 200 and a bearer token |
| GET | `/auth/me` | Yes | 200 |

Signup:

```json
{
  "full_name": "Nandini",
  "email": "nandini@example.com",
  "password": "secret12"
}
```

`full_name` is 3–25 characters. `password` is 7–25 characters. A duplicate email returns `400`. An invalid email or a short password returns `422`. The response never includes the password hash.

Login is form data, not JSON:

```text
username=nandini@example.com&password=secret12
```

A wrong email or password returns `401`. `GET /auth/me` without a token returns `401`.

### Centres and tests

| Method | Path | Auth | Success |
|---|---|---|---|
| POST | `/centres` | Yes | 201 |
| GET | `/centres` | No | 200 |
| GET | `/centres/{centre_id}` | No | 200 |
| POST | `/centres/{centre_id}/tests` | Yes | 201 |
| GET | `/centres/{centre_id}/tests` | No | 200 |

Create a centre:

```json
{
  "name": "City Lab",
  "location": "Hyderabad"
}
```

Add a test. Price must be greater than 0 and can have two decimal places:

```json
{
  "name": "Blood Test",
  "price": "100.00"
}
```

An unknown centre id returns `404`. A missing token on a create route returns `401`.

### Bookings

| Method | Path | Auth | Success |
|---|---|---|---|
| POST | `/bookings` | Yes | 201, status `PENDING` |
| GET | `/bookings` | Yes | 200, only the caller's bookings |
| GET | `/bookings/{booking_id}` | Yes | 200 |
| POST | `/bookings/{booking_id}/cancel` | Yes | 200, status `CANCELLED` |

Create a booking. The body does not include `user_id`, `centre_id`, or `amount`:

```json
{
  "test_id": 1,
  "appointment_at": "2026-10-01T10:30:00+05:30"
}
```

The user is taken from the token. The amount is copied from the test price at this moment, so a later price change does not rewrite the booking. The centre is taken from the test, and the response includes `centre_id` and `centre_name`. The appointment must include a timezone and must be in the future. A missing timezone or a past time returns `400`. An unknown test returns `404`.

Another user's booking returns `403`. Cancelling is allowed only while the status is `PENDING`. Cancelling again, or cancelling a confirmed or failed booking, returns `400`.

### Payments

| Method | Path | Auth | Success |
|---|---|---|---|
| POST | `/payments/` | Yes | 201 |
| POST | `/payments/webhook` | No | 200 |

The user pays for their own pending booking. `outcome` is `SUCCESS` or `FAILED`. This is a mock, so the request chooses the result instead of a real gateway:

```json
{
  "booking_id": 1,
  "outcome": "SUCCESS"
}
```

`SUCCESS` stores a payment and sets the booking to `CONFIRMED`. `FAILED` stores a payment and sets the booking to `FAILED`. Each user payment gets a new random `provider_event_id`. A second payment on that booking returns `409` because the booking is no longer `PENDING`. Paying for another user's booking returns `403`. An unknown booking returns `404`.

### Payment webhook

The webhook is the simulated provider reporting a result. It does not use a login token.

```json
{
  "event_id": "evt-100",
  "booking_id": 3,
  "status": "FAILED"
}
```

`event_id` is stored in `payments.provider_event_id`, which is unique. The first delivery creates one payment and updates the booking. The same `event_id` sent again returns the original payment and does not insert another row or change the booking again. Two deliveries that arrive together are covered by that unique constraint: the second commit rolls back and returns the row the first commit saved.

A webhook for a booking that is not `PENDING` returns `409` and leaves the status unchanged. A cancelled booking stays `CANCELLED` even if a late webhook says `SUCCESS`. An unknown booking id returns `404`. `event_id` must be 3–255 characters. `status` accepts only `SUCCESS` or `FAILED`; anything else returns `422`.

Booking status moves in one direction:

```text
PENDING --cancel--> CANCELLED
PENDING --payment SUCCESS--> CONFIRMED
PENDING --payment FAILED--> FAILED
```

## Database design

PostgreSQL database: `eve_booking`. Schema: `public`. The ORM creates the tables with `Base.metadata.create_all` when the app starts.

### `users`

| Column | Notes |
|---|---|
| `id` | Primary key |
| `full_name` | Required |
| `email` | Required, unique, indexed |
| `hashed_password` | Argon2 hash, never returned by the API |
| `created_at` | Set by the database |

### `centres`

| Column | Notes |
|---|---|
| `id` | Primary key |
| `name` | Required |
| `location` | Required |

### `diagnostic_tests`

| Column | Notes |
|---|---|
| `id` | Primary key |
| `centre_id` | Foreign key to `centres.id` |
| `name` | Required |
| `price` | `NUMERIC(10, 2)`, greater than 0 at the API |

A test belongs to one centre. The same test name can exist at another centre with a different price.

### `bookings`

| Column | Notes |
|---|---|
| `id` | Primary key |
| `user_id` | Foreign key to `users.id` |
| `test_id` | Foreign key to `diagnostic_tests.id` |
| `appointment_at` | Timezone-aware timestamp |
| `amount` | `NUMERIC(10, 2)`, copied from the test price |
| `status` | `PENDING`, `CONFIRMED`, `FAILED`, `CANCELLED` |
| `created_at` | Set by the database |

The centre is not stored again on the booking. It is reached through `diagnostic_tests.centre_id`, which keeps the test and the centre from disagreeing.

### `payments`

| Column | Notes |
|---|---|
| `id` | Primary key |
| `booking_id` | Foreign key to `bookings.id` |
| `amount` | Copied from the booking |
| `status` | `SUCCESS` or `FAILED` |
| `provider_event_id` | Unique. This is the webhook idempotency key |
| `created_at` | Set by the database |

A booking can have more than one payment row only when the event ids differ and the booking was still `PENDING` for each of them. The status check stops a second payment after the first one confirms or fails the booking.

## Assumptions

- Any logged-in user may create centres and tests. The assignment does not define an admin role, so there is no separate staff account.
- Listing centres and tests is public. Creating them, booking, and paying require a JWT.
- The booking request accepts `test_id` and `appointment_at` only. User, price, and centre are derived on the server.
- A booking can be cancelled only from `PENDING`.
- A payment is accepted only while the booking is `PENDING`.
- `POST /payments/` is a mock. The caller sends `SUCCESS` or `FAILED` so both results can be demonstrated. A real gateway would decide the result.
- `POST /payments/webhook` is unauthenticated because the caller is the simulated provider, not the patient. Repeating `event_id` is the idempotency guarantee implemented here.
- A repeated webhook returns the existing payment with HTTP 200. It is not treated as an error.
- A second user click on `POST /payments/` generates a new event id, then receives `409` because the booking is no longer pending.
- `create_all` creates missing tables and does not alter tables that already exist.

## What I would improve with more time

- Verify a provider signature on the webhook, so an anonymous caller cannot submit a payment result.
- Split the mock flow so `POST /payments/` only starts a payment, and only the webhook moves the booking to `CONFIRMED` or `FAILED`.
- Add an admin role, and allow only that role to create centres and tests.
- Replace `create_all` with Alembic migrations so column changes are applied safely.
- Add pagination on centre, test, and booking lists.
- Add Docker Compose for the API and PostgreSQL.
- Extend the tests to cover cancellation, a booking owned by another user, a webhook for a missing booking, and a late webhook for a cancelled booking.
- Add rate limiting on login and the webhook.
