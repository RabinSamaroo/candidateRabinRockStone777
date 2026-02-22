
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from models import LockerSummary, CompartmentStatus, ReservationStatus, ReservationStatusEnum, EventType
import hashlib

@dataclass
class Locker:
    locker_id: str
    compartments: Set[str] = field(default_factory=set)
    active_reservations: Set[str] = field(default_factory=set)
    degraded_compartments: Set[str] = field(default_factory=set)

@dataclass
class Compartment:
    compartment_id: str
    locker_id: str
    degraded: bool = False
    active_reservation: Optional[str] = None
    faults: Set[str] = field(default_factory=set)

@dataclass
class Reservation:
    reservation_id: str
    compartment_id: str
    locker_id: str
    status: ReservationStatusEnum = ReservationStatusEnum.CREATED

@dataclass
class Fault:
    fault_id: str
    compartment_id: str
    severity: int = 1
    cleared: bool = False

class Projection:
    def __init__(self):
        self.lockers: Dict[str, Locker] = {}
        self.compartments: Dict[str, Compartment] = {}
        self.reservations: Dict[str, Reservation] = {}
        self.faults: Dict[str, Fault] = {}
        self.applied_event_ids = set()

    def rebuild(self, events):
        self.lockers.clear()
        self.compartments.clear()
        self.reservations.clear()
        self.faults.clear()
        self.applied_event_ids.clear()
        for event in events:
            self.apply(event)

    def apply(self, event):
        eid = event['event_id']
        if eid in self.applied_event_ids:
            return
        self.applied_event_ids.add(eid)
        locker_id = event['locker_id']
        etype = event['type']
        payload = event['payload']

        if locker_id not in self.lockers:
            self.lockers[locker_id] = Locker(locker_id=locker_id)

        if etype == EventType.COMPARTMENT_REGISTERED:
            cid = payload['compartment_id']
            self.lockers[locker_id].compartments.add(cid)
            self.compartments[cid] = Compartment(compartment_id=cid, locker_id=locker_id)

        elif etype == EventType.RESERVATION_CREATED:
            cid = payload['compartment_id']
            rid = payload['reservation_id']
            if cid not in self.compartments:
                return  # Compartment must exist
            comp = self.compartments[cid]
            if comp.active_reservation is not None:
                return  # Only one active reservation
            if comp.degraded:
                return  # Cannot reserve degraded compartment
            comp.active_reservation = rid
            self.lockers[locker_id].active_reservations.add(rid)
            self.reservations[rid] = Reservation(
                reservation_id=rid,
                compartment_id=cid,
                locker_id=locker_id,
                status=ReservationStatusEnum.CREATED
            )

        elif etype == EventType.PARCEL_DEPOSITED:
            rid = payload['reservation_id']
            if rid not in self.reservations:
                return
            res = self.reservations[rid]
            if res.status != ReservationStatusEnum.CREATED:
                return
            res.status = ReservationStatusEnum.DEPOSITED

        elif etype == EventType.PARCEL_PICKED_UP:
            rid = payload['reservation_id']
            if rid not in self.reservations:
                return
            res = self.reservations[rid]
            if res.status != ReservationStatusEnum.DEPOSITED:
                return
            res.status = ReservationStatusEnum.PICKED_UP
            cid = res.compartment_id
            self.compartments[cid].active_reservation = None
            locker_id = res.locker_id
            self.lockers[locker_id].active_reservations.discard(rid)

        elif etype == EventType.RESERVATION_EXPIRED:
            rid = payload['reservation_id']
            if rid not in self.reservations:
                return
            res = self.reservations[rid]
            res.status = ReservationStatusEnum.EXPIRED
            cid = res.compartment_id
            self.compartments[cid].active_reservation = None
            locker_id = res.locker_id
            self.lockers[locker_id].active_reservations.discard(rid)

        elif etype == EventType.FAULT_REPORTED:
            cid = payload['compartment_id']
            fid = event['event_id']
            severity = payload.get('severity', 1)
            self.faults[fid] = Fault(
                fault_id=fid,
                compartment_id=cid,
                severity=severity,
                cleared=False
            )
            if cid in self.compartments:
                self.compartments[cid].faults.add(fid)
                if severity >= 3:
                    self.compartments[cid].degraded = True
                    self.lockers[locker_id].degraded_compartments.add(cid)

        elif etype == EventType.FAULT_CLEARED:
            ref_fault_id = payload['fault_event_id']
            cid = payload['compartment_id']
            if ref_fault_id not in self.faults:
                return
            fault = self.faults[ref_fault_id]
            if fault.compartment_id != cid:
                return
            if fault.cleared:
                return
            fault.cleared = True
            if cid in self.compartments:
                self.compartments[cid].faults.discard(ref_fault_id)
                # If no uncleared faults with severity >= 3, clear degraded
                uncleared = [self.faults[fid] for fid in self.compartments[cid].faults if not self.faults[fid].cleared and self.faults[fid].severity >= 3]
                if not uncleared:
                    self.compartments[cid].degraded = False
                    self.lockers[locker_id].degraded_compartments.discard(cid)

    def locker_summary(self, locker_id: str) -> Optional[LockerSummary]:
        if locker_id not in self.lockers:
            return None
        locker = self.lockers[locker_id]
        state_hash = self._compute_state_hash(locker_id)
        return LockerSummary(
            locker_id=locker_id,
            compartments=len(locker.compartments),
            active_reservations=len(locker.active_reservations),
            degraded_compartments=len(locker.degraded_compartments),
            state_hash=state_hash
        )

    def compartment_status(self, locker_id: str, compartment_id: str) -> Optional[CompartmentStatus]:
        if compartment_id not in self.compartments:
            return None
        comp = self.compartments[compartment_id]
        return CompartmentStatus(
            compartment_id=compartment_id,
            degraded=comp.degraded,
            active_reservation=comp.active_reservation
        )

    def reservation_status(self, reservation_id: str) -> Optional[ReservationStatus]:
        if reservation_id not in self.reservations:
            return None
        res = self.reservations[reservation_id]
        return ReservationStatus(
            reservation_id=reservation_id,
            status=res.status
        )

    def _compute_state_hash(self, locker_id: str) -> str:
        # Deterministic hash of locker state
        locker = self.lockers[locker_id]
        summary = {
            'compartments': sorted(list(locker.compartments)),
            'active_reservations': sorted(list(locker.active_reservations)),
            'degraded_compartments': sorted(list(locker.degraded_compartments)),
        }
        return hashlib.sha256(str(summary).encode()).hexdigest()
