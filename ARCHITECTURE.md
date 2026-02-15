# MATS Architecture

MATS is a workflow-driven recruitment infrastructure platform.

The architecture prioritizes structural correctness, workflow isolation, and governance alignment.

---

## Architectural Goals

- Strict workflow ↔ application isolation
- No cross-workflow data leakage
- Deterministic reporting
- Explicit transition enforcement
- Service-layer integrity validation
- On-premise compatibility

---

## Layered Architecture

### 1. Domain Layer

- Pure SQLAlchemy models
- No framework imports
- Explicit workflow binding (Application.workflow_id)

### 2. Service Layer

All business logic lives here.

Responsibilities:

- Transition validation
- Stage mutation integrity
- Workflow isolation enforcement
- Reporting aggregation
- Automation triggers
- Audit logging

No HTTP parsing.
No FastAPI coupling.

### 3. API Layer

- Request validation (Pydantic)
- Exception mapping
- No business logic

### 4. Reporting Layer

Workflow-scoped reporting:

- Stage distribution
- Stage duration
- Zero-count stage inclusion
- Deterministic time handling

### 5. Automation Layer

Event-driven:

- Stage change triggers
- Rule evaluation
- Activity logging

Runs inside the same DB transaction.

---

## Workflow Integrity Model

Applications are explicitly bound to a workflow.

Transitions are validated per workflow context.

This guarantees:

- Multi-workflow isolation
- Governance-safe deployment
- Predictable runtime behavior

---

## Design Philosophy

MATS prioritizes:

- Clarity over abstraction
- Explicit logic over magic
- Long-term stability over feature velocity
- Structural governance over rapid expansion