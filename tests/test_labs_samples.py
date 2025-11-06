"""Tests for dedicated labs and samples APIs."""

from __future__ import annotations

from flask import Response

from tests.test_auth import auth_header


def _login_admin(client) -> str:
    res = client.post("/auth/login", json={"username": "admin", "password": "password"})
    assert res.status_code == 200
    return res.get_json()["access_token"]


def test_labs_route_crud(client, admin_user):
    token = _login_admin(client)

    create = client.post(
        "/api/v1/labs",
        headers=auth_header(token),
        json={"name": "Genomics", "description": "Sequencing", "location": "A1"},
    )
    assert create.status_code == 201
    lab = create.get_json()["data"]

    detail = client.get(f"/api/v1/labs/{lab['id']}", headers=auth_header(token))
    assert detail.status_code == 200
    assert detail.get_json()["data"]["name"] == "Genomics"

    listing = client.get("/api/v1/labs", headers=auth_header(token))
    payload = listing.get_json()
    assert payload["meta"]["total"] >= 1

    update = client.put(
        f"/api/v1/labs/{lab['id']}",
        headers=auth_header(token),
        json={"description": "Updated description"},
    )
    assert update.status_code == 200
    assert update.get_json()["data"]["description"] == "Updated description"

    delete = client.delete(f"/api/v1/labs/{lab['id']}", headers=auth_header(token))
    assert delete.status_code == 204


def test_samples_route_crud(client, admin_user):
    token = _login_admin(client)

    lab_res = client.post(
        "/api/v1/labs",
        headers=auth_header(token),
        json={"name": "Chem", "description": "Chemistry"},
    )
    lab_id = lab_res.get_json()["data"]["id"]

    create = client.post(
        "/api/v1/samples",
        headers=auth_header(token),
        json={"lab_id": lab_id, "code": "CHEM-01", "status": "pending"},
    )
    assert create.status_code == 201
    sample_id = create.get_json()["data"]["id"]

    detail = client.get(f"/api/v1/samples/{sample_id}", headers=auth_header(token))
    assert detail.status_code == 200
    assert detail.get_json()["data"]["code"] == "CHEM-01"

    listing = client.get("/api/v1/samples", headers=auth_header(token))
    assert listing.status_code == 200
    assert listing.get_json()["meta"]["total"] >= 1

    update = client.put(
        f"/api/v1/samples/{sample_id}",
        headers=auth_header(token),
        json={"status": "archived", "description": "done"},
    )
    assert update.status_code == 200
    assert update.get_json()["data"]["status"] == "archived"

    delete = client.delete(f"/api/v1/samples/{sample_id}", headers=auth_header(token))
    assert delete.status_code == 204


def test_sample_creation_without_lab_is_rejected(client, admin_user):
    token = _login_admin(client)
    resp: Response = client.post(
        "/api/v1/samples",
        headers=auth_header(token),
        json={"lab_id": 999, "code": "CHEM-UNKNOWN"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"]["code"] == "lab_not_found"
