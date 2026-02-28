# Governance Model

MATS follows an architect-led governance model.

The project is open source (Apache 2.0), but architectural direction and roadmap control are centrally managed to preserve long-term stability.

---

## Governance Philosophy

- Architecture-first
- Integrity over speed
- Deterministic behavior
- Explicit change control

---

## Runtime Governance Controls

Beyond repository/process governance, MATS includes runtime controls designed for governance-aligned operation in multi-tenant environments:

- Organization isolation: all reads/writes are scoped by `organization_id` and cross-org access is explicitly blocked.
- Scope-based RBAC: API endpoints require exact-match scopes resolved from organization membership roles.
- Deterministic reporting: reporting endpoints are scope-protected and designed to be deterministic.
- 4-eyes approvals (optional): specific stage transitions can require approval by a second user; self-approval is forbidden.
- Tamper-evident audit trail: audit logs are append-only and hash-chained per organization (`seq`, `prev_hash`, `hash`).
- Audit verification: `/audit/verify` verifies the chain with a default limit of 1000 and a hard cap of 10,000; full-chain verification is reserved for internal callers that provide explicit rows.
- Compliance export: `/compliance/export` (scope `compliance:export`) produces an org-scoped ZIP bundle for audit/approval/lifecycle evidence.

---

## Maintainer Model

MATS operates under a Benevolent Architect model:

- Core architectural decisions are centralized.
- Pull Requests are reviewed for structural alignment.
- Breaking changes require design discussion.

---

## Contribution Policy

Accepted:

- Bug fixes
- Documentation improvements
- Scoped enhancements aligned with roadmap

Not accepted:

- Architectural rewrites
- Framework replacement proposals
- Unreviewed breaking changes

Engineering conventions and integrity rules are documented in ENGINEERING_GUIDELINES.md.

---

## Roadmap Authority

Roadmap decisions align with:

- Governance deployment needs
- On-premise operational models
- Long-term platform viability

Community input is welcome.
Strategic control remains centralized.