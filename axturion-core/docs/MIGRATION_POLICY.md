# Migration Discipline

- No model changes without migration file
- Every migration must:
  - Have clear message
  - Be reversible (downgrade implemented)
- Never modify existing migration files
- Always generate new revision
- Run alembic upgrade head locally before commit
- CI must fail if model != schema

