from models import Event, LockerSummary, CompartmentStatus, ReservationStatus
from event_store import EventStore

def test_event_store():
    store = EventStore('events.jsonl')
    # Create event 
    event = Event(
        event_id="123e4567-e89b-12d3-a456-426614174000",
        occurred_at="2026-02-20T12:00:00Z",
        locker_id="locker1",
        type="ReservationCreated",
        payload={"compartment_id": "c1", "reservation_id": "r1"}
    )
    event_dict = event.model_dump()

    # Append event
    result = store.append(event_dict)
    print("Append result:", result)  # True if new, False if duplicate

    # Try appending again 
    result2 = store.append(event_dict)
    print("Append result (duplicate):", result2)  

    # Load all events
    all_events = store.load_all()
    print("All events:", all_events)

    # Load by locker
    locker_events = store.load_by_locker("locker1")
    print("Locker events:", locker_events)

if __name__ == "__main__":
    test_event_store()