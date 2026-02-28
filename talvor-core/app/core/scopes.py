"""Scope strings for minimal scope-based authorization.

This is a pilot for endpoint-level authorization using exact-match scopes.
"""

APPLICATION_READ = "application:read"
APPLICATION_CREATE = "application:create"
APPLICATION_MOVE_STAGE = "application:move_stage"
APPLICATION_CLOSE = "application:close"

WORKFLOW_READ = "workflow:read"
WORKFLOW_WRITE = "workflow:write"

REPORTING_READ = "reporting:read"
AUDIT_READ = "audit:read"

COMPLIANCE_EXPORT = "compliance:export"

JOB_CREATE = "job:create"
JOB_READ = "job:read"
JOB_UPDATE = "job:update"
JOB_CLOSE = "job:close"

CANDIDATE_CREATE = "candidate:create"
CANDIDATE_READ = "candidate:read"
CANDIDATE_UPDATE = "candidate:update"
