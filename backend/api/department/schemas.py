from pydantic import BaseModel
from typing import Optional

class DepartmentBase(BaseModel):
    department: str
    description: Optional[str] = None

class DepartmentCreate(DepartmentBase):
    pass

class Department(DepartmentBase):
    id: int
    class Config:
        from_attributes = True