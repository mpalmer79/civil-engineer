# ADR 0008: Dependency security policy

Status: accepted

## Context

A full npm audit found two critical and one high vulnerability in the frontend test toolchain (vitest 2 chain), and pip-audit found sixteen known vulnerabilities across python-multipart, starlette, and pytest. The production npm tree was clean, but development tooling is part of the supply chain: the vulnerable components run on developer machines and CI runners with repository write access.

## Decision

1. CI gates dependencies on every push: npm audit --omit=dev at the high level, npm audit (full tree) at the high level, and pip-audit against backend/requirements.txt with no findings allowed.
2. Moderate or unavoidable findings require a documented exception in docs/internal/DEPENDENCY_REMEDIATION.md with an owner and an expiry date. There are no standing silent exceptions.
3. The frontend test toolchain (vitest, vite, plugin-react, coverage provider) is upgraded as one coordinated unit, never piecemeal, because version skew across that chain caused the original exposure.
4. Parser dependencies that back deterministic, committed artifacts (ezdxf, pypdf) are pinned and only upgraded together with regeneration and review of the proof artifacts in the same change.
5. Backend dependencies are pinned exactly in requirements.txt so pip-audit results are reproducible.
6. `npm audit fix --force` is never used; remediation upgrades are chosen and validated deliberately.

## Consequences

- New advisories fail CI until remediated or documented; the failure is visible and actionable rather than accumulating silently.
- Coordinated toolchain upgrades are larger but validated once, with test-suite and coverage behavior checked in the same change.
