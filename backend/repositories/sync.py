from sqlalchemy import select, func
from database.models import Employee, Biometric

from database.db import get_db 

async def get_employees_for_vector_init(
    offset: int, 
    limit: int
) -> list[tuple[int, str, str | None]]:    
    async for db in get_db():
        result = await db.execute(
            select(
                Employee.id,
                Employee.full_name,
                Biometric.photo_path
            )
            .outerjoin(Biometric, Employee.id == Biometric.employee_id)
            .offset(offset)
            .limit(limit)
        )
        return result.all()

async def get_employees_count() -> int:    
    async for db in get_db():
        result = await db.execute(select(func.count(Employee.id)))
        return result.scalar() or 0