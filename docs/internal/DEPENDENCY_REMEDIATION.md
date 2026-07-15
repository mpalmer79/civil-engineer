# Dependency Remediation Record

Internal engineering document recording the coordinated dependency and toolchain remediation performed during the consolidation initiative.

## JavaScript

Baseline npm audit (full tree): 2 critical, 1 high, 3 moderate, all in the test toolchain chain vitest 2.0.5, @vitest/coverage-v8 2.0.5, vite 5, vite-node, esbuild <= 0.24.2, @vitejs/plugin-react 4.3.1. Advisories included the Vitest API server remote code execution exposure, the Vitest UI arbitrary file read and execution exposure, the Vite optimized-deps source map path traversal, the launch-editor NTLMv2 disclosure on Windows, the Vite file-system deny bypass on Windows, and the esbuild development-server request exposure. The production tree (npm audit --omit=dev) was already clean.

Remediation, validated as one coordinated migration:

| Package | Before | After |
| --- | --- | --- |
| vitest | 2.0.5 | 4.1.10 |
| @vitest/coverage-v8 | 2.0.5 | 4.1.10 |
| @vitejs/plugin-react | 4.3.1 | 4.7.0 |
| vite | transitive 5.x | direct 7.3.6 with an override so vitest resolves the same copy |
| eslint | 8.57.0 | 9.39.5 (flat config, direct CLI, next lint removed) |
| typescript | 5.5.3 | 5.9.3 |
| @types/node | 20.x | 22.x |

Notes:

- Vitest 4 bundles vite 8 (rolldown) by default, which does not apply the JSX transform from @vitejs/plugin-react 4.x; test files failed to parse. The `"vitest": { "vite": "$vite" }` override pins vitest to the top-level vite 7.3.6, which plugin-react 4.7.0 supports. Moving to plugin-react 6 and vite 8 is deliberate future work, not required for remediation.
- The lockfile was regenerated to apply the override cleanly.
- Coverage ratchet floors in vitest.config.ts were re-baselined because the vitest 4 v8 remapping counts statements and branches differently for the identical suite and sources (statements 57 to 51, branches 62 to 42, functions 50 to 47, lines 57 to 52 at the same real coverage). Floors remain ratchets: raise only.
- ESLint migrated from `.eslintrc.json` plus deprecated `next lint` to `eslint.config.mjs` (flat) with FlatCompat over next/core-web-vitals, ignoring build output and generated artifacts. Zero errors, zero warnings.

Result: npm audit reports 0 vulnerabilities (full tree and production).

## Python

Baseline pip-audit on backend/requirements.txt: 16 known vulnerabilities in 3 packages (python-multipart 0.0.9 with 7 advisories, starlette 0.37.2 via fastapi 0.111.0 with 8 advisories, pytest 8.2.2 with 1 advisory).

Remediation:

| Package | Before | After |
| --- | --- | --- |
| fastapi | 0.111.0 | 0.139.0 |
| starlette | 0.37.2 (transitive) | 1.3.1 (pinned direct) |
| python-multipart | 0.0.9 | 0.0.32 |
| pytest | 8.2.2 | 9.1.1 |
| pydantic | 2.7.4 | 2.13.4 |
| pydantic-settings | 2.3.4 | 2.14.2 |
| SQLAlchemy | 2.0.31 | 2.0.51 |
| alembic | 1.13.2 | 1.18.5 |
| uvicorn | 0.30.1 | 0.51.0 |
| httpx | 0.27.0 | 0.28.1 |
| psycopg2-binary | 2.9.9 | 2.9.12 |

Deliberately held back:

- ezdxf 1.4.4 and pypdf 6.14.2 stay pinned. They are the parser versions the deterministic DXF proof and the PDF indexing behavior were validated against, they have no open audit findings, and upgrading them requires regenerating and re-reviewing the committed proof artifacts in the same change.
- boto3 and stripe stay pinned (no audit findings; upgrading is routine maintenance, not remediation).

Migration fallout fixed: starlette 1.x wraps included routers lazily, so tests/test_guard_coverage.py now walks the nested router structure instead of assuming a flat route list. The generated OpenAPI contract was regenerated; the diff is schema-dialect representation only (binary format expressed as contentMediaType, explicit additionalProperties), with no path, method, or field changes.

Result: pip-audit reports no known vulnerabilities. Full backend suite passes (905 passed, 1 skipped) and the DXF proof artifacts are byte-identical.

## Policy

- CI gates: production npm audit at high (existing), full-tree npm audit at high (added), pip-audit on backend requirements (added).
- Exceptions require a documented owner and expiry in this file. There are currently no exceptions.
- The test toolchain (vitest, vite, plugin-react) upgrades together as one unit; partial bumps of that chain are the failure mode that produced the baseline exposure.
