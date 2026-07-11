"""Command center domain package.

Holds the deterministic builder functions extracted from
command_center_service (ADR 0005): attention items, metrics, readiness
checks, and timeline events. Each builder is a pure function over the
gathered project data dict and returns review-support records only."""
