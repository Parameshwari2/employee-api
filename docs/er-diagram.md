# ER Diagram

mermaid
erDiagram
    DEPARTMENTS ||--o{ EMPLOYEES : "has"
    ROLES ||--o{ EMPLOYEES : "assigned to"
    EMPLOYEES |o--o{ EMPLOYEES : "manages"

    DEPARTMENTS {
        int id PK
        string name UK
        string description
        bool is_active
        datetime created_at
        datetime updated_at
    }
    ROLES {
        int id PK
        string title UK
        string description
        datetime created_at
        datetime updated_at
    }
    EMPLOYEES {
        int id PK
        string first_name
        string last_name
        string email UK
        date hire_date
        decimal salary
        bool is_active
        int department_id FK
        int role_id FK
        int manager_id FK
        datetime created_at
        datetime updated_at
    }
