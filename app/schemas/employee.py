from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

from app.schemas.department import DepartmentRead
from app.schemas.role import RoleRead

# Reusable "building block" types
NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Salary = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


def _not_in_future(value: date) -> date:
    if value > date.today():
        raise ValueError("hire_date cannot be in the future")
    return value


HireDate = Annotated[date, AfterValidator(_not_in_future)]


class EmployeeCreate(BaseModel):
    first_name: NameStr
    last_name: NameStr
    email: EmailStr
    hire_date: HireDate
    salary: Salary | None = None
    department_id: int
    role_id: int
    manager_id: int | None = None


class EmployeeUpdate(BaseModel):
    """PATCH body: send only the fields you want to change."""

    first_name: NameStr | None = None
    last_name: NameStr | None = None
    email: EmailStr | None = None
    hire_date: HireDate | None = None
    salary: Salary | None = None
    department_id: int | None = None
    role_id: int | None = None
    manager_id: int | None = None
    is_active: bool | None = None

    @field_validator(
        "first_name", "last_name", "email", "hire_date","department_id", "role_id", "is_active",
    )
    @classmethod
    def _cannot_be_null(cls, value):
        # salary and manager_id may be set to null; these fields may not
        if value is None:
            raise ValueError("cannot be null")
        return value


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str
    hire_date: date
    salary: Decimal | None
    is_active: bool
    department_id: int
    role_id: int
    manager_id: int | None
    department: DepartmentRead
    role: RoleRead
    created_at: datetime
    updated_at: datetime