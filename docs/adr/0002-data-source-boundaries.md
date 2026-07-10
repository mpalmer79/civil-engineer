# ADR 0002: Explicit data-source boundaries

Status: Accepted

## Context

The original `safeFetch()` helper collapsed every failure (network error, 401,
403, 404, validation, server error) into `null`, and several public demo
modules silently substituted static fixture data when the backend call
returned `null`. A reader could not tell seeded content from live content, and
an authenticated failure was indistinguishable from missing data.

## Decision

1. `apiFetch<T>()` in `lib/api/client.ts` is the typed core. It returns
   `ApiResult<T>`: success carries the data, HTTP status, and a
   `source: "backend"` marker; failure carries an error category
   (`unauthenticated`, `forbidden`, `not_found`, `validation`, `server`,
   `network`), the HTTP status when available, and a user-safe message.
2. Authenticated surfaces never substitute seeded data for a failed request.
   A 401 renders a sign-in state, a 403 a permission state, a 404 a
   missing-resource state, and a network failure a backend-unavailable state.
3. The public Brookside demo surfaces use an explicit `DemoSourced<T>` model:
   `{ data, source: "backend_seeded" | "demo_fixture" }`. The data is seeded
   either way; the marker records whether this render used the connected
   backend seed or the repository fixture snapshot. Every demo page renders a
   `DataSourceNotice` stating which one the visitor is seeing.
4. `safeFetch()` remains only as a transitional wrapper over `apiFetch()` for
   modules that model absence as `null`. It must never feed a seeded
   substitution on an authenticated path.

## Consequences

- The implicit `data ?? seededData` pattern is gone from the codebase.
- Public demo pages disclose their data source in the UI, satisfying the
  data-honesty requirement without breaking the offline-capable public demo.
- Modules can migrate from `safeFetch` to `apiFetch` incrementally as pages
  gain differentiated failure states.
