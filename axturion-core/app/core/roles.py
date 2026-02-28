from __future__ import annotations

from fastapi import HTTPException

from app.core.scopes import (
    APPLICATION_CLOSE,
    APPLICATION_CREATE,
    APPLICATION_MOVE_STAGE,
    APPLICATION_READ,
    AUDIT_READ,
    COMPLIANCE_EXPORT,
    JOB_CLOSE,
    JOB_CREATE,
    JOB_READ,
    JOB_UPDATE,
    REPORTING_READ,
    WORKFLOW_READ,
    WORKFLOW_WRITE,
    CANDIDATE_CREATE,
    CANDIDATE_READ,
    CANDIDATE_UPDATE,
    UX_READ,        # ✅ toegevoegd
    UX_WRITE,
)


ALL_DEFINED_SCOPES: set[str] = {
    APPLICATION_READ,
    APPLICATION_CREATE,
    APPLICATION_MOVE_STAGE,
    APPLICATION_CLOSE,
    WORKFLOW_READ,
    WORKFLOW_WRITE,
    REPORTING_READ,
    AUDIT_READ,
    COMPLIANCE_EXPORT,
    JOB_CREATE,
    JOB_READ,
    JOB_UPDATE,
    JOB_CLOSE,
    CANDIDATE_CREATE,
    CANDIDATE_READ,
    CANDIDATE_UPDATE,
    UX_READ,
    UX_WRITE,
}


ROLE_SCOPE_MAP: dict[str, set[str] | str] = {
    "recruiter": {
        APPLICATION_READ,
        APPLICATION_CREATE,
        APPLICATION_MOVE_STAGE,
        APPLICATION_CLOSE,
        WORKFLOW_READ,
        REPORTING_READ,
        JOB_READ,
        CANDIDATE_CREATE,
        CANDIDATE_READ,
        CANDIDATE_UPDATE,
        UX_READ,          # ✅ recruiter mag eigen UX bekijken
    },
    "hr_admin": {
        APPLICATION_READ,
        APPLICATION_CREATE,
        APPLICATION_MOVE_STAGE,
        APPLICATION_CLOSE,
        WORKFLOW_READ,
        WORKFLOW_WRITE,
        REPORTING_READ,
        COMPLIANCE_EXPORT,
        JOB_CREATE,
        JOB_READ,
        JOB_UPDATE,
        JOB_CLOSE,
        CANDIDATE_CREATE,
        CANDIDATE_READ,
        CANDIDATE_UPDATE,
        UX_READ,
        UX_WRITE,         # ✅ admin mag UX aanpassen
    },
    "auditor": {
        AUDIT_READ,
        REPORTING_READ,
        COMPLIANCE_EXPORT,
        APPLICATION_READ,
        JOB_READ,
        CANDIDATE_READ,
        UX_READ,          # ✅ auditor mag UX zien (read-only)
    },
    "stage_operator": {
        APPLICATION_READ,
        APPLICATION_MOVE_STAGE,
        UX_READ,
    },
    "platform_admin": "ALL",
}


def resolve_scopes_from_role(role: str) -> set[str]:
    role_key = str(role).strip()
    mapping = ROLE_SCOPE_MAP.get(role_key)

    if mapping is None:
        raise HTTPException(status_code=403, detail="Forbidden")

    if mapping == "ALL":
        return set(ALL_DEFINED_SCOPES)

    return set(mapping)