"""Bootstrap an administrator user in the database."""

from __future__ import annotations

import argparse

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.user_permissions import UserPermissionEntry
from app.utils.security import hash_password


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed an administrator user")
    parser.add_argument("--username", required=True, help="Username for the admin user")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Plaintext password")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = create_app()
    with app.app_context():
        existing = User.query.filter((User.username == args.username) | (User.email == args.email)).first()
        if existing:
            print("User already exists; skipping seeding")
            return
        user = User(
            username=args.username,
            email=args.email,
            password_hash=hash_password(args.password),
            is_admin=True,
        )
        db.session.add(user)
        db.session.flush()
        for scope in ("db", "doc"):
            db.session.add(UserPermissionEntry(user_id=user.id, scope=scope))
        db.session.commit()
        print(f"Seeded administrator user '{args.username}'")


if __name__ == "__main__":
    main()
