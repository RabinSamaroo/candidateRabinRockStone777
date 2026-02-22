# DECISIONS.MD

- Architectural Patterns
  1. Repository Pattern
  - `EventStore` abstracts event persistence and retrieval acting as a repo for domain events
  - Seperates storage concerns from business logic
  2. Command Pattern
  - Each event is a command and applied to the Projection, which updates state according to domain rules.

- Code Organization
  - Code is seperated out into clear modules:
  - `api.py` – HTTP API and request/response validation
  - `models.py` – Pydantic models and enums
  - `event_store.py` – Event log persistence and idempotency
  - `projection.py` – In-memory state projection and domain rule enforcement
  - `test_*.py` – Automated tests for contract, rules, and projection

- Single Source of Truth
  - All state is projected through the append only event log in the `events.jsonl` file
  - This gives auditability and deterministic state, and reconstruction as required

- All request and response models are generated from the openapi contract

- The projection class maintains all current state in memory and can be rebuilt from the event log.
  - This operation is `O(n), n = num of events` since rebuilding the projection is one pass over the event list

- State hashing
  - The projection exposes a `state_hash` for equivalence testing between incremental and full rebuilds
  - Used a hash of **sorted** events to ensure determisim

- No global state (prevents side effects)
