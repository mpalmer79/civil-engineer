# 0012. Durable background job queue for file processing

## Status

Accepted.

## Context

PDF page indexing and DXF metadata parsing ran on the request thread. Bounds
were added (a PDF page cap, DXF entity and layer caps, upload size limits), but a
large file still ties up a request worker for the duration of processing, and a
restart mid-processing loses the work. The ROADMAP named moving this work to a
background worker as the step before enterprise-scale load.

Constraints: no new external paid API or broker (CLAUDE.md), keep the existing
synchronous endpoints and their contracts intact, and preserve tenant isolation,
audit, and the human-review boundary. The stack is FastAPI plus SQLAlchemy on
SQLite for development and PostgreSQL for production.

## Decision

Add a durable job queue backed by the database, with a separate worker process.

1. `processing_jobs` table (`ProcessingJob` model, migration
   `0004_processing_jobs`) persists each unit of deferred work: job type, project
   scope, a small non-sensitive payload, status, retry bookkeeping, a worker
   lease, a safe error, a result summary, and the request correlation id. No file
   bytes, secrets, or stack traces are stored.

2. `job_queue_service` provides enqueue (with deduplication of active identical
   work), an atomic claim, complete, fail-with-backoff, permanent fail, stale
   reclaim, and tenant-scoped reads. Claiming is safe under concurrent workers on
   both backends: PostgreSQL uses `FOR UPDATE SKIP LOCKED`; SQLite, which
   serializes writers, uses a compare-and-set update guarded on the queued state.

3. Handlers (`job_handlers`) wrap the existing `index_pdf_document` and
   `parse_dxf_file` processors. No processing logic is duplicated: the worker runs
   the exact same code a reviewer triggers inline. Domain validation errors are
   classified as permanent and are not retried.

4. `app/worker.py` runs as a separate process (`python -m app.worker`). It creates
   its own sessions, rebinds each job's correlation id so audit rows and logs
   trace back to the enqueuing request, retries transient failures with
   exponential backoff, and reclaims jobs whose worker died.

5. The API is additive. New endpoints enqueue a job and return `202 Accepted` with
   a job resource, and poll job status, all scoped to the project with the same
   authorization as the synchronous routes. The existing synchronous index and
   parse endpoints are unchanged and remain the default for small, interactive
   files.

## Consequences

- Enterprise deployments run the worker and use the async endpoints to take file
  processing off the request thread; the request-thread bound is removed for that
  path. Small and development deployments can keep using the synchronous routes
  and need not run the worker.
- Because the queue is in the primary database, there is no broker to operate.
  At very high throughput a dedicated broker could be revisited, but the DB-backed
  queue is sufficient for the current and pilot scale.
- The synchronous and asynchronous routes coexist by design: same processor, two
  schedulers. This is not duplicated business logic.
- Frontend adoption of the async endpoints (enqueue then poll) is future work; the
  generated API types already include them.
