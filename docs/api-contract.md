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