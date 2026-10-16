from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.models import Department, Employee, Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.hierarchy import get_all_reports

# Load department and role in the same query (avoids one extra query per row)
_EAGER = (joinedload(Employee.department), joinedload(Employee.role))
_ORDER = (Employee.last_name, Employee.first_name, Employee.id)  # id = stable paging


# ---------- helpers ----------

def _escape_like(text: str) -> str:
    """Make % and _ typed by the user match literally."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _apply_filters(stmt, *, department, department_id, q, include_inactive):
    if not include_inactive:
        stmt = stmt.where(Employee.is_active.is_(True))
    if department_id is not None:
        stmt = stmt.where(Employee.department_id == department_id)
    if department:
        stmt = stmt.join(Department, Employee.department_id == Department.id).where(
            func.lower(Department.name) == department.strip().lower()
        )
    if q:
        pattern = f"%{_escape_like(q.strip())}%"
        full_name = Employee.first_name + " " + Employee.last_name
        stmt = stmt.where(full_name.ilike(pattern, escape="\\"))
    return stmt


def _check_references(db: Session, *, department_id=None, role_id=None, manager_id=None):
    checks = (
        (Department, department_id, "department_id"),
        (Role, role_id, "role_id"),
        (Employee, manager_id, "manager_id"),
    )
    for model, pk, field in checks:
        if pk is not None and db.get(model, pk) is None:
            raise BusinessRuleError(f"{field} {pk} does not exist", details={"field": field})


def _check_manager(db: Session, employee_id: int, manager_id: int) -> None:
    if manager_id == employee_id:
        raise BusinessRuleError(
            "An employee cannot be their own manager", details={"field": "manager_id"}
        )
    if manager_id in {e.id for e in get_all_reports(db, employee_id)}:
        raise BusinessRuleError(
            "That manager already reports (directly or indirectly) to this employee",
            details={"field": "manager_id"},
        )


def _ensure_email_free(db: Session, email: str, exclude_id: int | None = None) -> None:
    stmt = select(Employee.id).where(Employee.email == email.lower())
    if exclude_id is not None:
        stmt = stmt.where(Employee.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise ConflictError(
            "An employee with this email already exists", details={"field": "email"}
        )


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:  # safety net, e.g. two requests racing
        db.rollback()
        raise ConflictError("The change violates a database rule") from exc


# ---------- public functions ----------

def get_employee(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id, options=_EAGER)
    if employee is None:
        raise NotFoundError(f"Employee {employee_id} not found")
    return employee


def list_employees(
    db: Session,
    *,
    offset: int,
    limit: int,
    department: str | None = None,
    department_id: int | None = None,
    q: str | None = None,
    include_inactive: bool = False,
) -> tuple[list[Employee], int]:
    filters = dict(
        department=department, department_id=department_id,
        q=q, include_inactive=include_inactive,
    )
    count_stmt = _apply_filters(
        select(func.count(Employee.id)).select_from(Employee), **filters
    )
    total = db.scalar(count_stmt) or 0

    rows_stmt = _apply_filters(select(Employee).options(*_EAGER), **filters)
    rows = db.scalars(rows_stmt.order_by(*_ORDER).offset(offset).limit(limit)).all()
    return list(rows), total


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    values = data.model_dump()
    _check_references(
        db,
        department_id=values["department_id"],
        role_id=values["role_id"],
        manager_id=values["manager_id"],
    )
    _ensure_email_free(db, values["email"])

    employee = Employee(**values)
    db.add(employee)
    _commit(db)
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee_id: int, data: EmployeeUpdate) -> Employee:
    employee = get_employee(db, employee_id)
    changes = data.model_dump(exclude_unset=True)  # only what the client sent

    if "email" in changes:
        _ensure_email_free(db, changes["email"], exclude_id=employee.id)
    _check_references(
        db,
        department_id=changes.get("department_id"),
        role_id=changes.get("role_id"),
        manager_id=changes.get("manager_id"),
    )
    if changes.get("manager_id") is not None:
        _check_manager(db, employee.id, changes["manager_id"])

    for field, value in changes.items():
        setattr(employee, field, value)
    _commit(db)
    db.refresh(employee)
    return employee


def deactivate_employee(db: Session, employee_id: int) -> None:
    """Soft delete: keep the row, mark it inactive. Safe to call twice."""
    employee = get_employee(db, employee_id)
    if employee.is_active:
        employee.is_active = False
        _commit(db)


def get_team(db: Session, employee_id: int) -> list[Employee]:
    """Active direct reports of one manager."""
    get_employee(db, employee_id)  # raises 404 if the manager doesn't exist
    stmt = (
        select(Employee)
        .options(*_EAGER)
        .where(Employee.manager_id == employee_id, Employee.is_active.is_(True))
        .order_by(*_ORDER)
    )
    return list(db.scalars(stmt).all())