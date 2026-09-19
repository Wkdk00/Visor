from pydantic import BaseModel
from datetime import date

class BiometricBase(BaseModel):
    employee_id: int

class BiometricCreate(BiometricBase):
    pass

class Biometric(BiometricBase):
    id: int
    photo_path: str
    created_at: date

    class Config:
        from_attributes = True