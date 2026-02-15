# Engineering Guidelines

These rules preserve architectural integrity.

---

## Core Rules

1. No business logic in routers.
2. No FastAPI imports in domain models.
3. All workflow mutations enforce integrity rules.
4. No cross-workflow data leakage.
5. Reporting must remain deterministic.
6. No implicit behavior.
7. Service layer owns validation.
8. Tests use in-memory SQLite.
9. Architecture refactors require explicit approval.

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