from pydantic import BaseModel
from datetime import date
from typing import Optional

class EmployeeBase(BaseModel):
    full_name: str
    passport: str
    department_id: int
    position_id: Optional[int] = None
    post: str
    badge_id: int
    security_level: int
    phone_number: Optional[str] = None
    mail: Optional[str] = None
    address: str
    birth: date
    updated_at: date

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    class Config:
        from_attributes = True