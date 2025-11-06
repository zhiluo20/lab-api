"""Validate required environment variables for deployment."""

from __future__ import annotations

import sys

from app.config import Settings

REQUIRED_FIELDS = [
    "secret_key",
    "jwt_secret_key",
    "database_uri",
    "oo_base_url",
    "base_file_dir",
]


def main() -> None:
    settings = Settings()
    missing = [field for field in REQUIRED_FIELDS if not getattr(settings, field)]
    if missing:
        print("Missing environment variables:", ", ".join(missing))
        sys.exit(1)
    print("Environment looks good.")


if __name__ == "__main__":
    main()
