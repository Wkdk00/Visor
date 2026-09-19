from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Position

async def get_all(db: AsyncSession, skip: int, limit: int):
    result = await db.execute(select(Position).offset(skip).limit(limit))
    return result.scalars().all()

async def get_by_id(db: AsyncSession, position_id: int):
    result = await db.execute(select(Position).where(Position.id == position_id))
    return result.scalar_one_or_none()

async def create(db: AsyncSession, position: Position):
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return position

async def update(db: AsyncSession, position: Position):
    await db.commit()
    await db.refresh(position)
    return position

async def delete(db: AsyncSession, position: Position):
    await db.delete(position)
    await db.commit()