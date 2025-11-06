# Lab API Backend

Lab API is a Flask 3 service that powers laboratory management workflows, including authenticated document editing via OnlyOffice, CRUD access to a curated table whitelist, and scoped JWT authorization. The project ships with Docker tooling, automated tests, and developer ergonomics for rapid onboarding.

## Key Features
- JWT-based authentication with username/password, API-key exchange, invite-only registration, and password reset flows.
- Scope-aware authorization (`db`, `doc`) enforced across REST APIs and OnlyOffice integrations.
- Generic CRUD endpoints for approved tables plus explicit lab and sample APIs.
- OnlyOffice editor configuration and callback handling with optional JWT signing.
- Alembic migrations, seeding scripts, and health checks for production readiness.
- Makefile targets for formatting, linting, typing, testing, and Docker orchestration.

## Getting Started (Local Python)
1. **Clone & configure**
   ```bash
   cp .env.example .env
   ```
   Adjust database credentials or point `DATABASE_URI` at a local MySQL/MariaDB (SQLite is fine for quick experiments).

2. **Create a virtualenv and install dependencies**
   ```bash
   make venv
   make dev
   ```

3. **Run migrations and seed an admin**
   ```bash
   FLASK_APP=app.wsgi:app flask db upgrade
   python scripts/seed_admin.py --username admin --email admin@example.com --password changeme
   ```

4. **Start the dev server**
   ```bash
   make run
   ```
   Visit `http://localhost:5000/web/login` to obtain a token bundle. Swagger UI lives at `http://localhost:5000/docs` (served from `openapi.yaml`).

## Docker Compose Stack
```bash
docker compose up -d
```
Services:
- `app`: Gunicorn-serving Flask app on `localhost:8000`.
- `db`: MariaDB 10.11 with persisted volume `db-data`.
- `redis`: Rate limiting backend.
- `onlyoffice-d`: OnlyOffice DocumentServer exposed on `http://localhost:18080`.

Fonts for OnlyOffice can be copied into `scripts/fonts/` via `scripts/load_fonts.sh`. Restart `onlyoffice-d` afterwards.

## Makefile Cheat Sheet
- `make fmt` – black format `app/` and `tests/`.
- `make lint` – ruff + flake8.
- `make type` – mypy (PEP 484 coverage).
- `make test` – pytest with coverage.
- `make docker-build` / `make docker-up` / `make docker-down` – container lifecycle helpers.
- `make check` – run fmt, lint, type, and tests sequentially.

## Testing & Quality Gates
Pytest fixtures configure an isolated SQLite database and test OnlyOffice callbacks, auth flows, CRUD endpoints, and health checks. CI should execute:
```bash
make check
```
and treat non-zero exit codes as failures. Ruff, black, mypy, and pytest already integrate with the Makefile.

## API Overview
All endpoints are documented in `openapi.yaml` and surfaced at `/docs`. Highlights:
- `POST /auth/login`, `POST /auth/refresh`, `POST /auth/` (API key exchange)
- `POST /auth/register`, `POST /auth/create_invite`, `POST /auth/request_password_reset`
- `GET /api/v1/docs`, `/api/v1/docs/{id}`, `/api/v1/docs/{id}/edit`, `/api/v1/docs/{id}/callback`
- CRUD: `GET/POST/PUT/DELETE /api/v1/table/{table}` for the whitelist in `app/models/__init__.py`
- Labs & samples: `/api/v1/labs` and `/api/v1/samples`
- Web portals: `/web/login`, `/web/list`, `/web/edit/{id}`

Pass the JWT access token via `Authorization: Bearer <token>` and ensure scope coverage (`doc` for docs, `db` for CRUD).

## OnlyOffice Integration
Configure DocumentServer’s `JWT_ENABLED` and `JWT_SECRET` to match `.env` when enabling signed requests. The `/api/v1/docs/{id}/edit` endpoint returns both an editor config and a presigned document URL exposed through `/files/<path>`. OnlyOffice callback payloads post to `/api/v1/docs/{id}/callback` and are recorded in `file_ledger` for auditing.

## Project Structure
```
lab-api/
├─ app/                # Flask application package
├─ migrations/         # Alembic environment and versions
├─ scripts/            # seed_admin.py, check_env.py, font helper
├─ tests/              # pytest suites covering auth, docs, CRUD, health
├─ Dockerfile          # Multi-stage build (Gunicorn runtime)
├─ docker-compose.yml  # App + MariaDB + Redis + OnlyOffice stack
├─ Makefile            # Developer workflow commands
├─ README.md / DEPLOY.md / openapi.yaml
└─ .env.example        # Configuration template
```

For additional operational guidance (production, backups, monitoring), read `DEPLOY.md`.
