# Changelog

## [0.2.0] - Admin panel & RBAC
- Introduced role-based access control models (roles, role_permissions, user_roles) and login/activity auditing tables.
- Shipped a fully token-driven admin console (`/admin/*`) covering dashboards, user management, role matrix editing, and document lifecycle (versions, shares, comments).
- Captured login metadata and activity logs during authentication, seeded default roles during migrations, and expanded tests/fixtures accordingly.
- Enhanced README/DEPLOY docs to explain the new workflows and kept lint/type/test automation intact.

## [0.1.0] - Initial scaffold
- Bootstrapped Flask 3 application with JWT auth, scoped permissions, and rate limiting.
- Added SQLAlchemy ORM models, Alembic migrations, and OnlyOffice integration helpers.
- Implemented REST blueprints for auth, docs, CRUD, labs, samples, and HTML views.
- Delivered Dockerfile, docker-compose stack, Makefile workflows, and environment scripts.
- Authored pytest suite, OpenAPI spec, README, and deployment guide.
