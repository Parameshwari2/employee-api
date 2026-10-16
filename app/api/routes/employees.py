from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, PageParams
from app.schemas.common import ErrorResponse, Page, build_page
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services import employee_service

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)


@router.get("", response_model=Page[EmployeeRead])
def list_employees(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    department: Annotated[str | None, Query(description="Department name (case-insensitive)")] = None,
    q: Annotated[str | None, Query(max_length=100, description="Search in employee name")] = None,
    include_inactive: bool = False,
):
    rows, total = employee_service.list_employees(
        db,
        offset=params.offset,
        limit=params.size,
        department=department,
        q=q,
        include_inactive=include_inactive,
    )
    return build_page(rows, total, params.page, params.size)


@router.post("", response_model=EmployeeRead, status_code=201,
             responses={409: {"model": ErrorResponse}})
def create_employee(data: EmployeeCreate, db: DbSession):
    return employee_service.create_employee(db, data)


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(employee_id: int, db: DbSession):
    return employee_service.get_employee(db, employee_id)


@router.patch("/{employee_id}", response_model=EmployeeRead,
              responses={409: {"model": ErrorResponse}})
def update_employee(employee_id: int, data: EmployeeUpdate, db: DbSession):
    return employee_service.update_employee(db, employee_id, data)


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: DbSession):
    employee_service.deactivate_employee(db, employee_id)


@router.get("/{employee_id}/team", response_model=list[EmployeeRead])
def get_team(employee_id: int, db: DbSession):
    return employee_service.get_team(db, employee_id)