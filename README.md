AXTURION Platform

AXTURION is a governed recruitment execution platform.

It combines lifecycle management, governance enforcement, audit integrity, and operational analytics into a single controlled system.

AXTURION is not just an Applicant Tracking System (ATS).
It is a policy-aware execution engine for recruitment workflows.

⸻

PLATFORM COMPONENTS

AXTURION consists of two primary systems:
	1.	AXTURION Core
FastAPI-based backend responsible for:
	•	Domain logic (Applications, Jobs, Candidates, Workflows)
	•	Lifecycle state transitions
	•	Governance enforcement (PolicyConfig)
	•	SLA rules
	•	Retention previews
	•	4-eyes approval workflows
	•	Audit chain integrity
	•	Lifecycle reporting
	•	Compliance export
	2.	AXTURION Command
Next.js-based frontend responsible for:
	•	Operational dashboard
	•	SLA breach visibility
	•	UX configuration management
	•	Version history and rollback interface
	•	Governance-aware UI presentation

All authority lives in Core.
Command is a controlled presentation layer.

⸻

CORE CAPABILITIES

Lifecycle Engine
	•	Stage transitions
	•	Time-to-close tracking
	•	Stage duration analytics

Governance Engine
	•	Org-scoped PolicyConfig
	•	SLA configuration
	•	Retention rules
	•	4-eyes rollback enforcement
	•	Scope-based authorization (RBAC)

Audit Integrity
	•	Append-only audit log
	•	Hash chaining
	•	Verification support
	•	Compliance bundle export

Reporting Layer
	•	Stage Aging
	•	Time to Close
	•	Stage Duration Summary

All reporting is derived from domain state and audit events.

⸻

GOVERNANCE PRINCIPLES
	1.	No silent rule changes.
	2.	Policies are configuration, not code.
	3.	All critical actions are auditable.
	4.	Org isolation is absolute.
	5.	Frontend never enforces governance.
	6.	Reporting reflects policy — not the other way around.

Governance is not a feature.
It is a control layer.

⸻

UX CONFIGURATION SYSTEM

AXTURION supports controlled UI customization:
	•	Layout configuration
	•	Theme configuration
	•	Feature flags
	•	Version history
	•	Diff inspection
	•	Rollback
	•	Optional 4-eyes approval

All UX changes are audited and traceable.

⸻

SECURITY MODEL
	•	Org-scoped data isolation
	•	Scope-based authorization
	•	Explicit role-to-scope mapping
	•	Audit log verification
	•	Governance-enforced rollback control

Security is enforced in Core.

⸻

ARCHITECTURE DOCUMENTATION

See:
	•	ARCHITECTURE.md (Platform Overview)
	•	axturion-core/docs/CORE_ARCHITECTURE.md
	•	axturion-core/docs/GOVERNANCE_ENGINE.md
	•	axturion-command/docs/COMMAND_ARCHITECTURE.md
	•	axturion-command/docs/DASHBOARD_DESIGN.md
	•	axturion-command/docs/UX_CONFIG_SYSTEM.md

⸻

LOCAL DEVELOPMENT

The platform can be run using Docker via the root docker-compose.yml.

AXTURION Core runs on:
http://localhost:8000

AXTURION Command runs on:
http://localhost:3000/dashboard

Environment variables and setup details are described in the respective subproject README files.

⸻

POSITIONING

AXTURION is designed for organizations that require:
	•	Policy-controlled recruitment workflows
	•	Audit-grade change tracking
	•	SLA-aware lifecycle management
	•	Controlled UX customization
	•	Enterprise governance alignment

AXTURION is not optimized for hobby projects.
It is designed for governed, multi-tenant, enterprise recruitment environments.