# Deployment Guide

This guide describes how to deploy the Lab API stack into production-like environments.

## 1. Pre-flight Checklist
- **Secrets:** set `SECRET_KEY`, `JWT_SECRET_KEY`, `OO_JWT_SECRET`, database credentials, and `API_KEYS_JSON`. Never reuse defaults.
- **Environment:** export variables or mount a `.env` file. Run `python scripts/check_env.py` to verify required values.
- **Database:** provision MariaDB/MySQL with backups enabled (binlog + nightly snapshots). Ensure the application user has least-privilege access to the `labcode` schema.
- **Redis:** deploy a Redis instance for Flask-Limiter. Configure persistence (AOF/RDB) based on RPO requirements.
- **OnlyOffice:** provision `onlyoffice/documentserver` and set `JWT_ENABLED=true` with the same `OO_JWT_SECRET`. Mount custom fonts to `/usr/share/fonts/truetype/custom` and refresh via `fc-cache -f -v`.

## 2. Build & Release
- Build the multi-stage image: `docker build -t registry.example.com/lab-api:<tag> .`
- Push to registry and promote through environments using tags.
- Run database migrations in CI/CD:
  ```bash
  docker run --rm --env-file .env registry.example.com/lab-api:<tag> flask db upgrade
  ```

## 3. Runtime Configuration
- Run Gunicorn with at least 2 workers behind a reverse proxy (Nginx/Traefik). Example command:
  ```bash
  gunicorn -b 0.0.0.0:8000 --workers 4 --timeout 60 app.wsgi:app
  ```
- Configure health probes:
  - Liveness: `GET /healthz`
  - Readiness: `GET /health`
- Enforce HTTPS and forward headers (`X-Forwarded-*`). Enable request logging in the reverse proxy.

## 4. Observability & Security
- Centralize logs (stdout/stderr) to your logging stack. Consider enabling structured JSON logs via Gunicorn configuration.
- Hook the `/metrics` endpoint of your infra (or add Prometheus exporters) for CPU, memory, and DB metrics.
- Integrate alerting for 5xx spikes, DB connection exhaustion, and Redis errors.
- Enable Sentry or another APM by exporting `SENTRY_DSN`.
- Configure firewalls/security groups to allow OnlyOffice → Lab API callbacks and block public database access.

## 5. Data & Backup Strategy
- Automate MariaDB dumps (e.g. `mysqldump` nightly) plus binary logs for point-in-time recovery.
- Snapshot the document store (`BASE_FILE_DIR`) alongside database backups.
- Regularly test restoration drills and verify seeded admin credentials.

## 6. Post-Deployment Validation
1. `GET /healthz` returns `200` with `{ "status": "ok" }`.
2. Seeded admin authenticates via `POST /auth/login` and receives tokens.
3. Access `/web/list?token=<access-token>` to confirm docs render.
4. Hit `/api/v1/docs/{id}/edit` with a valid token to inspect OnlyOffice config.
5. Execute `make test` (or the CI suite) against the deployed build artifact.

## 7. Rollback Plan
- Retain the previous container image and DB snapshot.
- On failure, scale down the new deployment, redeploy the prior image, and restore DB/filesystem from the latest good backup.
- Document root cause and prevention steps before reattempting rollout.

Keep this document updated as new infrastructure components or SLAs evolve.
