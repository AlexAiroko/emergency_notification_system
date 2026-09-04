# AGENTS.md

FastAPI + async SQLAlchemy 2.0 + PostgreSQL, Pydantic v2, Alembic, Celery (RabbitMQ/Redis), Poetry. Python 3.12 only (`>=3.12,<3.13`).

## Commands (run via `poetry run`)
- Run API: `poetry run uvicorn app.main:app --reload`
- Celery worker: `poetry run celery -A app.celery_app.celery_app worker --loglevel=info`
- Celery beat (sweeper for retries/recovery): `poetry run celery -A app.celery_app.celery_app beat --loglevel=info`
- All tests: `poetry run pytest`
- Single file: `poetry run pytest tests/services/test_contact_service.py`
- Lint/format/typecheck (no config files — tool defaults): `poetry run ruff check .`, `poetry run black .`, `poetry run mypy app`
- Migration: `poetry run alembic revision --autogenerate -m "..."` then `poetry run alembic upgrade head`
- Audit dependencies: `poetry run pip-audit`
- Dev DB only: `docker compose up -d db`; full stack (db, migrations, app, worker, rabbitmq, redis, prometheus, grafana): `docker compose up --build`

## Setup gotchas
- `.env` is gitignored but **required** — pydantic-settings validates every field at import (`app/core/config.py`). Copy `.env.example` and fill it in before running anything, including tests.
- Tests hit a **real PostgreSQL** at `TEST_DATABASE_URL`. `tests/conftest.py` creates/drops all tables via `Base.metadata.create_all` (NOT Alembic). Start Postgres and create the `TEST_DB_NAME` database before running tests.
- Two DB drivers in play: app uses `DATABASE_URL` (asyncpg), Alembic uses `ALEMBIC_DATABASE_URL` (sync psycopg, same creds). Never reuse one for the other.
- Celery sending requires the broker (RabbitMQ) and backend (Redis) to be up — `docker compose up -d rabbitmq redis`. The API runs without them, but enqueuing `.delay()` needs a reachable broker.
- `mypy app` intentionally reports ~13 errors in the repositories from `BaseRepository.model = None` (`app/repositories/base.py`) — an accepted trade-off (no generics). Do not "fix" by re-annotating `model`.
- SMS (`ChannelType.SMS`) is enum + validator only; **no provider is registered**, so SMS deliveries always fail. It is future work, not usable in v1.

## Architecture
- Layered: `app/api` (thin routers) → `app/services` (business logic, take a `UnitOfWork`) → `app/repositories` → `app/models`. Pydantic schemas in `app/schemas`.
- Routes obtain services via FastAPI `Depends()` — factories live in `app/db/deps.py` (e.g., `get_notification_service`, `get_delivery_service`). These inject the shared `RateLimiter` singleton into services that need rate limiting.
- Services reach repositories dynamically via `uow.<name>_repo` — `UnitOfWork.__getattr__` in `app/db/uow.py` looks up `app/db/repositories_registry.py`. A repo is only available if registered in both.
- Routes are sync `def`; DB layer is async (`asyncpg`). Exceptions: domain errors subclass `AppError` and are rendered by the handler in `app/api/exception.py`.
- Re-exports: `app/models/__init__.py`, `app/repositories/__init__.py`, `app/services/__init__.py`, `app/providers/__init__.py` all re-export their public classes with `__all__`. Import via the package (`from app.repositories import ContactRepository`), never via submodules from outside the package. Inside a package, use direct submodule imports to avoid circular dependencies.

## Adding things — update every registry
- **New model**: import it in `app/models/__init__.py` AND add an explicit import in `migrations/env.py` (it imports models individually, not the package), otherwise autogenerate misses it.
- **New repository**: add class to the package, then re-export it in `app/repositories/__init__.py` (add to both the import and `__all__`), add to `REPOSITORIES` in `app/db/repositories_registry.py`, annotate the attribute on `UnitOfWork` (`app/db/uow.py`), and add a `Mock` for it in `tests/fakes/fake_uow.py`.
- **New channel/provider**: extend `ChannelType` enum, implement `BaseProvider` in `app/providers/`, register in `ProviderRegistry` (`app/providers/provider_registry.py`), and add a validator in `app/validators/contact_methods/registry.py`. (SMS in v1 is enum + validator only — no provider.)
- **New Celery task**: put it in `app/tasks/` (package is autodiscovered); register periodic/beat tasks in `app/celery_app.py`.

