# Backend-for-frontend proxy threat model

Scope: `app/api/backend/[...path]/route.ts` (the catch-all proxy) and the
`/api/session/*` route handlers. The proxy is the only path by which a browser
request can reach the FastAPI backend with credentials, so it is treated as
security infrastructure with its own test suite
(`app/api/__tests__/backendProxy.test.ts`).

## Assets

- The backend access token in the `ce_session` HttpOnly cookie.
- Tenant-scoped review data served by FastAPI.
- Next.js process memory and event loop (availability).
- The internal backend origin and its network position.

## Trust boundaries

- Browser to Next.js: untrusted. Anything in the request line, headers, or
  body is attacker-controllable.
- Next.js to FastAPI: trusted channel to a fixed, configured origin
  (`BACKEND_API_BASE_URL` or `NEXT_PUBLIC_API_BASE_URL`). FastAPI remains the
  authorization authority; the proxy never makes access decisions beyond its
  own gate checks.

## Threats and mitigations

| Threat | Mitigation |
| --- | --- |
| Open-proxy abuse (attacker-selected upstream) | The upstream origin is fixed at module load from configuration. No query parameter, header, body field, or route segment can change it. Absolute URL patterns (`http:`, `https:`, `//`) in the path are rejected. |
| Path traversal | Path segments are individually re-encoded; segments containing `..`, `.`, empty strings, backslashes, or percent-encoded traversal (`%2e`, `%2f`, `%5c`) are rejected before any forwarding. Only paths beginning with `api/` pass. |
| Unsupported methods | Only GET, POST, PUT, PATCH, and DELETE are exported; Next.js returns 405 with an `Allow` header for everything else (verified by test). CONNECT and TRACE are never handled. |
| Oversized JSON bodies | A declared `Content-Length` above the route-class limit is rejected with 413 before reading the body. Because `Content-Length` alone is untrustworthy, the streamed body is also counted and aborted at the limit. JSON mutation limit: 2 MB. Auth JSON limit (session endpoints): 64 KB. |
| Oversized uploads / memory exhaustion | Upload paths (multipart) stream the request body to the backend through a counting TransformStream; the request is aborted when the byte count exceeds the limit (project uploads 25 MB, CAD uploads 5 MB, matching backend `MAX_PROJECT_UPLOAD_BYTES` and `CAD_MAX_UPLOAD_BYTES`). The proxy never buffers an upload into a single ArrayBuffer. |
| Slow upstream / resource pinning | Explicit per-class upstream timeouts via AbortSignal: auth 10 s, JSON API 30 s, uploads 120 s. On timeout the upstream request is aborted and the client receives a typed 504 with a correlation ID, distinguishable from 502 backend-unavailable. |
| Client disconnects | The client request's abort signal is linked to the upstream fetch, so an abandoned browser request aborts the backend call. |
| Header injection / smuggling | Request headers are allowlisted: only `content-type` and `accept` are forwarded. `Host`, `Connection`, `Transfer-Encoding`, `Forwarded`, `X-Forwarded-*`, `Proxy-Authorization`, incoming `Authorization`, and incoming `Cookie` are never forwarded. |
| Credential leakage to the backend or logs | The Authorization header is constructed only from the HttpOnly cookie, server side. The token never appears in URLs, response bodies, logs, or correlation output. |
| Response-header leakage | Response headers are allowlisted: `content-type`, `content-disposition`, `cache-control`, and the correlation ID. Backend `Set-Cookie`, `Server`, and any other implementation headers are dropped. |
| CSRF on mutations | Two independent checks: when `Origin` is present it must match the configured trusted application origin (or the request host when no explicit origin is configured), and the custom `x-csrf-protection: 1` header must be present. Cross-site attackers cannot add custom headers without a CORS preflight the browser refuses. |
| Stale or invalid sessions | When the backend answers 401 to a request that carried a session cookie, the proxy clears `ce_session` and `ce_session_active` on the response and adds `x-session-expired: 1`, so the client renders an explicit signed-out state instead of trusting a stale indicator. |
| Malformed multipart | The proxy does not parse multipart; it enforces size and streams bytes. Multipart validation (boundaries, file types, per-file limits) remains the backend's responsibility, unchanged. |
| Unauthorized access | The proxy adds no authority: requests without a session cookie are forwarded without Authorization and receive the backend's public-data or 401 semantics unchanged. Tenant guards live in FastAPI. |
| Backend unavailability | Network failure returns a typed 502 with a correlation ID and no internal URL. Timeout returns 504. Both are distinguishable by the client. |
| Request correlation | Every proxied request gets a UUID correlation ID (or validates a client-supplied `x-request-id` of at most 64 safe characters). It is sent upstream as `x-request-id`, returned on the response, and included in error payloads. No credential material is ever attached to it. |

## Non-goals

- The proxy does not rate limit; FastAPI login rate limiting and platform
  level protections are the control there.
- The proxy does not rewrite or interpret response bodies.
- WebSocket upgrades are not supported or forwarded.

## Verification

`app/api/__tests__/backendProxy.test.ts` covers each row above with request
level tests, including traversal payloads, oversized declared and streamed
bodies, timeout behavior, header allowlists in both directions, cookie
clearing on 401, and correlation ID propagation. The threat model must be
updated in the same change as any proxy behavior change.
