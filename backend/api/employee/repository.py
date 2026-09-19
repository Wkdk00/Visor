from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Employee

async def get_all(db: AsyncSession, skip: int, limit: int):
    result = await db.execute(select(Employee).offset(skip).limit(limit))
    return result.scalars().all()

async def get_by_id(db: AsyncSession, employee_id: int):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    return result.scalar_one_or_none()

async def create(db: AsyncSession, employee: Employee):
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee

async def update(db: AsyncSession, employee: Employee):
    await db.commit()
    await db.refresh(employee)
    return employee

async def delete(db: AsyncSession, employee: Employee):
    await db.delete(employee)
    await db.commit()