# MATS
# Modular ATS Platform (Workflow-Driven)

A modular, workflow-driven Applicant Tracking System (ATS) backend inspired by Odoo.

This project focuses on **configuration over code**:
- workflows are data-driven
- transitions are enforced centrally
- automation rules react to workflow events
- activities provide a full candidate timeline

The ATS is the first use case — the underlying platform is designed for reusable workflow automation.

---

## Features ##

- Workflow engine with configurable stages & transitions
- Automation rules triggered by workflow events
- Activity timeline (audit + actions)
- Clean service-layer architecture (SOLID)
- FastAPI + SQLAlchemy backend
- Docker-first setup
- Designed for on-premise and extensibility

---

## Architectural Principles ##

- **Workflow is data, not code**
- **Commands and queries are separated**
- **Business logic lives in services**
- **No framework leakage into the domain**
- **Inspired by Odoo, not a clone**

---

## Getting Started ##

### Prerequisites ###
- Docker
- Docker Compose

### Run locally ##
docker compose up --build

Then open: http://localhost:8000/docs

## Project Structure ##

app/
├── api/            # FastAPI routes
├── core/           # DB, config, seeding
├── domain/         # Domain models (ATS concepts)
├── services/       # Business logic
├── automation/     # Automation engine

# Current Status #
This project is under active development.

Planned next steps:
	•	Workflow editor mutations (add/remove stages)
	•	Permissions & roles
	•	Versioned workflows
	•	Webhooks & external integrations
	•	Minimal frontend (optional)

## Contributing ##

Contributions are welcome, especially around:
	•	workflow integrity rules
	•	automation actions
	•	test coverage
	•	documentation

