# Roadmap

This document outlines the **intended direction** of the project.

It is **not a commitment**, timeline, or guarantee.
Items may change based on insights, discussions, or real-world usage.

The roadmap exists to provide context and architectural intent.

---

## Guiding Principles

- Prefer **correctness and clarity** over speed
- Favor **configuration over code**
- Avoid premature features
- Keep the core small and composable
- Maintain backend-first discipline

---

## Near Term (Exploration & Hardening)

Focus: strengthening the core workflow and automation concepts.

- Workflow editor mutations (add/remove stages and transitions)
- Workflow integrity rules (prevent breaking active applications)
- Stage change events logged as activities
- Allowed-transitions queries for UI and automation
- Minor model refinements (e.g. stage ordering)

---

## Mid Term (Stability & Extensibility)

Focus: making the platform safer and more reusable.

- Basic permissions and roles
- Workflow reuse and assignment strategies
- Versioned workflows (non-breaking changes)
- Automation rule extensions
- Improved seeding and setup flows

---

## Long Term (Optional & Exploratory)

Focus: integrations and broader applicability.

- Webhooks and external event integrations
- Additional domain use cases beyond ATS
- Lightweight test coverage for core services
- Optional reference frontend (out of scope by default)
- Multi-organization isolation (governance deployments)
- Versioned workflow configuration
- Enterprise governance layer
- Advanced audit and compliance reporting

---

## Explicitly Out of Scope (for now)

- Full-featured frontend application
- SaaS / multi-tenant hosting
- End-user UI design
- Enterprise-specific customizations

---

## Notes for Contributors

This roadmap is intentionally conservative.

Suggestions are welcome, but changes to direction should be discussed
before implementation to maintain architectural consistency.