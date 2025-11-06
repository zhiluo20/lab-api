"""Authentication endpoint tests."""

from __future__ import annotations

from flask_jwt_extended import decode_token

from app.extensions import db
from app.models.user import User
from app.models.user_permissions import UserPermissionEntry
from app.utils.security import hash_password
from tests.conftest import TEST_API_KEY


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_and_refresh(client, admin_user):
    res = client.post("/auth/login", json={"username": "admin", "password": "password"})
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data and "refresh_token" in data

    refresh = client.post("/auth/refresh", headers=auth_header(data["refresh_token"]))
    assert refresh.status_code == 200
    refreshed = refresh.get_json()
    assert refreshed["token_type"] == "bearer"


def test_change_password_flow(client, admin_user):
    login_res = client.post(
        "/auth/login", json={"username": "admin", "password": "password"}
    )
    access_token = login_res.get_json()["access_token"]

    change_res = client.post(
        "/auth/change_password",
        headers=auth_header(access_token),
        json={"current_password": "password", "new_password": "new-pass"},
    )
    assert change_res.status_code == 200

    new_login = client.post(
        "/auth/login", json={"username": "admin", "password": "new-pass"}
    )
    assert new_login.status_code == 200


def test_register_with_invite(client, invite_code):
    res = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "secret",
            "invite_code": invite_code.code,
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["user"]["username"] == "newuser"


def test_password_reset_flow(client, admin_user):
    # Create second user
    user = User(
        username="resetme",
        email="reset@example.com",
        password_hash=hash_password("abc123"),
    )
    db.session.add(user)
    db.session.flush()
    db.session.add(UserPermissionEntry(user_id=user.id, scope="doc"))
    db.session.add(UserPermissionEntry(user_id=user.id, scope="db"))
    db.session.commit()

    req = client.post(
        "/auth/request_password_reset", json={"email": "reset@example.com"}
    )
    token = req.get_json()["token"]

    perform = client.post(
        "/auth/perform_password_reset", json={"token": token, "password": "newpass"}
    )
    assert perform.status_code == 200

    login = client.post(
        "/auth/login", json={"username": "resetme", "password": "newpass"}
    )
    assert login.status_code == 200


def test_api_key_exchange(client):
    res = client.post("/auth/", json={"api_key": TEST_API_KEY})
    assert res.status_code == 200
    data = res.get_json()
    with client.application.app_context():
        decoded = decode_token(data["access_token"], allow_expired=False)
    assert "doc" in decoded["scopes"]


def test_create_invite_requires_admin(client, admin_user):
    login_res = client.post(
        "/auth/login", json={"username": "admin", "password": "password"}
    )
    assert login_res.status_code == 200
    token = login_res.get_json()["access_token"]
    res = client.post(
        "/auth/create_invite",
        headers=auth_header(token),
        json={"email": "guest@example.com", "expires_in_hours": 12, "max_uses": 2},
    )
    assert res.status_code == 201
    payload = res.get_json()
    assert "code" in payload
