# Engineering Guidelines

This document defines architectural guardrails for MATS development.

---

## Core Rules

1. No business logic in routers.
2. No FastAPI imports in domain models.
3. All workflow mutations must enforce integrity rules.
4. No cross-workflow data leakage.
5. Reporting must remain deterministic.
6. Avoid implicit behavior.
7. No silent data correction.
8. Service layer owns validation.
9. Tests must use in-memory SQLite.
10. No architecture refactors without explicit review.

---

## Mutation Integrity

Workflow mutations must enforce:

- Unique stage names per workflow
- No stage removal if used by:
  - Transitions
  - Applications
- No duplicate transitions
- No self-loop transitions (unless explicitly allowed)

---

## Reporting Constraints

- Always workflow-scoped
- Include zero-count stages
- No hidden filtering
- Deterministic time handling

---

## Architectural Authority

MATS follows a controlled open-core model.

Architectural alignment takes priority over feature additions.
Pull requests may be declined if they conflict with long-term design direction.