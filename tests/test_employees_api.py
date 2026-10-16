from datetime import date, timedelta

import pytest

from app.models import Department, Employee


@pytest.fixture
def payload(dept, role):
    return {
        "first_name": "Asha",
        "last_name": "Verma",
        "email": "asha.verma@example.com",
        "hire_date": "2024-02-01",
        "salary": "85000.00",
        "department_id": dept.id,
        "role_id": role.id,
    }


@pytest.fixture
def hr_dept(db):
    d = Department(name="HR")
    db.add(d)
    db.flush()
    return d


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert "message" in body["error"]
    return body["error"]


# ---------- POST /employees ----------

def test_create_employee(client, payload, dept):
    r = client.post("/employees", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["id"] > 0
    assert data["first_name"] == "Asha"
    assert data["is_active"] is True
    assert data["department"]["name"] == dept.name
    assert data["role"]["title"] == "Developer"


def test_create_lowercases_email(client, payload):
    payload["email"] = "Asha.Verma@Example.COM"
    r = client.post("/employees", json=payload)
    assert r.status_code == 201
    assert r.json()["email"] == "asha.verma@example.com"


def test_create_duplicate_email_returns_409(client, payload):
    assert client.post("/employees", json=payload).status_code == 201
    error = assert_error(client.post("/employees", json=payload), 409, "conflict")
    assert error["details"]["field"] == "email"


@pytest.mark.parametrize(
    "field, value",
    [
        ("email", "not-an-email"),
        ("first_name", "   "),
        ("last_name", ""),
        ("hire_date", (date.today() + timedelta(days=1)).isoformat()),
        ("hire_date", "not-a-date"),
        ("salary", "-5"),
    ],
)
def test_create_with_bad_input_returns_422(client, payload, field, value):
    payload[field] = value
    error = assert_error(client.post("/employees", json=payload), 422, "validation_error")
    assert any(field in item["field"] for item in error["details"])


def test_create_missing_field_returns_422(client, payload):
    del payload["email"]
    assert_error(client.post("/employees", json=payload), 422, "validation_error")


def test_create_unknown_department_returns_422(client, payload):
    payload["department_id"] = 999999
    assert_error(client.post("/employees", json=payload), 422, "business_rule_violation")


def test_create_unknown_manager_returns_422(client, payload):
    payload["manager_id"] = 999999
    assert_error(client.post("/employees", json=payload), 422, "business_rule_violation")


# ---------- GET /employees (list) ----------

def test_list_has_pagination_envelope(client, make_employee):
    for _ in range(3):
        make_employee()
    r = client.get("/employees", params={"page": 1, "size": 2})
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    assert (body["total"], body["page"], body["size"], body["pages"]) == (3, 1, 2, 2)


def test_list_second_page(client, make_employee):
    for _ in range(3):
        make_employee()
    body = client.get("/employees", params={"page": 2, "size": 2}).json()
    assert len(body["items"]) == 1
    assert body["total"] == 3


def test_list_empty(client):
    body = client.get("/employees").json()
    assert body == {"items": [], "total": 0, "page": 1, "size": 20, "pages": 0}


def test_list_filter_by_department(client, make_employee, hr_dept):
    make_employee()
    make_employee(department_id=hr_dept.id)
    body = client.get("/employees", params={"department": "hr"}).json()  # case-insensitive
    assert body["total"] == 1
    assert body["items"][0]["department"]["name"] == "HR"


def test_list_search_by_name(client, make_employee):
    make_employee(first_name="Asha", last_name="Verma")
    make_employee(first_name="Ravi", last_name="Kumar")
    assert client.get("/employees", params={"q": "ASH"}).json()["total"] == 1
    assert client.get("/employees", params={"q": "kumar"}).json()["total"] == 1
    assert client.get("/employees", params={"q": "asha v"}).json()["total"] == 1
    assert client.get("/employees", params={"q": "zzz"}).json()["total"] == 0


def test_list_search_treats_percent_literally(client, make_employee):
    make_employee(first_name="Asha")
    assert client.get("/employees", params={"q": "%"}).json()["total"] == 0


def test_list_filter_search_and_paging_together(client, make_employee, hr_dept):
    for n in range(3):
        make_employee(first_name=f"Asha{n}")                          # Engineering
    make_employee(first_name="Asha9", department_id=hr_dept.id)       # HR
    make_employee(first_name="Ravi")                                  # Engineering
    body = client.get(
        "/employees",
        params={"department": "Engineering", "q": "asha", "page": 1, "size": 2},
    ).json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["pages"] == 2


def test_list_hides_inactive_by_default(client, make_employee):
    make_employee()
    gone = make_employee(is_active=False)
    assert client.get("/employees").json()["total"] == 1
    body = client.get("/employees", params={"include_inactive": True}).json()
    assert body["total"] == 2
    assert gone.id in [e["id"] for e in body["items"]]


@pytest.mark.parametrize("params", [{"page": 0}, {"size": 0}, {"size": 101}, {"page": "x"}])
def test_list_bad_paging_returns_422(client, params):
    assert_error(client.get("/employees", params=params), 422, "validation_error")


# ---------- GET /employees/{id} ----------

def test_get_employee(client, make_employee):
    emp = make_employee(first_name="Asha")
    r = client.get(f"/employees/{emp.id}")
    assert r.status_code == 200
    assert r.json()["first_name"] == "Asha"


def test_get_unknown_employee_returns_404(client):
    assert_error(client.get("/employees/999999"), 404, "not_found")


def test_get_employee_with_text_id_returns_422(client):
    assert_error(client.get("/employees/abc"), 422, "validation_error")


# ---------- PATCH /employees/{id} ----------

def test_patch_changes_only_sent_fields(client, make_employee):
    emp = make_employee(first_name="Asha", last_name="Verma")
    r = client.patch(f"/employees/{emp.id}", json={"last_name": "Nair"})
    assert r.status_code == 200
    assert r.json()["last_name"] == "Nair"
    assert r.json()["first_name"] == "Asha"


def test_patch_duplicate_email_returns_409(client, make_employee):
    make_employee(email="a@example.com")
    other = make_employee(email="b@example.com")
    assert_error(
        client.patch(f"/employees/{other.id}", json={"email": "a@example.com"}), 409, "conflict"
    )


def test_patch_keeping_own_email_is_fine(client, make_employee):
    emp = make_employee(email="a@example.com")
    r = client.patch(f"/employees/{emp.id}", json={"email": "A@example.com"})
    assert r.status_code == 200


@pytest.mark.parametrize(
    "body",
    [
        {"first_name": None},
        {"first_name": " "},
        {"email": "nope"},
        {"hire_date": (date.today() + timedelta(days=5)).isoformat()},
    ],
)
def test_patch_bad_input_returns_422(client, make_employee, body):
    emp = make_employee()
    assert_error(client.patch(f"/employees/{emp.id}", json=body), 422, "validation_error")


def test_patch_unknown_employee_returns_404(client):
    assert_error(client.patch("/employees/999999", json={"last_name": "X"}), 404, "not_found")


def test_patch_cannot_make_self_manager(client, make_employee):
    emp = make_employee()
    r = client.patch(f"/employees/{emp.id}", json={"manager_id": emp.id})
    assert_error(r, 422, "business_rule_violation")


def test_patch_cannot_create_management_loop(client, make_employee):
    boss = make_employee()
    worker = make_employee(manager_id=boss.id)
    r = client.patch(f"/employees/{boss.id}", json={"manager_id": worker.id})
    assert_error(r, 422, "business_rule_violation")


def test_patch_can_remove_manager_with_null(client, make_employee):
    boss = make_employee()
    worker = make_employee(manager_id=boss.id)
    r = client.patch(f"/employees/{worker.id}", json={"manager_id": None})
    assert r.status_code == 200
    assert r.json()["manager_id"] is None


def test_patch_can_reactivate(client, make_employee):
    emp = make_employee(is_active=False)
    r = client.patch(f"/employees/{emp.id}", json={"is_active": True})
    assert r.json()["is_active"] is True


# ---------- DELETE /employees/{id} (soft) ----------

def test_delete_is_soft(client, db, make_employee):
    emp = make_employee()
    assert client.delete(f"/employees/{emp.id}").status_code == 204

    assert client.get("/employees").json()["total"] == 0          # hidden from the list
    assert client.get(f"/employees/{emp.id}").json()["is_active"] is False
    assert db.get(Employee, emp.id) is not None                   # row still exists


def test_delete_twice_is_ok(client, make_employee):
    emp = make_employee()
    assert client.delete(f"/employees/{emp.id}").status_code == 204
    assert client.delete(f"/employees/{emp.id}").status_code == 204


def test_delete_unknown_returns_404(client):
    assert_error(client.delete("/employees/999999"), 404, "not_found")


# ---------- GET /employees/{id}/team ----------

def test_team_returns_only_active_direct_reports(client, make_employee):
    boss = make_employee()
    a = make_employee(manager_id=boss.id)
    make_employee(manager_id=boss.id, is_active=False)
    make_employee(manager_id=a.id)                       # grandchild: not included
    r = client.get(f"/employees/{boss.id}/team")
    assert r.status_code == 200
    assert [e["id"] for e in r.json()] == [a.id]


def test_team_of_unknown_employee_returns_404(client):
    assert_error(client.get("/employees/999999/team"), 404, "not_found")


# ---------- departments ----------

def test_list_departments(client, dept, hr_dept):
    r = client.get("/departments")
    assert r.status_code == 200
    assert {"Engineering", "HR"} <= {d["name"] for d in r.json()}


def test_department_employees_are_paginated(client, dept, make_employee, hr_dept):
    for _ in range(3):
        make_employee()
    make_employee(department_id=hr_dept.id)
    r = client.get(f"/departments/{dept.id}/employees", params={"size": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_department_employees_unknown_department_returns_404(client):
    assert_error(client.get("/departments/999999/employees"), 404, "not_found")


# ---------- error format ----------

def test_unknown_route_uses_same_error_format(client):
    assert_error(client.get("/does-not-exist"), 404, "not_found")