from fastapi import FastAPI, HTTPException, status
from models import Event, LockerSummary, CompartmentStatus, ReservationStatus
from event_store import EventStore
from projection import Projection

app = FastAPI()
event_store = EventStore('events.jsonl')
projection = Projection()

# On startup, rebuild projection from event log
@app.on_event("startup")
def startup_event():
    events = event_store.load_all()
    projection.rebuild(events)

@app.post("/events", status_code=status.HTTP_202_ACCEPTED)
def ingest_event(event: Event):
    event_dict = event.model_dump()
    # Idempotency check
    appended = event_store.append(event_dict)
    if not appended:
        return {"detail": "Duplicate event"}
    # Apply event to projection
    projection.apply(event_dict)
    return {"detail": "Event accepted"}

@app.get("/lockers/{locker_id}", response_model=LockerSummary)
def get_locker_summary(locker_id: str):
    summary = projection.locker_summary(locker_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Locker not found")
    return summary

@app.get("/lockers/{locker_id}/compartments/{compartment_id}", response_model=CompartmentStatus)
def get_compartment_status(locker_id: str, compartment_id: str):
    status_obj = projection.compartment_status(locker_id, compartment_id)
    if status_obj is None:
        raise HTTPException(status_code=404, detail="Compartment not found")
    return status_obj

@app.get("/reservations/{reservation_id}", response_model=ReservationStatus)
def get_reservation_status(reservation_id: str):
    res_status = projection.reservation_status(reservation_id)
    if res_status is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return res_status
