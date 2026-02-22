import pytest
from fastapi.testclient import TestClient
from api import app
from event_store import EventStore
from projection import Projection

client = TestClient(app)

def test_projection_equivalence_state_hash():
    # Setup: clear event log and add events
    store = EventStore('events.jsonl')
    store.path.unlink(missing_ok=True)  # Remove file if exists
    events = [
        {
            "event_id": "eq-1",
            "occurred_at": "2026-02-21T10:00:00Z",
            "locker_id": "lockerE",
            "type": "CompartmentRegistered",
            "payload": {"compartment_id": "cE1"}
        },
        {
            "event_id": "eq-2",
            "occurred_at": "2026-02-21T10:01:00Z",
            "locker_id": "lockerE",
            "type": "ReservationCreated",
            "payload": {"compartment_id": "cE1", "reservation_id": "rE1"}
        },
        {
            "event_id": "eq-3",
            "occurred_at": "2026-02-21T10:02:00Z",
            "locker_id": "lockerE",
            "type": "ParcelDeposited",
            "payload": {"reservation_id": "rE1"}
        }
    ]
    for e in events:
        store.append(e)

    # Full rebuild
    proj_full = Projection()
    proj_full.rebuild(store.load_all())
    hash_full = proj_full.locker_summary("lockerE").state_hash

    # Incremental application
    proj_inc = Projection()
    for e in store.load_all():
        proj_inc.apply(e)
    hash_inc = proj_inc.locker_summary("lockerE").state_hash

    assert hash_full == hash_inc, f"State hash mismatch: {hash_full} != {hash_inc}"
