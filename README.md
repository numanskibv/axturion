# Workflow-Driven ATS Platform (Backend)

A modular, workflow-driven Applicant Tracking System (ATS) backend inspired by Odoo.

This project is **backend-first** and focuses on **configuration over code**:
- workflows are defined as data
- transitions are centrally enforced
- automation rules react to workflow events
- activities provide a full, auditable candidate timeline

The ATS is the **first concrete use case**.  
The underlying goal is a **reusable workflow & automation platform** suitable for complex business processes.

---

## Key Features

- Configurable workflow engine (stages & transitions)
- Strict transition validation (no invalid state changes)
- Automation rules triggered by workflow events
- Activity timeline (system events, automation, user actions)
- Clean service-layer architecture (SOLID)
- FastAPI + SQLAlchemy
- Docker-first, on-premise friendly
- Designed for extensibility and modularity

---

## Architectural Principles

This project intentionally avoids “CRUD-only” design.

Core principles:
- **Workflow is data, not code**
- **Commands and queries are separated**
- **Business logic lives in services**
- **No framework leakage into the domain**
- **Editor-friendly backend (Odoo-style)**

The codebase is structured to be readable, explicit and refactor-friendly.

---

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Run locally
Bash: docker compose up --build
Then open: http://localhost:8000/docs

## Project structure ##
app/
├── api/            # FastAPI routes (HTTP layer)
├── core/           # DB setup, configuration, seeding
├── domain/         # Domain models (ATS concepts)
├── services/       # Business logic (workflow, automation)
├── automation/     # Automation engine

## Current Status ## 7 feb 2026
The project is under active development.

Implemented:
	•	Workflow engine with enforced transitions
	•	Automation engine reacting to workflow events
	•	Activity timeline
	•	Read-only workflow editor endpoints

Planned next steps:
	•	Workflow editor mutations (add/remove stages & transitions)
	•	Permissions and roles
	•	Versioned workflows
	•	Webhooks & integrations
	•	Lightweight test coverage

⸻

## Contributing ##

Contributions are welcome, especially around:
	•	workflow integrity rules
	•	automation actions
	•	architectural improvements
	•	documentation

Please open an issue before proposing major changes.

This project values clarity and design discipline over feature quantity.

⸻

## License ##

Apache License 2.0
