from datetime import datetime, timedelta, timezone

def signup_and_login(client):
    client.post(
        "/auth/signup",
        json={
            "full_name": "Nandini",
            "email": "nandini@example.com",
            "password": "secret12",
        },
    )
    response = client.post(
        "/auth/login",
        data={"username": "nandini@example.com", "password": "secret12"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def create_pending_booking(client, headers):
    centre = client.post(
        "/centres",
        json={"name": "City Lab", "location": "Hyderabad"},
        headers=headers,
    )
    centre_id = centre.json()["id"]
    test = client.post(
        f"/centres/{centre_id}/tests",
        json={"name": "Blood Test", "price": "100.00"},
        headers=headers,
    )
    appointment = datetime.now(timezone.utc) + timedelta(days=1)
    booking = client.post(
        "/bookings",
        json={"test_id": test.json()["id"], "appointment_at": appointment.isoformat()},
        headers=headers,
    )
    return booking.json()["id"]

def test_signup_and_me(client):
    headers = signup_and_login(client)
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "nandini@example.com"
    
def test_booking_requires_login(client):
    response = client.post(
        "/bookings",
        json={"test_id": 1, "appointment_at": "2026-10-01T10:00:00+05:30"},
    )
    assert response.status_code == 401


def test_second_payment_is_rejected(client):
    headers = signup_and_login(client)
    booking_id = create_pending_booking(client, headers)
    first = client.post(
        "/payments/",
        json={"booking_id": booking_id, "outcome": "SUCCESS"},
        headers=headers,
    )
    second = client.post(
        "/payments/",
        json={"booking_id": booking_id, "outcome": "SUCCESS"},
        headers=headers,
    )
    assert first.status_code == 201
    assert first.json()["booking_status"] == "CONFIRMED"
    assert second.status_code == 409


def test_webhook_is_idempotent(client):
    headers = signup_and_login(client)
    booking_id = create_pending_booking(client, headers)
    body = {"event_id": "evt-100", "booking_id": booking_id, "status": "FAILED"}
    first = client.post("/payments/webhook", json=body)
    second = client.post("/payments/webhook", json=body)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["booking_status"] == "FAILED"