# Engineering Guidelines

These rules preserve architectural integrity.

---

## Core Rules

1. No business logic in routers.
2. No FastAPI imports in domain models.
3. All workflow mutations enforce integrity rules.
4. No cross-workflow data leakage.
5. No cross-organization data leakage (org boundary is mandatory everywhere).
5. Reporting must remain deterministic.
6. No implicit behavior.
7. Service layer owns validation.
8. Tests use in-memory SQLite.
9. Architecture refactors require explicit approval.

---

## Tenancy & Authorization (RBAC)

- Every query and mutation must be organization-scoped (`organization_id`).
- API endpoints enforce authorization using exact-match scopes (`require_scope`).
- Never rely on client-provided identifiers alone: always re-check org ownership in the service layer.

---

## Audit & Compliance

- Audit logs are append-only and tamper-evident via per-organization hash chaining (`seq`, `prev_hash`, `hash`).
- All audit writes must go through the centralized append helper (no direct `AuditLog(...)` inserts in feature services).
- Audit verification is bounded by default (limit=1000, hard cap=10,000). Full-chain verification is reserved for internal callers that provide explicit rows.
- Compliance export (`/compliance/export`) is org-scoped and produces a ZIP with fixed filenames:
  - `audit_chain.json`
  - `audit_verification.json`
  - `approvals_snapshot.json`
  - `lifecycle_summary.json`

---

## API Conventions

- Listings should support safe pagination (`limit`/`offset`) with sensible defaults and hard caps.
- Ordering must be explicit (e.g. `created_at desc`) to avoid nondeterminism.
- Errors should be mapped consistently at the API layer (service raises domain errors; router maps to HTTP).

---

## Tests & Local Runs

- System tests use SQLite in-memory and override app startup side effects.
- Run tests with backend module resolution:
  - `PYTHONPATH=backend ./.venv/bin/python -m pytest -q`

---

## Mutation Integrity Rules

- Unique stage names per workflow
- No stage removal if used by:
  - Transitions
  - Applications
- No duplicate transitions
- No self-loop transitions
- Stage order normalization after deletion

---

## Reporting Constraints

- Always workflow-scoped
- Include zero-count stages
- Deterministic time handling
- No silent filtering