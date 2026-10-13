# Employee API

FastAPI + PostgreSQL, run with Docker Compose.

## Run
1. `cp .env.example .env` and edit the values (set a real SECRET_KEY).
2. `docker compose up --build`
3. Open http://localhost:8000/docs  (health: /health)

## Test (local)
python -m venv .venv && activate it
pip install -r requirements-dev.txt
pytest

## Structure
app/api (routes) · app/services (logic) · app/models (tables) · app/schemas · app/core (settings)

## Docs for other teams
docs/api-contract.md · data/sample_employees.json