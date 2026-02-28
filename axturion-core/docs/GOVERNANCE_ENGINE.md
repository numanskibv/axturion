# AXTURION Governance Engine

The Governance Engine is a first-class architectural layer in AXTURION.

It ensures that:

- Organizational policies are enforced
- Critical changes are auditable
- SLA thresholds are configurable
- Retention policies are previewable
- Sensitive operations require 4-eyes approval
- All governance actions are traceable

---

## Governance System Overview

```mermaid
graph TD

    User[Admin / HR / Auditor]

    subgraph Command["AXTURION Command"]
        PolicyUI[Policy UI]
        UXRollbackUI[UX Rollback UI]
        DashboardUI[Dashboard (SLA View)]
    end

    subgraph Core["AXTURION Core"]
        PolicyConfig[PolicyConfig Model]
        Retention[Retention Rules]
        SLA[SLA Policy]
        FourEyes[4-Eyes Rollback]
        RBAC[Scope-based Authorization]
        Audit[Audit Chain]
    end

    User --> PolicyUI
    User --> UXRollbackUI
    User --> DashboardUI

    PolicyUI --> PolicyConfig
    DashboardUI --> SLA
    UXRollbackUI --> FourEyes

    PolicyConfig --> SLA
    PolicyConfig --> Retention
    PolicyConfig --> FourEyes

    SLA --> Audit
    Retention --> Audit
    FourEyes --> Audit
    PolicyConfig --> Audit
```

---

## Core Governance Components

### 1. PolicyConfig (Org-Scoped)

Defines per-organization rules:

- stage_aging_sla_days
- retention policies
- 4-eyes requirements
- other future governance flags

Properties:
- Org-scoped
- Strict schema
- Audited on update
- Auto-defaulted if missing

All policy changes trigger:

```
action = "policy_updated"
entity_type = "policy"
```

---

### 2. SLA Governance

SLA is not hardcoded.

- Defined per organization
- Used by dashboard
- Affects breach highlighting
- Auditable via policy change

SLA does not mutate lifecycle state.
It only interprets it.

---

### 3. Retention Rules (Preview-Only)

Retention system:

- Calculates eligible deletions
- Does not auto-delete
- Is org-scoped
- Previewable via governance endpoint

Designed to support future controlled deletion workflows.

---

### 4. 4-Eyes UX Rollback

When enabled:

1. First rollback request → creates pending approval
2. Audit event: `ux_rollback_pending`
3. Second user approves
4. Audit event: `ux_rollback_approved`
5. Rollback applied
6. Audit event: `ux_config_rollback`

Prevents unilateral UX manipulation.

---

### 5. Scope-Based Authorization (RBAC)

All governance endpoints require explicit scopes:

Examples:

- WORKFLOW_WRITE
- UX_WRITE
- REPORTING_READ

Platform Admin → ALL scopes  
Other roles → explicit scope sets

Authorization decisions are deterministic and server-enforced.

---

### 6. Audit Chain Integrity

Audit log characteristics:

- Append-only
- Hash chained
- Sequence validated
- Supports verification endpoint
- Used for compliance export

All governance decisions are recorded.

---

## Governance Data Flow

Policy Change →
    Validate Schema →
    Persist →
    Append Audit →
    Affect Runtime Interpretation (SLA / Retention / 4-eyes)

No silent rule changes.

---

## Governance Design Principles

1. Policies are configuration, not code.
2. Governance is org-scoped.
3. Critical operations require dual control.
4. All governance mutations are auditable.
5. UI never enforces governance — Core does.
6. Reporting reflects policy, not vice versa.

---

## Enterprise Positioning

AXTURION Governance enables:

- Compliance-grade change tracking
- Controlled UX customization
- Risk-aware lifecycle management
- Enterprise audit traceability
- Multi-tenant isolation

Governance is not a feature.  
It is the control layer of the platform.