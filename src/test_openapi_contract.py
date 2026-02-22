import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

# 1. Requests violating OpenAPI schema must return 422
@pytest.mark.parametrize("invalid_event", [
    # Missing required field: event_id
    {
        "occurred_at": "2026-02-21T10:00:00Z",
        "locker_id": "lockerA",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "cA1"}
    },
    # Wrong type for event_id
    {
        "event_id": 123,
        "occurred_at": "2026-02-21T10:00:00Z",
        "locker_id": "lockerA",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "cA1"}
    },
    # Missing payload
    {
        "event_id": "bad-1",
        "occurred_at": "2026-02-21T10:00:00Z",
        "locker_id": "lockerA",
        "type": "CompartmentRegistered"
    },
    # Invalid enum value for type
    {
        "event_id": "bad-2",
        "occurred_at": "2026-02-21T10:00:00Z",
        "locker_id": "lockerA",
        "type": "NotAValidType",
        "payload": {"compartment_id": "cA1"}
    }
])
def test_invalid_event_schema_returns_422(invalid_event):
    r = client.post("/events", json=invalid_event)
    assert r.status_code == 422

# 2. Valid requests must conform exactly to the response schemas
# LockerSummary, CompartmentStatus, ReservationStatus

def test_valid_event_and_response_schema():
    # Register compartment
    event = {
        "event_id": "valid-1",
        "occurred_at": "2026-02-21T10:00:00Z",
        "locker_id": "lockerB",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "cB1"}
    }
    r = client.post("/events", json=event)
    assert r.status_code == 202
    # ReservationCreated
    event2 = {
        "event_id": "valid-2",
        "occurred_at": "2026-02-21T10:01:00Z",
        "locker_id": "lockerB",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "cB1", "reservation_id": "rB1"}
    }
    r2 = client.post("/events", json=event2)
    assert r2.status_code == 202
    # LockerSummary
    r3 = client.get("/lockers/lockerB")
    assert r3.status_code == 200
    summary = r3.json()
    assert set(summary.keys()) == {"locker_id", "compartments", "active_reservations", "degraded_compartments", "state_hash"}
    # CompartmentStatus
    r4 = client.get("/lockers/lockerB/compartments/cB1")
    assert r4.status_code == 200
    comp_status = r4.json()
    assert set(comp_status.keys()) == {"compartment_id", "degraded", "active_reservation"}
    # ReservationStatus
    r5 = client.get("/reservations/rB1")
    assert r5.status_code == 200
    res_status = r5.json()
    assert set(res_status.keys()) == {"reservation_id", "status"}
