# Production Database

How Civil Engineer AI handles its data layer across local development, the
design-partner pilot, and production SaaS. This is the canonical reference for
the database provider, the migration framework, and the startup posture added in
Production Phase 4A. It pairs with `docs/RELEASE_READINESS.md`,
`docs/PILOT_RELEASE_CHECKLIST.md`, and `docs/RAILWAY_DEPLOYMENT_GUIDE.md`.

This is a data-layer foundation only. It does not change any review-support
behavior. A human reviewer remains responsible for every finding.

## Summary

- SQLite is supported for local development and tests. It is the default and
  needs no external service.
- Postgres is required for production SaaS. Production data must not live on
  ephemeral SQLite.
- Migrations are managed with Alembic. The initial migration reflects the
  current schema, including the pilot request operator fields (status, internal
  notes, last contacted timestamp).
- The provider is selected from `DATABASE_URL`. Nothing else in the application
  changes to switch databases.

## Provider selection

The database is chosen from the `DATABASE_URL` scheme:

- `sqlite:///./civil_engineer_ai.db` selects SQLite (local development and
  tests).
- A Postgres URL selects Postgres (production SaaS).

Some providers, including Railway, hand out the legacy `postgres://` scheme.
SQLAlchemy 2.0 no longer accepts it, so the backend normalizes `postgres://` and
`postgresql://` to the explicit `postgresql+psycopg2://` driver URL. The
normalization changes only the scheme; no other part of the URL is read or
altered. See `normalize_database_url` in `backend/app/db/database.py`.

The provider class is derived from the scheme only and is reported as `sqlite`,
`postgres`, or `other`. No host, credential, or path is ever read for this
classification, so it is safe to log and to return from the readiness API.

## Required environment variables

Backend service variables (set on the backend service only):

- `DATABASE_URL` - connection string. SQLite for local and tests; a Postgres URL
  for production SaaS.
- `APP_ENV` - deployment mode. `development` and `pilot` allow SQLite.
  `production` requires a Postgres `DATABASE_URL` (see Startup posture below).
  Defaults to `development`.

No database secret is logged, returned by any diagnostics or readiness route, or
stored in `alembic.ini`. The auth secret and storage credentials are documented
separately in `.env.example`.

## Dependencies

- `alembic` provides the migration framework.
- `psycopg2-binary` is the Postgres driver. It is only needed when `DATABASE_URL`
  points at Postgres; local SQLite development does not use it.

Both are pinned in `backend/requirements.txt`.

## Migration commands

Run these from the `backend/` directory, where `alembic.ini` lives. The
migration environment reads `DATABASE_URL` from the application settings, so the
same commands work against SQLite locally and Postgres in production.

- Create a new migration after a model change (autogenerate):

  ```
  alembic revision --autogenerate -m "describe the change"
  ```

  Review the generated file in `app/migrations/versions/` before applying it.
  Autogenerate is a starting point, not a substitute for review.

- Apply migrations locally:

  ```
  alembic upgrade head
  ```

- Apply migrations in deployment: run `alembic upgrade head` as a release or
  deploy step against the production `DATABASE_URL` before or as the backend
  starts. See the Railway notes below.

- Check the current migration status:

  ```
  alembic current
  ```

  Compare it to the latest revision with:

  ```
  alembic heads
  ```

- Roll back one migration (where the migration defines a downgrade):

  ```
  alembic downgrade -1
  ```

  Rollback warning: a downgrade can drop columns or tables and lose data. Take a
  backup first and only downgrade when you understand exactly what the target
  migration removes. Treat production downgrades as a last resort.

## Initial migration

The initial migration, `0001_initial_schema`, creates the full current schema
from the application's SQLAlchemy metadata, so it stays in sync with the models
that local development previously created with `create_all`. It includes the
Phase 2 through Phase 14 review entities, the organization, user, membership, and
project-access tables, the CAD intake and traceability tables, and the pilot
request table with its operator pipeline fields (status, internal notes, last
contacted timestamp).

An existing SQLite database created by the `create_all` convenience path can be
adopted under Alembic by stamping it at this revision:

```
alembic stamp 0001_initial_schema
```

Future schema changes are added as new migrations on top of this one.

## Migration history

- `0001_initial_schema`: the full schema as of Production Phase 4A.
- `0002_auth_billing_usage`: Production Phase 4B/4C account-lifecycle and
  billing-readiness tables (`password_reset_tokens`,
  `organization_invitations`, `organization_subscriptions`, `usage_events`). It
  adds tables only; it alters and drops nothing, so no existing pilot or project
  data is affected. See `docs/AUTH_LIFECYCLE.md` and `docs/BILLING_AND_USAGE.md`.
- `0003_billing_events`: Production Phase 4D Stripe webhook idempotency table
  (`billing_events`). It adds one table only and stores no Stripe secret,
  signature, or raw payload. See `docs/STRIPE_BILLING.md`.

Run `alembic upgrade head` to apply all migrations, and `alembic current` to
confirm the database is at the latest revision.

## SQLite ALTER limitations

