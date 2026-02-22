from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class EventType(str, Enum):
    COMPARTMENT_REGISTERED = "CompartmentRegistered"
    RESERVATION_CREATED = "ReservationCreated"
    PARCEL_DEPOSITED = "ParcelDeposited"
    PARCEL_PICKED_UP = "ParcelPickedUp"
    RESERVATION_EXPIRED = "ReservationExpired"
    FAULT_REPORTED = "FaultReported"
    FAULT_CLEARED = "FaultCleared"

class Event(BaseModel):
    event_id: str = Field(..., description="UUID")
    occurred_at: datetime
    locker_id: str
    type: EventType
    payload: Dict[str, Any]

class LockerSummary(BaseModel):
    locker_id: str
    compartments: int
    active_reservations: int
    degraded_compartments: int
    state_hash: str

class CompartmentStatus(BaseModel):
    compartment_id: str
    degraded: bool
    active_reservation: Optional[str]

class ReservationStatusEnum(str, Enum):
    CREATED = "CREATED"
    DEPOSITED = "DEPOSITED"
    PICKED_UP = "PICKED_UP"
    EXPIRED = "EXPIRED"

class ReservationStatus(BaseModel):
    reservation_id: str
    status: ReservationStatusEnum
