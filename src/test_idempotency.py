import pytest
import os
from fastapi.testclient import TestClient
from api import app
from models import Event

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_event_log():
    path = os.path.join(os.path.dirname(__file__), '..', 'events.jsonl')
    path = os.path.abspath(path)
    if os.path.exists(path):
        os.remove(path)


def test_event_idempotency():
    event = {
        "event_id": "idemp-1",
        "occurred_at": "2026-02-21T12:00:00Z",
        "locker_id": "idemp-locker",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "idemp-c1"}
    }
    # First POST should return 202
    r1 = client.post("/events", json=event)
    assert r1.status_code == 202
    # Second POST (same event_id) should return 200 (duplicate)
    r2 = client.post("/events", json=event)
    assert r2.status_code == 200
    assert r2.json().get("detail") == "Duplicate event"
    # State should not change after duplicate
    r3 = client.get("/lockers/idemp-locker")
    assert r3.status_code == 200
    summary = r3.json()
    assert summary["compartments"] == 1
    # Send another event for same compartment
    event2 = {
        "event_id": "idemp-2",
        "occurred_at": "2026-02-21T12:01:00Z",
        "locker_id": "idemp-locker",
        "type": "CompartmentRegistered",
        "payload": {"compartment_id": "idemp-c1"}
    }
    r4 = client.post("/events", json=event2)
    assert r4.status_code == 202 or r4.status_code == 200
    # State should still have only one compartment (no duplicates)
    r5 = client.get("/lockers/idemp-locker")
    assert r5.status_code == 200
    summary2 = r5.json()
    assert summary2["compartments"] == 1
