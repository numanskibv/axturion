from pydantic import BaseModel
from uuid import UUID


class WorkflowStageResponse(BaseModel): # API response schema for workflow stages.
    id: UUID
    name: str
    order: int


class WorkflowTransitionResponse(BaseModel): # API response schema for workflow transitions.
    from_stage: str
    to_stage: str


class WorkflowDefinitionResponse(BaseModel): # API response schema for full workflow definition.
    id: UUID
    name: str
    stages: list[WorkflowStageResponse]
    transitions: list[WorkflowTransitionResponse]

    class Config:
        from_attributes = True

class CreateWorkflowStageRequest(BaseModel): # API request schema for creating a new workflow stage.
    name: str
    order: int | None = None


class WorkflowStageCreatedResponse(BaseModel): # API response schema for a newly created workflow stage.
    id: UUID
    name: str
    order: int