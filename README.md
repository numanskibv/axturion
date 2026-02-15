# MATS
Modular Application Tracking System

MATS is a workflow-driven recruitment infrastructure platform designed for governance-oriented organizations.

It is built for environments where:

- On-premise deployment is required
- Vendor lock-in must be avoided
- Workflow control and auditability are essential
- Long-term architectural stability is prioritized over rapid feature expansion

MATS is not a feature-first ATS.
It is an infrastructure-first recruitment foundation.

---

## Core Principles

- Workflow-driven process control
- Strict workflow ↔ application isolation
- Governance-safe mutations
- Deterministic reporting
- API-first design
- Modular extensibility

---

## Architecture Overview

MATS follows a layered architecture:

- Domain models (pure SQLAlchemy)
- Service layer (business logic & integrity rules)
- API layer (FastAPI, request/response mapping)
- Reporting layer (governance insights)
- Automation layer (event-driven rules)

For full architectural details, see:
→ `ARCHITECTURE.md`

---

## Running Locally

## Start the stack ##
bash:
docker compose up -d --build

## Run test ##
bash:
docker exec -it deploy-backend-1 sh -lc 'PYTHONPATH=/app pytest -q /tests'

## Swagger UI ##
http://localhost:8000/docs

## Documentation ##
	•	Architecture → ARCHITECTURE.md
	•	Engineering Guardrails → ENGINEERING_GUIDELINES.md
	•	Roadmap → ROADMAP.md
	•	Changelog → CHANGELOG.md
	•	Contribution Guidelines → CONTRIBUTING.md

⸻

## License ##

Open Core model.
Enterprise governance layer may be provided separately.

Code:

 ---

# ✅ 2️⃣ ARCHITECTURE.md (Uitgebreid, volwassen)

```markdown
# MATS Architecture

MATS is built as a workflow-driven recruitment infrastructure platform.

The architecture prioritizes structural correctness, governance alignment, and long-term maintainability.

---

## Architectural Goals

- Strict workflow isolation
- No cross-workflow leakage
- Deterministic reporting
- Service-layer integrity enforcement
- Clear separation of concerns
- On-premise compatibility

---

## Layered Design

### 1. Domain Layer

- Pure SQLAlchemy models
- No FastAPI imports
- No framework coupling
- Explicit workflow_id binding

### 2. Service Layer

All business logic lives here.

Responsibilities:
- Workflow integrity validation
- Transition enforcement
- Stage mutation safety
- Reporting aggregation
- Automation triggers

No HTTP logic.
No request parsing.

### 3. API Layer

- FastAPI routers
- Schema validation via Pydantic
- Error mapping only
- No business rules

### 4. Reporting Layer

Workflow-scoped reporting:
- Stage distribution
- Stage duration
- Deterministic calculations
- Zero-count inclusion

### 5. Automation Layer

Event-driven:
- Stage change triggers
- Activity logging
- Rule-based execution

---

## Workflow Integrity Model

Applications are explicitly bound to a workflow:

Application.workflow_id

Transitions are validated per workflow context.

This enables:

- Multi-workflow deployments
- Future multi-organization support
- Governance-safe isolation

---

## Design Philosophy

MATS prioritizes:

- Structural clarity over abstraction cleverness
- Explicit logic over magic
- Long-term maintainability over speed
- Governance alignment over feature velocity
