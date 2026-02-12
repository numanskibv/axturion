# ATS Platform – Architecture Overview

## 1. Vision

This project is a backend-first, workflow-driven ATS (Applicant Tracking System).

Core principles:

- Workflow configuration over hardcoded behavior
- Service-layer business logic
- Explicit and readable code
- Minimal framework leakage
- Deterministic runtime behavior
- Testable domain logic

The system is designed in layers, not as CRUD endpoints.

---

## 2. High-Level Architecture

The backend is organized into four conceptual layers:

### 2.1 Runtime Workflow Engine

Responsible for:

- Moving applications between stages
- Validating transitions
- Creating audit logs
- Triggering automation events
- Writing timeline activities

Core file:
- `service.py`

Important properties:

- Stage transitions are validated against `WorkflowTransition`
- Invalid transitions raise domain exceptions
- All mutations are atomic (single DB transaction)
- Automation runs within the same transaction

---

### 2.2 Workflow Editor (Configuration Layer)

Responsible for:

- Creating workflow stages
- Removing workflow stages
- Creating transitions
- Removing transitions
- Reading workflow definitions

Core file:
- `workflow_editor_service.py`

Important properties:

- Stage names are unique per workflow (enforced in service layer)
- Integrity rules are enforced in services
- API layer only maps exceptions to HTTP errors

This layer treats workflows as configuration data.

---

### 2.3 Workflow Query Layer

Responsible for:

- Exposing read-only queries
- Determining allowed transitions for an application

Core file:
- `workflow_query_service.py`

Important properties:

- No mutations
- No side effects
- No commit calls

---

### 2.4 Automation Engine

Responsible for:

- Listening to domain events
- Evaluating rules
- Creating activities or performing actions

Core file:
- `automation/service.py`

Important properties:

- Rule-based
- Runs inside the same DB transaction as the triggering mutation
- Currently supports:
  - create_activity
  - send_email (mocked as activity)

---

## 3. Data Model Overview

### Workflow

- id (UUID)
- name

### WorkflowStage

- id (UUID)
- workflow_id (UUID FK)
- name
- order

### WorkflowTransition

- id (UUID)
- workflow_id (UUID FK)
- from_stage (string)
- to_stage (string)

### Application

- id (UUID)
- candidate_id
- job_id
- stage (string)
- status

### Activity

- id (UUID)
- entity_type
- entity_id
- type
- message
- payload (JSON)
- created_at

---

## 4. Important Architectural Decisions

### 4.1 Service-Layer First

All business logic lives in service files.
API routes:

- Parse input
- Call service
- Map exceptions

No business logic in routes.

---

### 4.2 No Repository Layer

We intentionally avoid adding an abstraction layer on top of SQLAlchemy.

Reason:
- Keep code explicit
- Avoid unnecessary abstraction
- Preserve clarity

---

### 4.3 No Migrations (Yet)

Schema is currently managed via:

- `Base.metadata.create_all()`
- Dev-time column sync

Future improvement:
- Alembic migration flow

---

## 5. Known Architectural Limitations

These are explicit trade-offs in the current version.

### 5.1 Applications Are Not Linked to Workflows

`Application` does NOT have a `workflow_id`.

Implication:

- Runtime transition validation does not filter by workflow.
- Transitions are effectively global by stage name.
- Multiple workflows are not safely isolated.

Current system behaves as:

> Single-workflow runtime with multi-workflow configuration support.

---

### 5.2 Transition Isolation

`WorkflowTransition.workflow_id` exists, but:

- Runtime validation does not filter by it.
- Allowed transitions query does not filter by it.

This will require a model change to fix properly.

---

### 5.3 Stage Removal Is Globally Restricted

When removing a stage:

- We must block removal if any `Application.stage` equals that stage name.
- Because applications are not workflow-scoped.

---

## 6. What This System Currently Is

- A deterministic workflow engine
- With configurable transitions
- With event-driven automation
- With append-only activity tracking
- With strong service-layer separation
- Suitable for single-workflow production use

---

## 7. What This System Is Not (Yet)

- Not fully multi-workflow isolated
- Not migration-driven
- Not multi-tenant
- Not permission-aware
- Not versioned workflows
- Not asynchronous job-based

---

## 8. Future Architectural Milestone

To support true multi-workflow isolation:

Minimal required change:

Option A:
- Add `workflow_id` to `Application`

Option B:
- Add `workflow_id` to `Job`
- Derive Application workflow via Job

Runtime validation must then:

- Filter transitions by workflow_id
- Filter allowed transitions by workflow_id

This will be introduced in a future milestone.

---

## 9. Current Stability Status

- Runtime stable
- Editor read stable
- Editor write in progress
- Tests green
- Docker startup deterministic

System maturity: Early-stage but architecturally structured.
