from pydantic import BaseModel
from uuid import UUID


class WorkflowListItem(BaseModel):
    id: UUID
    name: str
    active: bool
