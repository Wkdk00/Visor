from sqlalchemy import select
from database.models import Employee
from database.db import get_db 

async def get_position_by_name(name: str) -> str | None:
    async for db in get_db():
        query = select(Employee.post).where(Employee.full_name == name).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()