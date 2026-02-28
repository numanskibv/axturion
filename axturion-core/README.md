# AXTURION
Modular Application Tracking System

AXTURION is a workflow-driven recruitment infrastructure platform.

It is designed for governance-oriented organizations that require:

- On-premise deployment
- Sovereign data control
- No vendor lock-in
- Strict workflow integrity
- Deterministic reporting
- Long-term architectural stability

AXTURION is not a feature-first ATS.
It is an infrastructure-first recruitment foundation.

---

## Core Characteristics

- Workflow-scoped application isolation
- Explicit transition validation
- Governance-safe workflow mutations
- Deterministic reporting engine
- Event-driven automation
- Service-layer enforced business rules
- Open-core architecture

---

## Architecture

AXTURION follows a layered backend-first architecture:

- Domain models (SQLAlchemy)
- Service layer (business logic and integrity)
- API layer (FastAPI + Pydantic)
- Reporting layer
- Automation engine

For full architectural details:
→ ARCHITECTURE.md

---

## Running Locally

Start stack:

docker compose up -d --build

Run tests:

Local (venv):

PYTHONPATH=backend ./.venv/bin/python -m pytest -q

Container (example):

docker exec -it deploy-backend-1 sh -lc 'PYTHONPATH=/app pytest -q /tests'

Swagger UI:

http://localhost:8000/docs

---

## Authorization & Tenancy

AXTURION is organization-scoped. API requests are authorized via organization membership roles mapped to exact-match scopes.

System tests and local calls typically pass:

- X-Org-Id: organization UUID
- X-User-Id: user UUID

Selected governance endpoints:

- GET /audit/verify (scope: audit:read)
- GET /compliance/export (scope: compliance:export)
- GET /approvals/pending (scope: reporting:read)
- GET /reporting/approvals/summary (scope: reporting:read)

---

## Documentation

- Architecture → ARCHITECTURE.md
- Engineering Guardrails → ENGINEERING_GUIDELINES.md
- Governance Model → GOVERNANCE.md
- Governance Blueprint → docs/GOVERNANCE_BLUEPRINT.md
- Technical Roadmap → TECNICAL_ROADMAP.md
- Changelog → CHANGELOG.md
- Security Policy → SECURITY.md
- Enterprise Layer → docs/ENTERPRICE.md

---

## License

AXTURION Core is licensed under Apache 2.0.

Enterprise governance capabilities may be provided separately.