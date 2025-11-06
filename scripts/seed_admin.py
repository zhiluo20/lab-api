"""Bootstrap an administrator user in the database."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is importable when running as a standalone script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed an administrator user")
    parser.add_argument("--username", required=True, help="Username for the admin user")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Plaintext password")
    parser.add_argument(
        "--database-uri",
        help="Override DATABASE_URI for this run (e.g. sqlite:///lab.db)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.database_uri:
        os.environ["DATABASE_URI"] = args.database_uri

    from app import create_app  # noqa: E402
    from app.extensions import db  # noqa: E402
    from app.models.user import User  # noqa: E402
    from app.models.user_permissions import UserPermissionEntry  # noqa: E402
    from app.utils.security import hash_password  # noqa: E402

    app = create_app()
    with app.app_context():
        existing = User.query.filter(
            (User.username == args.username) | (User.email == args.email)
        ).first()
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
