# LockStream Backend Service

## Overview

LockStream is an event-sourced backend service for smart parcel lockers.
All domain rules, event types, etc are derived from the OpenAPI contract

## Requirements

- Python 3.14
- Dependencies: FastAPI, Pydantic, Uvicorn, Pytest

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/RabinSamaroo/candidateRabinRockStone777
   cd candidateRabinRockStone777
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3.14 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn pydantic pytest
   ```
   Or
   ```bash
   uv pip install -r pyproject.toml
   ```

## Running the API

1. **Start the FastAPI app**

   ```bash
   uvicorn src.api:app --reload
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000).

2. **API contract**
   - The OpenAPI contract is in `src/openapi.yaml`.
   - Endpoints:
     - `POST /events` — Ingest domain events
     - `GET /lockers/{locker_id}` — Locker summary
     - `GET /lockers/{locker_id}/compartments/{compartment_id}` — Compartment status
     - `GET /reservations/{reservation_id}` — Reservation status

## Running Tests

**NOTE:** `httpx` is required for fastapi test client, if you recieve an error message related to this try:

```bash
pip install httpx
```

1. **Clear any previous event log**
   - Tests automatically clear `src/events.jsonl` before each run.

2. **Run all tests**
   ```bash
   pytest src/
   ```
