# 0011. Request correlation, structured logging, and safe error handling

## Status

Accepted.

## Context

The backend had a small secret-safe logger but no way to trace a single request
across its log lines and its audit rows. The `audit_events` table already
carried a `request_id` column, but nothing ever populated it. Uncaught
exceptions fell through to the framework default with no central logging and no
correlation returned to the client. Log verbosity was hardcoded, and PDF
indexing iterated every page inline with no bound.

The system remains a review-support platform. Observability must never weaken
that boundary or leak secrets, credentials, raw paths, request bodies, or client
IP addresses.

## Decision

1. A per-request correlation id is assigned by `RequestContextMiddleware`. A
   safe inbound `X-Request-Id` is reused; otherwise a fresh id is generated. The
   id is held in a context variable, echoed on the response `X-Request-Id`
   header, and merged into every structured log event for the request.

2. Request context lives in `app/core/request_context.py` as context variables
   (correlation id, and the resolved user, organization, and project when
   known). Context variables isolate values per request and per async task.

3. `log_event` merges the current request context into every event and keeps the
   existing redaction of secret-like and path-like fields. One
   `request_completed` event per request records method, route, status, and
   duration.

4. A single SQLAlchemy `before_insert` listener on `AuditEvent` fills
   `request_id` from the context when a caller did not set it. This populates the
   existing column everywhere without editing dozens of audit call sites and
   never overrides an explicit value or any other attribution field.

5. A global exception handler returns a generic
   `{"detail": "Internal server error.", "request_id": ...}` with status 500. The
   exception type and route are logged server side with the correlation id; the
   message, stack trace, and internal detail never reach the client. Typed route
   errors keep their own status codes.

6. `LOG_LEVEL` makes verbosity configurable per environment, defaulting to INFO
   and falling back to INFO on an unknown value rather than failing startup.

7. `PDF_MAX_PAGES` bounds inline PDF indexing. Pages beyond the cap are left for
   reviewer follow-up and the document is flagged `indexed_partial_needs_review`.

## Consequences

- A request id from a client response or support report is enough to find the
  request's access log, application events, and audit rows.
- No external APM, Sentry, or OpenTelemetry dependency is introduced; this stays
  standard library only, consistent with the existing logger.
- Technical metrics (request counters, latency histograms, a `/metrics`
  endpoint) and moving file and DXF processing to a background worker remain
  future work, tracked in `docs/ROADMAP.md`.
- The redaction list stays the single guard against secret leakage in logs; new
  secret-like field names must keep matching it.
