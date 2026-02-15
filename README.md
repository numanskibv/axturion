# MATS
Modular Application Tracking System

MATS is a workflow-driven recruitment infrastructure platform.

It is designed for governance-oriented organizations that require:

- On-premise deployment
- Sovereign data control
- No vendor lock-in
- Strict workflow integrity
- Deterministic reporting
- Long-term architectural stability

MATS is not a feature-first ATS.
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

MATS follows a layered backend-first architecture:

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

docker exec -it deploy-backend-1 sh -lc 'PYTHONPATH=/app pytest -q /tests'

Swagger UI:

http://localhost:8000/docs

---

## Documentation

- Architecture → ARCHITECTURE.md
- Engineering Guardrails → ENGINEERING_GUIDELINES.md
- Governance Model → GOVERNANCE.md
- Roadmap → ROADMAP.md
- Changelog → CHANGELOG.md
- Contribution Guidelines → CONTRIBUTING.md
- Security Policy → SECURITY.md
- Enterprise Layer → ENTERPRISE.md

---

## License

MATS Core is licensed under Apache 2.0.

Enterprise governance capabilities may be provided separately.