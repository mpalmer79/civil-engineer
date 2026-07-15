"""Guard-regression test for project-scoped routes.

This protects the Phase 2B tenant isolation work from silent regressions: if a new
route with a ``{project_id}`` path parameter is added without calling one of the
project access guards, this test fails and names the route.

The check inspects the source of each route's endpoint function for a guard call,
because the guards are invoked in the function body (for example
``require_project_read(db, project_id, user)``) rather than declared as a
``Depends`` dependency. That keeps the test resilient to route ordering and to
how the dependency graph is assembled.

Routes that are genuinely project-scoped in their path but intentionally not
tenant-gated must be added to ``ALLOWLIST`` with a reason, so every such route is
an explicit, reviewed decision rather than an accident.
"""

from __future__ import annotations

import inspect

from fastapi.routing import APIRoute

from app.main import app

# Tokens that indicate a route enforces access. Any one is sufficient.
GUARD_TOKENS = (
    "require_project_read",
    "require_project_reviewer",
    "require_project_admin",
    "require_admin_user",
    "get_current_user",
)

# (method, path) pairs that contain {project_id} but are intentionally not
# project-access gated. Each entry needs a documented reason. Empty today: every
# project-scoped route is guarded.
ALLOWLIST: dict[tuple[str, str], str] = {}


def _walk_api_routes(routes: list[object]) -> list[APIRoute]:
    # Starlette 1.x wraps included routers lazily (_IncludedRouter), so the
    # application's route list is no longer flat. Walk both shapes: flat
    # APIRoute entries and nested routers reachable through original_router
    # or a routes attribute.
    found: list[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
        elif hasattr(route, "original_router"):
            found.extend(_walk_api_routes(route.original_router.routes))
        elif hasattr(route, "routes"):
            found.extend(_walk_api_routes(route.routes))
    return found


def _project_scoped_routes() -> list[tuple[str, str, object]]:
    found: list[tuple[str, str, object]] = []
    for route in _walk_api_routes(app.routes):
        if "{project_id}" not in route.path:
            continue
        for method in sorted(route.methods or []):
            if method in {"HEAD", "OPTIONS"}:
                continue
            found.append((method, route.path, route.endpoint))
    return found


def test_every_project_scoped_route_calls_a_guard():
    offenders: list[str] = []
    for method, path, endpoint in _project_scoped_routes():
        if (method, path) in ALLOWLIST:
            continue
        try:
            source = inspect.getsource(endpoint)
        except (OSError, TypeError):  # pragma: no cover - defensive
            offenders.append(f"{method} {path} (source unavailable)")
            continue
        if not any(token in source for token in GUARD_TOKENS):
            offenders.append(f"{method} {path}")

    assert not offenders, (
        "Project-scoped routes missing an access guard. Add a guard call or, if "
        "intentionally public, add the route to ALLOWLIST with a reason:\n  "
        + "\n  ".join(offenders)
    )


def test_allowlist_entries_are_still_project_scoped_routes():
    # Keep the allowlist honest: every allowlisted route must still exist as a
    # project-scoped route, so stale exemptions cannot silently accumulate.
    live = {(m, p) for m, p, _ in _project_scoped_routes()}
    stale = [f"{m} {p}" for (m, p) in ALLOWLIST if (m, p) not in live]
    assert not stale, "Stale ALLOWLIST entries (route no longer present):\n  " + "\n  ".join(
        stale
    )


def test_guard_coverage_finds_project_scoped_routes():
    # Sanity check that the introspection actually sees the project-scoped API,
    # so a future refactor that hides routes does not turn this suite into a
    # silent no-op that gives false confidence.
    assert len(_project_scoped_routes()) > 50
