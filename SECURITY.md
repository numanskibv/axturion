# Security Policy

MATS is designed for governance-oriented environments where
data control, auditability, and infrastructure ownership are critical.

This document outlines the security posture and reporting process.

---

## Supported Versions

Security fixes are applied to the latest minor release within the current development line.

Example:
- 0.4.x → supported
- 0.3.x → security fixes only (no feature updates)
- <0.3.0 → not supported

Future LTS policies may be defined under enterprise deployments.

---

## Security Principles

MATS is built with the following security foundations:

- Workflow isolation enforced at service layer
- No cross-workflow data leakage
- Deterministic reporting logic
- Explicit mutation validation
- No implicit privilege escalation
- API-first design (clear boundaries)
- On-premise deployment compatibility

MATS does not rely on hidden background processing or opaque automation.

All critical state changes are logged and auditable.

---

## Reporting a Vulnerability

If you discover a security vulnerability:

Please do NOT open a public issue.

Instead, contact:

security@mats-platform.org  
(or replace with official contact once defined)

Include:

- Description of the issue
- Steps to reproduce
- Affected version
- Potential impact assessment

We aim to:

- Acknowledge receipt within 72 hours
- Provide a remediation timeline
- Publish a patch release if required

---

## Deployment Responsibility

MATS is infrastructure software.

Security posture depends on:

- Network configuration
- Database security
- Authentication layer integration
- Reverse proxy setup
- OS hardening

Enterprise deployments should:

- Use TLS termination
- Restrict database access
- Apply role-based access controls
- Implement regular backups
- Monitor audit logs

---

## Scope Limitations

The current open-core version does NOT include:

- Built-in authentication provider
- IAM federation
- SSO integrations
- Advanced role-based access control

These may be provided in enterprise layers.

---

## Security Philosophy

Security is not a feature.
It is a structural property of the architecture.

MATS prioritizes:

- Explicit logic over implicit behavior
- Isolation over convenience
- Determinism over automation opacity