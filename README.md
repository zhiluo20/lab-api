# Lab API Backend

Lab API is a Flask 3 service that powers laboratory management workflows, including authenticated document editing via OnlyOffice, CRUD access to a curated table whitelist, and scoped JWT authorization. The project ships with Docker tooling, automated tests, and developer ergonomics for rapid onboarding.

## Key Features
- JWT-based authentication with username/password, API-key exchange, invite-only registration, and password reset flows.
- Scope-aware authorization (`db`, `doc`) enforced across REST APIs and OnlyOffice integrations.
- Generic CRUD endpoints for approved tables plus explicit lab and sample APIs.
- OnlyOffice editor configuration and callback handling with optional JWT signing.
- Alembic migrations, seeding scripts, and health checks for production readiness.
- Makefile targets for formatting, linting, typing, testing, and Docker orchestration.
- Built-in admin panel (`/admin/users?token=...`) for managing accounts, roles, permissions, document lifecycle, and audit logs.
- Built-in admin panel (`/admin/users?token=...`) for managing accounts, scopes, and activation without leaving the browser.

## Getting Started (Local Python)
1. **Clone & configure**
   ```bash
   cp .env.example .env
   ```
   Adjust database credentials or point `DATABASE_URI` at a local MySQL/MariaDB (SQLite is fine for quick experiments). The default `RATE_REDIS_URL=memory://` keeps rate limiting in-process; set it to your Redis instance only when one is available.

2. **Create and activate the virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # macOS/Linux
   # .venv\Scripts\activate.bat     # Windows (Command Prompt)
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   The Makefile provides shortcuts if you prefer:
   ```bash
   make venv
   source .venv/bin/activate
   make dev
   ```
   Re-run `source .venv/bin/activate` whenever you return to the project in a new shell.

3. **Run migrations and seed an admin**
   ```bash
   DATABASE_URI=sqlite:///lab.db FLASK_APP=app.wsgi:app flask db upgrade
   python scripts/seed_admin.py --username admin --email admin@example.com --password changeme --database-uri sqlite:///lab.db
   ```
   The commands above target a local SQLite file (`lab.db`). If you prefer MariaDB/MySQL, point `DATABASE_URI` to your server (e.g. `mysql+pymysql://user:pass@localhost:3306/labcode`) and omit the `--database-uri` override when seeding. The migration creates default roles (`admin`, `editor`, `viewer`) and seeds their permission matrix.

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

### Using the Compose database from the host
If you want to run the Flask app directly against the dockerised MariaDB, export:
```bash
export DATABASE_URI="mysql+pymysql://labadmin:password@127.0.0.1:3306/labcode"
export RATE_REDIS_URL="redis://127.0.0.1:6379/0"
```
and then repeat the migration/seed steps without overriding the URI. (Mac/Windows users may need to replace `127.0.0.1` with the Docker host address.)

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

## Admin Panel Quick Tour
Sign in as an administrator (e.g. `admin/changeme`) and you will be redirected to the document catalogue. If the account has admin privileges, an **Admin Panel** button appears, linking to `/admin/users?token=<access_token>`. The panel provides:

- **Dashboard:** high-level metrics and recent activity feed (audit entries stored in `activity_logs`).
- **User Management:** search/filter, create, edit, disable/delete users, reset passwords, assign roles/scopes, inspect login history.
- **Role & Permission Builder:** create roles, tweak permission matrix (resources/actions), flag defaults for new sign-ups, and remove deprecated roles.
- **Document Control:** search documents, inspect version history, manage shares, leave comments, and log governance actions (including ad-hoc version notes).

All admin actions are captured in `activity_logs`, and login attempts are tracked inside `login_logs`. Use the generated links in the UI or call the REST APIs with the same access token (`Authorization: Bearer <token>`).

> Tip: The admin panel is token-driven. If you bookmark a view, keep the `?token=` portion or obtain a fresh token from `/web/login`.

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

> ℹ️ **Tip:** After exporting environment variables (e.g. `export DATABASE_URI=sqlite:///lab.db`), they apply only to that terminal session. Activate your virtual environment (`source .venv/bin/activate`) and re-export the variables whenever you open a new shell before rerunning migration or seeding commands.