## Rate Limiting
- `RateLimiter` (`app/core/rate_limiter.py`) — singleton, Redis sliding-window algorithm. Accessed via `get_rate_limiter()`. Lazy connect: Redis connection opens on first `acquire()`, not at import. Call `close()` on shutdown (done in `app/main.py` lifespan).
- Integrated into `DeliveryService.send_delivery()` — called before every provider dispatch. When limit is exceeded, delivery is retried in 1 second and the rejection is counted in metrics.
- Config: `RATE_LIMIT_EMAIL` (requests/min), `RATE_LIMIT_TELEGRAM` (requests/min) in `app/core/config.py`.

## Metrics & Monitoring
- `GET /metrics` — Prometheus text format. 5 business metrics:
  - `ens_notifications_total` (counter, label: status)
  - `ens_deliveries_total` (counter, labels: channel, status)
  - `ens_delivery_retries_total` (counter, label: channel)
  - `ens_rate_limit_rejects_total` (counter, label: channel)
  - `ens_notifications_in_progress` (gauge)
- `MetricsCollector` singleton in `app/metrics/registry.py`. Services call `get_metrics_collector()` to increment counters/gauges.
- Config: `METRICS_ENABLED: bool` in `app/core/config.py`.
- Prometheus scrapes `app:8000/metrics` every 15s (`monitoring/prometheus/prometheus.yml`).
- Grafana auto-provisioned at `http://localhost:3000` (admin/admin) with ENS dashboard (`monitoring/grafana/dashboards/ens.json`). Datasource + dashboard provisioned via YAML.
- Start monitoring: `docker compose up -d prometheus grafana`

## Logging
- Configured in `app/core/logging.py`, imported by `app/main.py` at startup.
- `setup_logging()` configures root logger with a `StreamHandler(sys.stdout)`.
- Format: `TextFormatter` (default, human-readable) or `JSONFormatter` (structured, for production).
- Config: `LOG_LEVEL` (DEBUG/INFO/WARNING/ERROR/CRITICAL), `LOG_FORMAT` (text/json) in `app/core/config.py`.
- All modules use `logger = logging.getLogger(__name__)`. Lazy `%s` formatting in all logger calls. No f-strings inside `logger.xxx()`.
- UoW logs session lifecycle (DEBUG), rollback warnings (WARNING), commit/rollback failures (EXCEPTION).
- Error handler logs every domain error at ERROR level.

## Tests
- `pytest.ini`: `asyncio_mode = auto` and `pythonpath = .` — async tests need no marker; run pytest from repo root.
- Layout mirrors `app`: `tests/{services,repositories,providers,tasks,core,api,metrics}`. Fixtures are pytest plugins registered in `tests/conftest.py` (`tests/fixtures/...`).
- Service and provider tests use `FakeUnitOfWork` (unittest.mock `Mock`s, `tests/fakes/fake_uow.py`); repository tests use the real DB via the `db_session`/`*_repo` fixtures.
- Provider tests patch at the module path, e.g. `app.providers.email.aiosmtplib.SMTP` (see `tests/providers/test_email_provider.py`).
- Celery task tests live in `tests/tasks/` and exercise the task functions directly (asserting on the fake UoW / DB) without a live broker.

## Notifications flow
- `POST /notifications` creates the Notification plus one PENDING `Delivery` per **active** contact method of each active contact (`NotificationService._prepare_deliveries`). `POST /notifications/{id}` enqueues the Celery task `send_notification_task.delay(notification_id)` — **not** BackgroundTasks. The task wraps the async UoW flow with `run_async()` (`app/core/async_utils.py`) — a per-process event loop helper, not `asyncio.run()`.
- Sending is **batched**: notification work is split into chunks of ~100–200 deliveries, each chunk a separate task, so workers scale independently of the API (`app/tasks/delivery.py`). Finalization runs only after every chunk of the notification finished.
- Delivery statuses: PENDING → SENT / FAILED. A failed attempt increments `attempts`; while `attempts < RETRY_COUNT` (default 5) the delivery returns to PENDING with `next_attempt_at = now + RETRY_INTERVAL` (default 1 min), otherwise it stays FAILED for manual handling (`app/services/delivery.py`, config in `app/core/config.py`). `SENT` deliveries are never re-sent; re-delivering a whole notification is allowed.
- Guaranteed delivery: durable queue, `worker_ack_late=True`, `worker_prefetch_multiplier=1`. Beat task `sweep_deliveries` (every minute) re-drives due retries and resumes notifications stuck in `IN_PROGRESS` after a crash.
- A notification finalizes to SUCCESS / FAILED / PARTIAL_SUCCESS in `NotificationService.finalize_notification` only when all its deliveries are terminal (no PENDING left).

## Conventions
- Conventional commits (see git log): `feat(scope):`, `refactor:`, `test:`, `fix:`.
- Add/update tests in the mirror directory whenever touching a layer.
