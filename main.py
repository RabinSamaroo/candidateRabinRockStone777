from models import Event, LockerSummary, CompartmentStatus, ReservationStatus
from event_store import EventStore
from projection import Projection

def test_event_store_and_projection():
    store = EventStore('events.jsonl')
    # Create events
    events = [
        Event(
            event_id="1",
            occurred_at="2026-02-20T12:00:00Z",
            locker_id="locker1",
            type="CompartmentRegistered",
            payload={"compartment_id": "c1"}
        ),
        Event(
            event_id="2",
            occurred_at="2026-02-20T12:01:00Z",
            locker_id="locker1",
            type="ReservationCreated",
            payload={"compartment_id": "c1", "reservation_id": "r1"}
        ),
        Event(
            event_id="3",
            occurred_at="2026-02-20T12:02:00Z",
            locker_id="locker1",
            type="ParcelDeposited",
            payload={"reservation_id": "r1"}
        ),
        Event(
            event_id="4",
            occurred_at="2026-02-20T12:03:00Z",
            locker_id="locker1",
            type="ParcelPickedUp",
            payload={"reservation_id": "r1"}
        ),
    ]
    # Append events
    for e in events:
        store.append(e.model_dump())

    # Load all events
    all_events = store.load_all()
    print("All events:", all_events)

    # Test projection
    proj = Projection()
    proj.rebuild(all_events)

    # Locker summary
    summary = proj.locker_summary("locker1")
    print("Locker summary:", summary)

    # Compartment status
    comp_status = proj.compartment_status("locker1", "c1")
    print("Compartment status:", comp_status)

    # Reservation status
    res_status = proj.reservation_status("r1")
    print("Reservation status:", res_status)

if __name__ == "__main__":
    test_event_store_and_projection()