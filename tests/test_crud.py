"""Generic CRUD API tests."""

from __future__ import annotations

from app.extensions import db
from app.models.labs import Lab

from tests.test_auth import auth_header


def setup_token(client):
    login_res = client.post(
        "/auth/login", json={"username": "admin", "password": "password"}
    )
    assert login_res.status_code == 200
    return login_res.get_json()["access_token"]


def test_metadata_endpoint(client, admin_user):
    token = setup_token(client)
    res = client.get("/api/v1/meta", headers=auth_header(token))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "labs" in data

    detail = client.get("/api/v1/meta/labs", headers=auth_header(token))
    assert detail.status_code == 200
    assert any(col["name"] == "name" for col in detail.get_json()["data"]["columns"])


def test_crud_cycle_for_labs(client, admin_user):
    token = setup_token(client)
    create = client.post(
        "/api/v1/table/labs",
        headers=auth_header(token),
        json={"name": "Bio Lab", "description": "Biology", "location": "Building 1"},
    )
    assert create.status_code == 201
    lab_id = create.get_json()["data"]["id"]

    list_res = client.get("/api/v1/table/labs", headers=auth_header(token))
    assert list_res.status_code == 200
    assert list_res.get_json()["meta"]["total"] == 1

    update = client.put(
        f"/api/v1/table/labs/{lab_id}",
        headers=auth_header(token),
        json={"description": "Updated"},
    )
    assert update.status_code == 200
    assert update.get_json()["data"]["description"] == "Updated"

    delete = client.delete(f"/api/v1/table/labs/{lab_id}", headers=auth_header(token))
    assert delete.status_code == 204
    assert db.session.query(Lab).count() == 0


def test_crud_for_samples(client, admin_user):
    token = setup_token(client)
    lab_res = client.post(
        "/api/v1/table/labs",
        headers=auth_header(token),
        json={"name": "Physics Lab", "description": "Physics"},
    )
    lab_id = lab_res.get_json()["data"]["id"]

    create_sample = client.post(
        "/api/v1/table/samples",
        headers=auth_header(token),
        json={"lab_id": lab_id, "code": "SAMPLE-42", "status": "ready"},
    )
    assert create_sample.status_code == 201
    sample_id = create_sample.get_json()["data"]["id"]

    update_sample = client.put(
        f"/api/v1/table/samples/{sample_id}",
        headers=auth_header(token),
        json={"status": "archived"},
    )
    assert update_sample.status_code == 200
    assert update_sample.get_json()["data"]["status"] == "archived"

    delete_sample = client.delete(
        f"/api/v1/table/samples/{sample_id}", headers=auth_header(token)
    )
    assert delete_sample.status_code == 204
