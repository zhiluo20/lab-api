"""Tests for admin panel workflows."""

from __future__ import annotations

from app.extensions import db
from app.models.user import User
from app.models.user_permissions import UserPermissionEntry
from app.utils.security import hash_password


def login_and_get_token(client):
    resp = client.post(
        "/auth/login", json={"username": "admin", "password": "password"}
    )
    assert resp.status_code == 200
    return resp.get_json()["access_token"]


def test_admin_access_requires_token(client, admin_user):
    resp = client.get("/admin")
    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("/web/login")


def test_admin_user_listing_and_scope_toggle(client, admin_user):
    token = login_and_get_token(client)

    # Create another user to manipulate
    user = User(
        username="guest",
        email="guest@example.com",
        password_hash=hash_password("guest-pass"),
    )
    user.permissions.append(UserPermissionEntry(scope="doc"))
    db.session.add(user)
    db.session.commit()

    listing = client.get(f"/admin/users?token={token}")
    assert listing.status_code == 200
    assert "guest@example.com" in listing.get_data(as_text=True)

    toggle = client.post(
        f"/admin/users/{user.id}/scopes",
        data={"token": token, "scope": "db", "action": "add"},
        follow_redirects=True,
    )
    assert toggle.status_code == 200
    db.session.refresh(user)
    assert "db" in {perm.scope for perm in user.permissions}

    deactivate = client.post(
        f"/admin/users/{user.id}/status",
        data={"token": token, "action": "toggle_active"},
        follow_redirects=True,
    )
    assert deactivate.status_code == 200
    db.session.refresh(user)
    assert user.is_active is False
