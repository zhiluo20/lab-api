"""Docs and OnlyOffice endpoints tests."""

from __future__ import annotations

from app.extensions import db
from app.models.file_ledger import FileLedger

from tests.test_auth import auth_header


def test_list_and_get_docs(client, admin_user, sample_doc):
    login_res = client.post(
        "/auth/login", json={"username": "admin", "password": "password"}
    )
    token = login_res.get_json()["access_token"]

    list_res = client.get("/api/v1/docs", headers=auth_header(token))
    assert list_res.status_code == 200
    payload = list_res.get_json()
    assert payload["meta"]["total"] == 1

    doc_res = client.get(f"/api/v1/docs/{sample_doc.id}", headers=auth_header(token))
    assert doc_res.status_code == 200
    assert doc_res.get_json()["name"] == sample_doc.name


def test_edit_config_and_callback(client, admin_user, sample_doc):
    login_res = client.post(
        "/auth/login", json={"username": "admin", "password": "password"}
    )
    token = login_res.get_json()["access_token"]

    config_res = client.get(
        f"/api/v1/docs/{sample_doc.id}/edit", headers=auth_header(token)
    )
    assert config_res.status_code == 200
    config_payload = config_res.get_json()
    assert "config" in config_payload

    callback_res = client.post(
        f"/api/v1/docs/{sample_doc.id}/callback",
        json={"status": "Saved", "users": [admin_user.id]},
    )
    assert callback_res.status_code == 200
    assert callback_res.get_json()["status"] == "received"
    assert db.session.query(FileLedger).count() == 1

    file_res = client.get(f"/files/{sample_doc.path}")
    assert file_res.status_code == 200
    assert file_res.data == b"demo document"
