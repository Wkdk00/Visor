from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Zone

async def get_all(db: AsyncSession, skip: int, limit: int):
    result = await db.execute(select(Zone).offset(skip).limit(limit))
    return result.scalars().all()

async def get_by_id(db: AsyncSession, zone_id: int):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    return result.scalar_one_or_none()

async def create(db: AsyncSession, zone: Zone):
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone

async def update(db: AsyncSession, zone: Zone):
    await db.commit()
    await db.refresh(zone)
    return zone

async def delete(db: AsyncSession, zone: Zone):
    await db.delete(zone)
    await db.commit()