# ATS Governance Blueprint (Extended Edition)

## MATS → Governance-First ATS Core

Version: 0.3 (Extended) Status: Stabilized & Documented Core Audience:
Architecture, Governance, Compliance, Security, Defense Stakeholders

------------------------------------------------------------------------

# 0. Executive Overview

This document describes the governance architecture of the ATS core
platform.

The system is engineered around:

-   Organization isolation as a hard boundary
-   Database-backed identity and membership
-   Scope-based Role Based Access Control (RBAC)
-   Immutable hash-chained audit logging
-   Optional 4-eyes workflow approvals
-   Bounded read paths (no unlimited queries)
-   Compliance export packaging
-   Deterministic startup validation

The system is designed to evolve toward Defense-grade operational
environments.

------------------------------------------------------------------------

# 1. Architectural Overview

## 1.1 Layered Structure

    domain/        → SQLAlchemy models (pure data structures)
    services/      → business rules, invariants, governance enforcement
    api/routes/    → FastAPI endpoints + scope enforcement
    core/          → config, DB init, logging, request context

## 1.2 Request Execution Flow

1.  HTTP Request
2.  Headers: X-Org-Id, X-User-Id
3.  RequestContext resolution
4.  Role → Scope mapping
5.  Scope enforcement (require_scope)
6.  Service-layer execution (org-filtered)
7.  Audit append (hash chained)
8.  Activity append
9.  Structured log emission (correlation_id)

------------------------------------------------------------------------

# 2. Identity & Role Model

## 2.1 Role → Scope Mapping

### recruiter

-   application:read
-   application:create
-   application:move_stage
-   application:close
-   workflow:read
-   reporting:read
-   job:read
-   candidate:create
-   candidate:read
-   candidate:update

### hr_admin

All recruiter scopes plus:

-   workflow:write
-   compliance:export
-   job:create
-   job:update
-   job:close

### auditor

-   audit:read
-   reporting:read
-   compliance:export
-   application:read
-   job:read
-   candidate:read

### stage_operator

-   application:read
-   application:move_stage

### platform_admin

-   ALL (all defined scopes)

------------------------------------------------------------------------

## 2.2 Scope Enforcement

All mutating endpoints use:

    Depends(require_scope(SCOPE_NAME))

Unauthorized access: - Returns HTTP 403 - Is logged with
correlation_id - Never reaches service layer

------------------------------------------------------------------------

# 3. API Surface Overview

## Core Endpoints

### Applications

POST /applications\
POST /applications/{id}/move-stage\
POST /applications/{id}/close

### Jobs

POST /jobs\
PATCH /jobs/{id}\
POST /jobs/{id}/close\
GET /jobs\
GET /jobs/{id}

### Candidates

POST /candidates\
PATCH /candidates/{id}\
GET /candidates\
GET /candidates/{id}

### Workflows

GET /workflows/{id}\
GET /workflow-editor/{id}/definition\
POST /workflow-editor/{id}/stages\
POST /workflow-editor/{id}/transitions\
DELETE /workflow-editor/{id}/transitions

### Reporting & Oversight

GET /reporting/workflows/{id}/stage-summary\
GET /reporting/workflows/{id}/stage-duration\
GET /reporting/approvals/summary

### Approvals

GET /approvals/pending\
GET /approvals/pending/{application_id}

### Audit

GET /audit/verify

### Compliance

GET /compliance/export

------------------------------------------------------------------------

# 4. Lifecycle Governance Controls

## 4.1 Application Lifecycle

create → move_stage → close

Controls: - Org validation - Workflow transition validation - Optional
4-eyes approval - Audit append - Activity append

## 4.2 Job Lifecycle

create → update → close

All changes audited.

## 4.3 Candidate Lifecycle

create → update → read → list (paginated)

All mutations audited.

------------------------------------------------------------------------

# 5. Approval System

If workflow transition requires approval:

1.  First call creates PendingStageTransition → 202
2.  Second user approves → 200
3.  Same user attempting approval → 403

All approvals: - Org-scoped - Reporting-scoped - Paginated + capped

------------------------------------------------------------------------

# 6. Audit & Integrity

## 6.1 Immutable Audit Log

Fields:

-   seq
-   prev_hash
-   hash
-   actor_id
-   organization_id
-   entity_type
-   entity_id
-   action
-   payload
-   created_at

Hash algorithm:

    SHA256(prev_hash + canonical_payload)

Concurrency control:

-   Organization-level locking
-   Last-row locking
-   Sequential enforcement

------------------------------------------------------------------------

## 6.2 Audit Verification

Endpoint:

    GET /audit/verify

Default verification limit: 1000\
Hard cap: 10,000

Unlimited verification only allowed internally (compliance export).

------------------------------------------------------------------------

# 7. Compliance Export Bundle

Endpoint:

    GET /compliance/export

Requires:

    compliance:export

ZIP includes:

-   audit_chain.json
-   audit_verification.json
-   approvals_snapshot.json
-   lifecycle_summary.json

Characteristics:

-   Org-scoped
-   Memory-safe
-   MAX_AUDIT_ENTRIES = 200,000
-   Compact JSON
-   Truncation metadata included

------------------------------------------------------------------------

# 8. Operational Controls

## 8.1 Deterministic Startup

Startup verifies:

-   Database connectivity
-   Alembic head migration applied
-   Configuration validation

## 8.2 Logging Discipline

-   Structured JSON logs
-   Correlation ID per request
-   Sensitive field redaction
-   No DEBUG logging in production

------------------------------------------------------------------------

# 9. Defense Readiness Path

Future enhancements toward Defense deployment:

-   OIDC / SSO integration
-   Data retention policies
-   Advanced role matrices
-   Multi-level approval matrices
-   Evidence retention vault integration
-   SIEM export hooks
-   Field-level encryption
-   Immutable object storage for audit exports

------------------------------------------------------------------------

Status: Extended Blueprint v0.3
