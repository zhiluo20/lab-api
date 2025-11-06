"""Smoke tests for HTML routes."""

from __future__ import annotations

from flask.testing import FlaskClient


def _login(client: FlaskClient) -> dict:
    res = client.post("/auth/login", json={"username": "admin", "password": "password"})
    assert res.status_code == 200
    return res.get_json()


def test_login_page_get_and_post(client, admin_user):
    response = client.get("/web/login")
    assert response.status_code == 200

    res = client.post(
        "/web/login",
        data={"username": "admin", "password": "password"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "access_token" in res.get_data(as_text=True)


def test_docs_list_and_edit_html(client, admin_user, sample_doc):
    tokens = _login(client)
    token = tokens["access_token"]

    list_res = client.get(f"/web/list?token={token}")
    assert list_res.status_code == 200
    assert sample_doc.name in list_res.get_data(as_text=True)

    edit_res = client.get(f"/web/edit/{sample_doc.id}?token={token}")
    assert edit_res.status_code == 200
    page = edit_res.get_data(as_text=True)
    assert sample_doc.name in page
    assert "config" in page
