# MATS Architecture

MATS is a workflow-driven recruitment infrastructure platform.

The architecture prioritizes structural correctness, workflow isolation, and governance alignment.

---

## Architectural Goals

- Strict workflow ↔ application isolation
- No cross-workflow data leakage
- Organization-scoped data isolation (multi-tenant)
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
- Authorization-aware org scoping (enforced in queries/writes)

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

## Tenancy & Authorization

MATS is organization-scoped. Every business entity is bound to an `organization_id`, and all reads/writes are constrained by that boundary.

Authorization is enforced at the API boundary using exact-match scopes resolved from the user’s organization membership role.

Key properties:

- No cross-organization access: service queries always filter by `organization_id` and explicitly block cross-org operations.
- Endpoint-level RBAC: API routes declare required scopes (e.g. `application:move_stage`, `reporting:read`, `audit:read`, `compliance:export`).

---

## Governance Features

### 4-eyes approvals for stage transitions

Stage transitions can be configured to require a second person’s approval:

- `workflow_transition.requires_approval` enables approval per transition.
- A pending transition is stored in `pending_stage_transition`.
- API semantics: initiating a protected transition returns `202 Accepted` (pending), approving returns `200 OK`; self-approval is forbidden.

### Tamper-evident audit trail (hash chaining)

Audit events are append-only and chained per organization:

- `audit_log` includes `seq`, `prev_hash`, `hash` (and optional `actor_id`).
- Hash input is deterministic/canonicalized; each row’s hash depends on the previous row’s hash.
- Verification endpoint: `GET /audit/verify` checks the chain (default limit 1000, hard cap 10,000). Full-chain verification is reserved for internal callers that pass explicit rows.

### Compliance export bundle

Organization admins/auditors can export a compliance bundle as a ZIP:

- Endpoint: `GET /compliance/export` (requires `compliance:export`).
- Includes:
	- `audit_chain.json`
	- `audit_verification.json`
	- `approvals_snapshot.json`
	- `lifecycle_summary.json`
- Safety cap: exports only the most recent audit entries when the audit log exceeds a configured maximum, while preserving sequence order.

---

## API Surface (Route Groups)

Routes are grouped by feature and mounted in the main app:

- Reporting: `/reporting/*`
- Approvals dashboard: `/approvals/*`
- Audit verification: `/audit/*`
- Compliance export: `/compliance/*`
- Applications: `/applications/*`
- Activity feed/timeline: `/activity/*`
- Candidates: `/candidates/*`
- Jobs: `/jobs/*`
- Workflows: `/workflows/*`, `/workflow-queries/*`, `/workflow-editor/*`

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