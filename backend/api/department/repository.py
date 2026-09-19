from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Department

async def get_all(db: AsyncSession, skip: int, limit: int):
    result = await db.execute(select(Department).offset(skip).limit(limit))
    return result.scalars().all()

async def get_by_id(db: AsyncSession, department_id: int):
    result = await db.execute(select(Department).where(Department.id == department_id))
    return result.scalar_one_or_none()

async def create(db: AsyncSession, department: Department):
    db.add(department)
    await db.commit()
    await db.refresh(department)
    return department

async def update(db: AsyncSession, department: Department):
    await db.commit()
    await db.refresh(department)
    return department

async def delete(db: AsyncSession, department: Department):
    await db.delete(department)
    await db.commit()