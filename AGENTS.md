# AGENTS.md

FastAPI + async SQLAlchemy 2.0 + PostgreSQL, Pydantic v2, Alembic, Celery (RabbitMQ/Redis), Poetry. Python 3.12 only (`>=3.12,<3.13`).

## Commands (run via `poetry run`)
- Run API: `poetry run uvicorn app.main:app --reload`
- All tests: `poetry run pytest`
- Single file: `poetry run pytest tests/services/test_contact_service.py`
- Lint/format/typecheck (no config files — tool defaults): `poetry run ruff check .`, `poetry run black .`, `poetry run mypy app`
- Migration: `poetry run alembic revision --autogenerate -m "..."` then `poetry run alembic upgrade head`
- Dev DB only: `docker compose up -d db`; full stack (db, migrations, app, worker, rabbitmq, redis): `docker compose up --build`

## Setup gotchas
- `.env` is gitignored but **required** — pydantic-settings validates every field at import (`app/core/config.py`). Copy `.env.example` and fill it in before running anything, including tests.
- Tests hit a **real PostgreSQL** at `TEST_DATABASE_URL`. `tests/conftest.py` creates/drops all tables via `Base.metadata.create_all` (NOT Alembic). Start Postgres and create the `TEST_DB_NAME` database before running tests.
- Two DB drivers in play: app uses `DATABASE_URL` (asyncpg), Alembic uses `ALEMBIC_DATABASE_URL` (sync psycopg, same creds). Never reuse one for the other.

## Architecture
- Layered: `app/api` (thin routers) → `app/services` (business logic, take a `UnitOfWork`) → `app/repositories` → `app/models`. Pydantic schemas in `app/schemas`.
- Services reach repositories dynamically via `uow.<name>_repo` — `UnitOfWork.__getattr__` in `app/db/uow.py` looks up `app/db/repositories_registry.py`. A repo is only available if registered in both.
- Routes are sync `def`; DB layer is async (`asyncpg`). Exceptions: domain errors subclass `AppError` and are rendered by the handler in `app/api/exception.py`.

## Adding things — update every registry
- **New model**: import it in `app/models/__init__.py` AND add an explicit import in `migrations/env.py` (it imports models individually, not the package), otherwise autogenerate misses it.
- **New repository**: add to `REPOSITORIES` in `app/db/repositories_registry.py`, annotate the attribute on `UnitOfWork` (`app/db/uow.py`), and add a `Mock` for it in `tests/fakes/fake_uow.py`.
- **New channel/provider**: extend `ChannelType` enum, implement `BaseProvider` in `app/providers/`, register in `ProviderRegistry` (`app/providers/provider_registry.py`), and add a validator in `app/validators/contact_methods/registry.py`.

## Tests
- `pytest.ini`: `asyncio_mode = auto` and `pythonpath = .` — async tests need no marker; run pytest from repo root.
- Layout mirrors `app`: `tests/{services,repositories,providers}`. Fixtures are pytest plugins registered in `tests/conftest.py` (`tests/fixtures/...`).
- Service and provider tests use `FakeUnitOfWork` (unittest.mock `Mock`s, `tests/fakes/fake_uow.py`); repository tests use the real DB via the `db_session`/`*_repo` fixtures.
- Provider tests patch at the module path, e.g. `app.providers.email.aiosmtplib.SMTP` (see `tests/providers/test_email_provider.py`).

## Notifications flow
- `POST /notifications/{id}` runs `app/tasks/notification.py:send_notification_task` via FastAPI `BackgroundTasks` — this is a plain async function, **not** a Celery task yet (see TODO in `app/api/notification.py`). The Celery worker (`celery -A app.celery_app.celery_app worker`) is wired for `app.tasks` but not used for sending.
- Delivery statuses: PENDING → SENT/FAILED; notification finalizes to SUCCESS / FAILED / PARTIAL_SUCCESS in `NotificationService.finalize_notification`.

## Conventions
- Conventional commits (see git log): `feat(scope):`, `refactor:`, `test:`, `fix:`.
- Add/update tests in the mirror directory whenever touching a layer.
