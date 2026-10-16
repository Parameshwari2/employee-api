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

## Database

Schema is managed with Alembic.

    docker compose exec api alembic upgrade head      # apply
    docker compose exec api alembic downgrade base    # roll back everything
    docker compose exec api alembic revision --autogenerate -m "message"   # new migration

ER diagram: docs/er-diagram.md

### Design decision: one role per employee
Each employee has exactly one role (`employees.role_id`). Payroll needs a single
job title and salary band, and the API contract exposes one `job_title`. A single
foreign key is simpler and faster to query. If we later need multiple roles or
permissions, we can add an `employee_roles` link table without changing existing columns.

### Other decisions
- Soft delete: `is_active = false` instead of deleting rows, so history stays intact.
- Emails are lowercased on save and must be unique.
- Departments/roles cannot be deleted while employees use them (RESTRICT).
- Deleting a manager sets their reports' `manager_id` to NULL.

### Running tests
Tests need PostgreSQL running and a test database:

    docker compose up -d db
    docker compose exec db psql -U postgres -c "CREATE DATABASE employees_test;"
    pytest