from pydantic import BaseModel
from typing import List


class StageSummaryItem(BaseModel):
    stage: str
    count: int


class WorkflowStageSummaryResponse(BaseModel):
    workflow_id: str
    workflow_name: str
    stages: List[StageSummaryItem]
    

class StageDurationItem(BaseModel):
    stage: str
    average_days: float
    count: int


class WorkflowStageDurationResponse(BaseModel):
    workflow_id: str
    workflow_name: str
    stages: List[StageDurationItem]
