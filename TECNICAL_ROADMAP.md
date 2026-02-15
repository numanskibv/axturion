# MATS Technical Roadmap

This document outlines the technical evolution path of MATS from v0.4.0 toward v1.0.

MATS is positioned as governance-grade recruitment infrastructure,
not as a feature-driven ATS product.

The roadmap prioritizes architectural integrity, risk reduction,
and long-term operational stability.

---

# Current State (v0.4.0)

Implemented:

- Workflow engine (workflow-scoped transitions)
- Stage transition validation
- Audit logging
- Activity timeline
- Reporting (stage summary, duration)
- Workflow editor mutations (add/remove stage & transition)
- OpenAPI documentation
- Full test coverage (service-level)

The foundation is stable.

---

# Phase 1 – Domain Stabilisation (v0.5)

Goal: Harden the workflow engine and lifecycle model.

## 1. Application Lifecycle Improvements
- Add `stage_entered_at`
- Add `closed_at`
- Separate `status` from `stage`
- Optional `rejected_reason`

## 2. Workflow Engine Hardening
- Strict state machine enforcement
- Prevent orphan transitions
- Soft-delete stages
- Improve transition validation rules

## 3. Reporting Expansion
- Time-in-stage reporting
- Average stage duration
- Funnel conversion ratios
- Workflow health metrics

Priority: High  
Reason: Core product integrity.

---

# Phase 2 – Governance Layer (v0.6)

Goal: Governance-grade infrastructure readiness.

## 1. Role-Based Access Control (RBAC)
- Recruiter
- Manager
- Auditor
- Administrator

## 2. Advanced Audit Capabilities
- Immutable audit events
- Actor tracking (who performed change)
- Metadata capture
- Exportable audit trails

## 3. Data Segregation Preparation
- `tenant_id` (optional)
- `department_id` alternative model

Priority: High for regulated environments.

---

# Phase 3 – Extensibility Layer (v0.7)

Goal: Modular architecture (Open-Core readiness).

## 1. Domain Event Abstraction
- Formal event bus
- Plugin hook registration

## 2. Module Interfaces
- Custom transition guards
- Custom reporting modules
- Custom validation rules

## 3. Config-Driven Features
- Workflow templates
- Conditional transitions

Priority: Strategic.

---

# Phase 4 – Enterprise Readiness (v0.8)

Goal: Operational maturity for on-premise deployments.

## 1. API Versioning
## 2. Health & Metrics Endpoints
## 3. Configurable Logging
## 4. Migration Strategy (Alembic)
## 5. Backup & Restore Documentation

Priority: Required for enterprise contracts.

---

# Phase 5 – Productisation (v1.0)

Goal: Stable governance infrastructure release.

## 1. Frontend Layer
## 2. Deployment Packaging
## 3. Enterprise Governance Add-ons
## 4. Multi-tenant Configuration Model
## 5. Long-term Maintenance Policy

Priority: After architectural stabilization.

---

# Strategic Principle

MATS evolves infrastructure first.

Features are secondary.
Governance, stability, and extensibility are primary.

Modernisation must reduce risk, not introduce it.