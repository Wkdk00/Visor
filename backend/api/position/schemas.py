from pydantic import BaseModel
from typing import Optional

class PositionBase(BaseModel):
    position: str
    description: Optional[str] = None
    department_id: int

class PositionCreate(PositionBase):
    pass

class Position(PositionBase):
    id: int
    class Config:
        from_attributes = True