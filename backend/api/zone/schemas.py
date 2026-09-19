from pydantic import BaseModel
from datetime import datetime

class ZoneBase(BaseModel):
    zone_name: str
    sequrity_level: int
    created_at: datetime

class ZoneCreate(BaseModel):
    zone_name: str
    sequrity_level: int

class Zone(ZoneCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True