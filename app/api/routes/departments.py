from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, PageParams
from app.schemas.common import ErrorResponse, Page, build_page
from app.schemas.department import DepartmentRead
from app.schemas.employee import EmployeeRead
from app.services import department_service

router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: DbSession):
    return department_service.list_departments(db)


@router.get("/{department_id}/employees", response_model=Page[EmployeeRead])
def list_department_employees(
    department_id: int,
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    include_inactive: bool = False,
):
    rows, total = department_service.list_department_employees(
        db,
        department_id,
        offset=params.offset,
        limit=params.size,
        include_inactive=include_inactive,
    )
    return build_page(rows, total, params.page, params.size)