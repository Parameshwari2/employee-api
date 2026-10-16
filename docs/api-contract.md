# Draft API Contract (v0.1, subject to change)

Base URL (local): http://localhost:8000 · Format: JSON · Interactive docs: /docs

| Method | Path                      | Purpose                    | Request body        | Success response          | Status |
|--------|---------------------------|----------------------------|---------------------|---------------------------|--------|
| GET    | /health                   | Liveness check             | none                | {"status": "ok"}          | Live   |
| POST   | /auth/login               | Get access token           | {email, password}   | {access_token, token_type}| Planned|
| GET    | /employees                | List employees (paginated) | query: page, size, department | {items: [Employee], total} | Planned|
| GET    | /employees/{id}           | Get one employee           | none                | Employee                  | Planned|
| POST   | /employees                | Create employee            | EmployeeCreate      | Employee (201)            | Planned|
| PUT    | /employees/{id}           | Update employee            | EmployeeUpdate      | Employee                  | Planned|
| DELETE | /employees/{id}           | Delete employee            | none                | 204 No Content            | Planned|
| GET    | /departments              | List departments           | none                | [Department]              | Planned|

## Employee object
{
  "id": 1, "first_name": "Aarav", "last_name": "Sharma",
  "email": "aarav.sharma@example.com", "department": "Engineering",
  "job_title": "Backend Developer", "salary": 85000,
  "hire_date": "2022-03-14", "is_active": true
}

## Errors
{"detail": "Employee not found"}  (404)  ·  422 for validation errors  ·  401 if not authenticated

## Changes in v0.2 (Task 3)
- Employee updates use **PATCH** (partial), not PUT.
- Employee response now nests `department {id,name,...}` and `role {id,title}`;
  `department_id` / `role_id` / `manager_id` are still included.
- `salary` is returned as a **string** (e.g. "85000.00") to avoid rounding errors with money.
- List endpoints return `{items, total, page, size, pages}`.
- All errors: `{"error": {"code", "message", "details"}}`

| Method | Path | Notes | Success |
|---|---|---|---|
| GET | /employees | ?page=1&size=20&department=HR&q=asha&include_inactive=false | 200 Page |
| POST | /employees | 409 duplicate email, 422 bad input | 201 |
| GET | /employees/{id} | returns inactive employees too | 200 |
| PATCH | /employees/{id} | send only changed fields | 200 |
| DELETE | /employees/{id} | soft delete (is_active=false), idempotent | 204 |
| GET | /employees/{id}/team | active direct reports | 200 list |
| GET | /departments | active departments | 200 list |
| GET | /departments/{id}/employees | paginated | 200 Page |