SQLite has limited `ALTER TABLE` support. The migration environment enables
Alembic batch mode (`render_as_batch`) for SQLite so column changes can still be
applied locally. Production runs on Postgres, where this limitation does not
apply.

## Startup posture

- In `development` and `pilot` mode, SQLite is allowed and the backend starts
  normally. Local boot, tests, and preview builds are unaffected.
- In `production` mode (`APP_ENV=production`), the backend refuses to start
  unless `DATABASE_URL` is a Postgres URL. This prevents production SaaS data
  from silently living on an ephemeral SQLite file that is recreated on each
  redeploy. The check is in `check_production_database`
  (`backend/app/db/database.py`) and the error names no secret.
- The application still calls `create_all` at startup as a convenience for local
  development, tests, and the pilot prototype. `create_all` only creates missing
  tables and never alters an existing one, so the production schema is managed by
  migrations, not by that call. Run `alembic upgrade head` to apply schema
  changes in production.

## Identifying the database provider from logs

On startup the backend logs a `startup_configuration` event that includes
`app_env` and `database_kind` (the provider class: `sqlite`, `postgres`, or
`other`). The logger redacts secrets, the database URL, and raw paths, so the log
records the provider class and deployment mode without leaking any connection
detail.

## Health and readiness

- `GET /health` returns liveness only (`status`, `service`, `version`,
  `demo_mode`). No secrets.
- `GET /api/v1/readiness` returns a sanitized readiness summary. In addition to
  the existing database, authentication, and storage checks, it reports:
  - `app_env` - the deployment mode.
  - `database_provider` - the provider class (`sqlite`, `postgres`, or `other`),
    derived from the URL scheme only.
  - `migration_status` - the schema control state (`unmanaged`, `up_to_date`,
    `managed`, or `behind`).
  - a `migrations` check describing whether the schema is under Alembic control
    and current. Reported revision identifiers are short Alembic hashes, never a
    connection string.

No password, host, full connection string, provider key, or raw file path
appears in any of these responses.

## Demo seed behavior

The Brookside Meadows demo seed runs at startup and is idempotent: if the demo
project already exists, seeding is skipped, so it is safe to start the backend
repeatedly against the same database. The seed can run against a fresh database
created either by `create_all` locally or by `alembic upgrade head` in
production.

Demo seeding only loads the labeled, seeded review-support demo data plus the
CAD findings produced by really parsing the bundled sample DXF. It does not
touch real tenant data and does not wipe pilot request records. Real tenant data
never depends on reseeding. For a production deployment, demo seeding is
optional: keep it on to host the public Brookside demo, or disable the demo
posture flags to run without it.

## Railway and Postgres setup notes

1. Add a Postgres plugin to the Railway project. Railway exposes a connection
   URL as a service variable.
2. Set `DATABASE_URL` on the backend service to that Postgres URL. The legacy
   `postgres://` scheme is normalized automatically.
3. Set `APP_ENV=production` on the backend service so the startup posture check
   requires Postgres.
4. Run `alembic upgrade head` against the production database as a release step.
5. Set `AUTH_SECRET_KEY` and the production-posture auth flags as documented in
   `docs/PILOT_RELEASE_CHECKLIST.md`.

A SQLite file on Railway lives on the service file system and is recreated from
seed data on each redeploy unless a persistent volume is mounted, so it is not
suitable for production data.

## Backup and restore (high level)

- Postgres: use the provider's managed backups, or `pg_dump` for a logical
  backup and `pg_restore` (or `psql`) to restore. Take a backup before any
  migration that drops or rewrites data, and before any production downgrade.
- SQLite (local and pilot prototype only): the database is a single file; copy
  it while the app is stopped for a simple backup. SQLite is not a production
  backup target.

Treat backup and restore procedures as provider-specific operational tasks. This
document records the posture, not a full runbook.

## Known limitations

- Postgres integration is exercised at the URL and configuration level in the
  test suite; the automated suite runs on SQLite. Verify a real Postgres
  connection manually with the steps below before relying on a deployment.
- `create_all` remains available for local development, tests, and the pilot
  prototype. Production schema changes must go through Alembic migrations.
- No data migration tooling beyond Alembic schema migrations is included in this
  phase. Moving existing pilot SQLite data into Postgres is a manual, one-time
  export and import, out of scope here.
- Auth lifecycle, billing, live AI, and new analysis engines are intentionally
  out of scope for this phase.

## Manual Postgres verification

Because CI runs on SQLite, verify Postgres handling manually when preparing a
production deployment:

1. Start a local Postgres (for example with Docker) and create a database.
2. From `backend/`, set `DATABASE_URL` to the Postgres URL and `APP_ENV=pilot`
   (so the startup posture check does not require production yet), then run
   `alembic upgrade head`.
3. Confirm `alembic current` reports `0001_initial_schema`.
4. Start the backend and load `GET /api/v1/readiness`. Confirm
   `database_provider` is `postgres` and `migration_status` is `up_to_date`, and
   that no secret appears in the response.
5. Confirm the Brookside demo loads and that the public demo surfaces respond.
6. Set `APP_ENV=production` and confirm the backend starts on Postgres and would
   refuse to start on SQLite.
