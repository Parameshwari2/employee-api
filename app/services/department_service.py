from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import Department, Employee
from app.services import employee_service


def list_departments(db: Session) -> list[Department]:
    return list(
        db.scalars(
            select(Department).where(Department.is_active.is_(True)).order_by(Department.name)
        ).all()
    )


def get_department(db: Session, department_id: int) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise NotFoundError(f"Department {department_id} not found")
    return department


def list_department_employees(
    db: Session, department_id: int, *, offset: int, limit: int, include_inactive: bool = False
) -> tuple[list[Employee], int]:
    get_department(db, department_id)  # 404 if missing
    return employee_service.list_employees(
        db,
        department_id=department_id, offset=offset, limit=limit, include_inactive=include_inactive,
    )