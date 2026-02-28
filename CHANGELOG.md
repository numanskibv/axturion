# Changelog

All notable changes to MATS (Modular Application Tracking System) will be documented in this file.

The format is inspired by Keep a Changelog.
This project adheres to semantic versioning principles.

# Release Philosophy

MATS follows an incremental, architecture-first release strategy.

Each minor version (0.x.0) represents a meaningful architectural step forward — not just feature additions.

We prioritize:

- Structural correctness over feature volume
- Governance and workflow integrity over speed
- Backward compatibility within minor lines
- Explicit documentation of architectural shifts

Versioning principle:

- 0.x.0 → Architectural milestone
- 0.x.y → Stability or internal improvements
- 1.0.0 → Production-ready governance baseline

MATS is built as a long-term modernization platform, not a feature-driven startup MVP.

---

## [Unreleased]

### Planned

- Workflow editor mutation refinements
- Governance configuration layer expansion
- Enterprise-layer packaging strategy
- Versioned workflow configuration groundwork

## [0.6.0] - 2026-02-28

### Added

- Organization-scoped Candidate endpoints (CRUD-lite) with scope-based RBAC
- Optional 4-eyes approval for stage transitions (`requires_approval` + pending transitions)
- Approvals dashboard endpoints (`/approvals/*`) and approvals summary reporting (`/reporting/approvals/summary`)
- Tamper-evident audit hash chaining (`seq`, `prev_hash`, `hash`) and verification endpoint (`/audit/verify`)
- Compliance export bundle endpoint (`/compliance/export`) producing an org-scoped ZIP (audit + approvals + lifecycle)

### Improved

- Activity listing endpoints now support safe pagination (`limit`/`offset`, default 50, hard cap 500)
- Compliance export memory usage reduced (single audit row materialization, compact JSON in ZIP, truncation safety cap)
- Audit verification hardened: API-style calls cannot request full-chain verification via `limit=None`
- Approvals summary optimized to use DB aggregation (avoids full materialization)
- Documentation refreshed (README/docs), removed obsolete roadmap/contributing references

## Why is MATS still < 1.0?

MATS is currently in the 0.x phase because we are deliberately stabilizing the architectural foundation before declaring production maturity.

This phase focuses on:

- Workflow integrity correctness
- Multi-workflow isolation
- Governance-safe mutations
- Deterministic reporting
- API stability

The transition to 1.0.0 will mark:

- A fully stable workflow engine
- Formalized migration strategy
- Governance-layer foundation
- Enterprise deployment readiness

Until then, 0.x releases represent controlled architectural evolution — not instability.

## [0.5.0] - 2026-02-15

### Added
- Alembic migrations integrated
- Docker entrypoint with automated migration & seed
- Health endpoints (/live, /ready, /health)
- Structured startup flow

### Improved
- Stage duration reporting stabilization
- Deterministic reporting tests
- Logging configuration
- Infrastructure maturity

### Fixed
- Closed applications cannot change stage
- Flaky datetime-based tests
- Duplicate Alembic execution

## [v0.4.0] – 2026-02-14

### Focus
Workflow integrity stabilization and governance-aligned reporting foundation.

This release marks the transition from technical prototype to stable recruitment infrastructure core.

---

### Added

- Stage distribution reporting endpoint (workflow-scoped)
- Stage duration reporting endpoint (deterministic calculation)
- Deterministic time handling in reporting service (test-safe)
- Complete OpenAPI documentation coverage across API
- Strict workflow ↔ application isolation enforcement

---

### Improved

- Workflow-scoped transition validation
- Stage removal integrity checks
- Zero-count stages included in reporting summaries
- Test stability (no time-based flakiness)
- Consistent error mapping in API layer

---

### Integrity Guarantees

- No cross-workflow data leakage
- Transitions enforced per workflow
- Reporting strictly filtered by workflow_id
- Applications bound to workflow context

---

### Test Status

- 18+ service-level tests passing
- SQLite in-memory test environment stable
- Deterministic reporting calculations

---

## [v0.3.0] – 2026-02-12

### Focus
Workflow engine hardening and architectural integrity.

This release establishes strict workflow scoping across the platform and removes cross-workflow ambiguity.

---

### Added

- `workflow_id` added to Application model
- Workflow-scoped transition validation in runtime stage changes
- Workflow-aware allowed transitions query
- Workflow-scoped stage removal integrity rules
- Service-level tests for cross-workflow isolation

---

### Improved

- Stage transition validation now enforces:
  - from_stage/to_stage must belong to the same workflow
  - No cross-workflow transition leakage
- Stage deletion blocked if:
  - Used in transitions (within same workflow)
  - Used by active Applications (within same workflow)
- Ordering of workflow stages normalized after deletion

---

### Architectural Impact

This release closes a critical design gap:

- Applications are now explicitly bound to a workflow
- Transitions are validated per workflow context
- Reporting and stage summaries are workflow-isolated

This establishes the foundation for:
- Multi-tenant support
- Governance-safe deployments
- Per-department configuration models

---

### Test Status

- Workflow isolation tests added
- Stage mutation integrity tests added
- All tests passing in containerized environment