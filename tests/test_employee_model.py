from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Department, Employee
from app.services.hierarchy import get_all_reports


def test_duplicate_email_fails(make_employee):
    make_employee(email="same@example.com")
    with pytest.raises(IntegrityError):
        make_employee(email="same@example.com")


def test_duplicate_email_different_case_fails(make_employee):
    make_employee(email="Same@Example.com")
    with pytest.raises(IntegrityError):
        make_employee(email="same@example.com")


def test_email_is_required(db, dept, role):
    db.add(Employee(first_name="A", last_name="B", hire_date=date(2024, 1, 1),
                    department_id=dept.id, role_id=role.id))
    with pytest.raises(IntegrityError):
        db.flush()


def test_department_name_must_be_unique(db, dept):
    db.add(Department(name=dept.name))
    with pytest.raises(IntegrityError):
        db.flush()


def test_employee_needs_a_real_department(make_employee):
    with pytest.raises(IntegrityError):
        make_employee(department_id=999999)


def test_cannot_delete_department_with_employees(db, dept, make_employee):
    make_employee()
    db.delete(dept)
    with pytest.raises(IntegrityError):
        db.flush()


def test_cannot_be_own_manager(db, make_employee):
    emp = make_employee()
    emp.manager_id = emp.id
    with pytest.raises(IntegrityError):
        db.flush()


def test_new_employee_is_active_and_timestamped(db, make_employee):
    emp = make_employee()
    db.refresh(emp)
    assert emp.is_active is True
    assert emp.created_at is not None
    assert emp.updated_at is not None


def test_manager_and_direct_reports(db, make_employee):
    boss = make_employee()
    worker = make_employee(manager_id=boss.id)
    db.refresh(boss)
    assert worker.manager.id == boss.id
    assert [e.id for e in boss.direct_reports] == [worker.id]


def test_all_reports_at_any_depth(db, make_employee):
    ceo = make_employee()
    vp = make_employee(manager_id=ceo.id)
    dev = make_employee(manager_id=vp.id)
    ids = {e.id for e in get_all_reports(db, ceo.id)}
    assert ids == {vp.id, dev.id}