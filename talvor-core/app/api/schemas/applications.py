from pydantic import BaseModel

class MoveStageRequest(BaseModel):
    new_stage: str