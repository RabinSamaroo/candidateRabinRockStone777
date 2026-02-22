import pytest
from fastapi.testclient import TestClient
from src.api import app
import os

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_event_log():
    path = os.path.join(os.path.dirname(__file__), '..', 'events.jsonl')
    path = os.path.abspath(path)
    if os.path.exists(path):
        os.remove(path)

# reservation can only exist for an existing compartment
def test_reservation_only_for_existing_compartment():
    event = {
        "event_id": "rule-1",
        "occurred_at": "2026-02-21T10:00:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "nonexistent", "reservation_id": "r1"}
    }
    r = client.post("/events", json=event)
    assert r.status_code == 202  # API always returns 202/200, but projection will not create reservation
    r2 = client.get("/reservations/r1")
    assert r2.status_code == 404

# compartment can have at most one active reservation
def test_one_active_reservation_per_compartment():
    # Register compartment
    client.post("/events", json={
        "event_id": "rule-2a",
        "occurred_at": "2026-02-21T10:01:00Z",
        "locker_id": "rule-locker",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "c1"}
    })
    # First reservation
    client.post("/events", json={
        "event_id": "rule-2b",
        "occurred_at": "2026-02-21T10:02:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "c1", "reservation_id": "r2"}
    })
    # Second reservation (should not overwrite)
    client.post("/events", json={
        "event_id": "rule-2c",
        "occurred_at": "2026-02-21T10:03:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "c1", "reservation_id": "r3"}
    })
    r = client.get("/reservations/r3")
    assert r.status_code == 404

# parcel deposit only valid after reservation creation and before pickup/expiration
def test_deposit_only_after_reservation():
    # Register compartment and reservation
    client.post("/events", json={
        "event_id": "rule-3a",
        "occurred_at": "2026-02-21T10:04:00Z",
        "locker_id": "rule-locker",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "c2"}
    })
    client.post("/events", json={
        "event_id": "rule-3b",
        "occurred_at": "2026-02-21T10:05:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "c2", "reservation_id": "r4"}
    })
    # Deposit before reservation (invalid)
    client.post("/events", json={
        "event_id": "rule-3c",
        "occurred_at": "2026-02-21T10:06:00Z",
        "locker_id": "rule-locker",
        "type": "ParcelDeposited",
        "payload": {"reservation_id": "r5"}
    })
    r = client.get("/reservations/r5")
    assert r.status_code == 404
    # Deposit after reservation (valid)
    client.post("/events", json={
        "event_id": "rule-3d",
        "occurred_at": "2026-02-21T10:07:00Z",
        "locker_id": "rule-locker",
        "type": "ParcelDeposited",
        "payload": {"reservation_id": "r4"}
    })
    r2 = client.get("/reservations/r4")
    assert r2.status_code == 200
    assert r2.json()["status"] == "DEPOSITED"

# Parcel pickup only valid after deposit
def test_pickup_only_after_deposit():
    # Register compartment and reservation
    client.post("/events", json={
        "event_id": "rule-4a",
        "occurred_at": "2026-02-21T10:08:00Z",
        "locker_id": "rule-locker",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "c3"}
    })
    client.post("/events", json={
        "event_id": "rule-4b",
        "occurred_at": "2026-02-21T10:09:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "c3", "reservation_id": "r6"}
    })
    # Pickup before deposit (invalid)
    client.post("/events", json={
        "event_id": "rule-4c",
        "occurred_at": "2026-02-21T10:10:00Z",
        "locker_id": "rule-locker",
        "type": "ParcelPickedUp",
        "payload": {"reservation_id": "r6"}
    })
    r = client.get("/reservations/r6")
    assert r.status_code == 200
    assert r.json()["status"] == "CREATED"
    # Deposit then pickup (valid)
    client.post("/events", json={
        "event_id": "rule-4d",
        "occurred_at": "2026-02-21T10:11:00Z",
        "locker_id": "rule-locker",
        "type": "ParcelDeposited",
        "payload": {"reservation_id": "r6"}
    })
    client.post("/events", json={
        "event_id": "rule-4e",
        "occurred_at": "2026-02-21T10:12:00Z",
        "locker_id": "rule-locker",
        "type": "ParcelPickedUp",
        "payload": {"reservation_id": "r6"}
    })
    r2 = client.get("/reservations/r6")
    assert r2.status_code == 200
    assert r2.json()["status"] == "PICKED_UP"

# Expired reservations cannot be picked up
def test_expired_reservation_cannot_be_picked_up():
    # Register compartment and reservation
    client.post("/events", json={
        "event_id": "rule-5a",
        "occurred_at": "2026-02-21T10:13:00Z",
        "locker_id": "rule-locker",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "c4"}
    })
    client.post("/events", json={
        "event_id": "rule-5b",
        "occurred_at": "2026-02-21T10:14:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "c4", "reservation_id": "r7"}
    })
    client.post("/events", json={
        "event_id": "rule-5c",
        "occurred_at": "2026-02-21T10:15:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationExpired",
        "payload": {"reservation_id": "r7"}
    })
    # Attempt pickup after expiration
    client.post("/events", json={
        "event_id": "rule-5d",
        "occurred_at": "2026-02-21T10:16:00Z",
        "locker_id": "rule-locker",
        "type": "ParcelPickedUp",
        "payload": {"reservation_id": "r7"}
    })
    r = client.get("/reservations/r7")
    assert r.status_code == 200
    assert r.json()["status"] == "EXPIRED"

# Faults affect compartment availability but not parcel state
# Compartments with uncleared faults of severity >= 3 are degraded and cannot accept new reservations

def test_faults_and_degraded_compartment():
    # Register compartment
    client.post("/events", json={
        "event_id": "rule-6a",
        "occurred_at": "2026-02-21T10:17:00Z",
        "locker_id": "rule-locker",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "c5"}
    })
    # FaultReported with severity 3
    client.post("/events", json={
        "event_id": "rule-6b",
        "occurred_at": "2026-02-21T10:18:00Z",
        "locker_id": "rule-locker",
        "type": "FaultReported",
        "payload": {"compartment_id": "c5", "severity": 3}
    })
    # Try to create reservation (should not succeed)
    client.post("/events", json={
        "event_id": "rule-6c",
        "occurred_at": "2026-02-21T10:19:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "c5", "reservation_id": "r8"}
    })
    r = client.get("/reservations/r8")
    assert r.status_code == 404
    # FaultCleared
    client.post("/events", json={
        "event_id": "rule-6d",
        "occurred_at": "2026-02-21T10:20:00Z",
        "locker_id": "rule-locker",
        "type": "FaultCleared",
        "payload": {"compartment_id": "c5", "fault_event_id": "rule-6b"}
    })
    # Now reservation should succeed
    client.post("/events", json={
        "event_id": "rule-6e",
        "occurred_at": "2026-02-21T10:21:00Z",
        "locker_id": "rule-locker",
        "type": "ReservationCreated",
        "payload": {"compartment_id": "c5", "reservation_id": "r9"}
    })
    r2 = client.get("/reservations/r9")
    assert r2.status_code == 200
    assert r2.json()["status"] == "CREATED"
