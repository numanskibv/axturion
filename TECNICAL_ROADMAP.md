MATS Technical Roadmap

This document outlines the technical evolution path of MATS from v0.4.0 toward v1.0.

MATS is positioned as governance-grade recruitment infrastructure,
not as a feature-driven ATS product.

The roadmap prioritizes architectural integrity, risk reduction,
and long-term operational stability.

⸻

Current State (v0.4.0)

Implemented:
	•	Workflow engine (workflow-scoped transitions)
	•	Stage transition validation
	•	Audit logging
	•	Activity timeline
	•	Reporting (stage summary, duration)
	•	Workflow editor mutations (add/remove stage & transition)
	•	OpenAPI documentation
	•	Health endpoints (live, ready, health)
	•	Alembic migration framework
	•	Deterministic test coverage (service-level + system-level)

The architectural foundation is stable and migration-controlled.

⸻

Phase 1 – Domain Stabilisation (v0.5)

Goal: Harden the workflow engine and lifecycle model.

1. Application Lifecycle Improvements
	•	Add stage_entered_at
	•	Add closed_at
	•	Separate status from stage
	•	Optional rejected_reason
	•	Prevent stage changes on closed applications

2. Workflow Engine Hardening
	•	Strict state machine enforcement
	•	Prevent orphan transitions
	•	Transition integrity validation
	•	Workflow-scoped isolation guarantees
	•	Immutable audit enforcement per transition

3. Reporting Expansion
	•	Time-in-stage reporting
	•	Deterministic stage duration calculation
	•	Inclusion of zero-count stages
	•	Average stage duration
	•	Funnel conversion ratios (foundational)
	•	Workflow health metrics (basic)

4. Infrastructure Stabilisation
	•	Remove Base.metadata.create_all
	•	Full Alembic-controlled schema lifecycle
	•	Deterministic startup behaviour
	•	Health & readiness validation against migrations

Priority: High
Reason: Core infrastructure integrity.

⸻

Phase 2 – Governance Hardening (v0.6)

Goal: Governance-grade infrastructure readiness.

This phase strengthens structural guarantees rather than adding features.

⸻

1. Workflow Engine Integrity Hardening

1.1 Immutable Audit Enforcement
	•	Every stage transition must generate an audit record
	•	No silent lifecycle mutations
	•	Add consistency tests for audit completeness

1.2 Transition Integrity Safeguards
	•	Validate transitions reference existing stages
	•	Prevent structural inconsistencies
	•	Add validation tests for workflow integrity

1.3 Workflow Freeze Mode
	•	Introduce workflow “locked” state
	•	Prevent structural edits on locked workflows
	•	Enforce freeze checks in workflow editor services
	•	Add tests for locked workflow protection

⸻

2. Reporting Governance Enhancements

2.1 Application Lifecycle Summary
	•	Reporting endpoint for lifecycle states:
	•	Active
	•	Closed
	•	Rejected
	•	Hired
	•	Workflow-scoped aggregation
	•	Deterministic structure

2.2 Workflow Snapshot Reporting
	•	Endpoint exposing workflow definition snapshot
	•	Includes:
	•	Ordered stages
	•	Valid transitions
	•	Structural metadata
	•	Designed for audit & governance validation

2.3 UTC Standardisation
	•	All timestamps strictly timezone-aware (UTC)
	•	Eliminate naive datetime usage
	•	Add regression tests

⸻

3. Infrastructure Maturity – Level 2

3.1 Structured Configuration Module
	•	Typed configuration layer
	•	Environment validation at startup
	•	Fail-fast behaviour on misconfiguration

3.2 Strict Startup Guarantees
	•	Startup fails if:
	•	Database unreachable
	•	Migrations out-of-date
	•	Required environment variables missing

3.3 Strengthened Readiness Probe
	•	/ready returns failure if:
	•	Database unreachable
	•	Migrations not applied

⸻

4. Governance Preparation Layer

4.1 Role Architecture Placeholder
	•	Introduce basic role model (stub only)
	•	Prepare foundation for RBAC
	•	No full auth implementation yet

4.2 Multi-Workflow Isolation Tests
	•	Add system-level tests ensuring:
	•	No cross-workflow leakage
	•	Reporting remains strictly scoped

Priority: Very High for regulated environments.

⸻

Phase 3 – Extensibility Layer (v0.7)

Goal: Modular architecture (Open-Core readiness).

1. Domain Event Abstraction
	•	Formal event bus
	•	Decoupled domain events
	•	Plugin hook registration mechanism

2. Module Interfaces
	•	Custom transition guards
	•	Custom reporting modules
	•	Custom validation rules

3. Config-Driven Features
	•	Workflow templates
	•	Conditional transitions
	•	Pluggable validation components

Priority: Strategic differentiation.

⸻

Phase 4 – Enterprise Readiness (v0.8)

Goal: Operational maturity for on-premise deployments.

1. API Versioning

2. Configurable Logging

3. Advanced Health & Metrics

4. Backup & Restore Strategy

5. Deployment Hardening Documentation

6. Upgrade Strategy Documentation

7. Structured Release Policy

Priority: Required for enterprise contracts.

⸻

Phase 5 – Governance & Segregation Model (v0.9)

Goal: Institutional deployment readiness.

1. Data Segregation Models
	•	tenant_id (optional)
	•	Alternative department_id segmentation

2. Advanced Audit Capabilities
	•	Immutable audit events
	•	Actor tracking
	•	Metadata capture
	•	Exportable audit trails

3. Isolation Enforcement Policies
	•	Cross-tenant protection rules
	•	Enforcement testing

Priority: Critical for government environments.

⸻

Phase 6 – Productisation (v1.0)

Goal: Stable governance infrastructure release.

1. Frontend Layer (UI abstraction)

2. Deployment Packaging

3. Enterprise Governance Add-ons

4. Multi-tenant Configuration Model

5. Long-term Maintenance Policy

6. LTS Support Model

Priority: After architectural stabilization.

⸻

Strategic Principle

MATS evolves infrastructure first.

Features are secondary.
Governance, stability, and extensibility are primary.

Modernisation must reduce risk, not introduce it.
