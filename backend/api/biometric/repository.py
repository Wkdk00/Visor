from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Biometric

async def get_all(db: AsyncSession, skip: int, limit: int):
    result = await db.execute(select(Biometric).offset(skip).limit(limit))
    return result.scalars().all()

async def get_by_id(db: AsyncSession, biometric_id: int):
    result = await db.execute(select(Biometric).where(Biometric.id == biometric_id))
    return result.scalar_one_or_none()

async def create(db: AsyncSession, biometric: Biometric):
    db.add(biometric)
    await db.commit()
    await db.refresh(biometric)
    return biometric

async def update(db: AsyncSession, biometric: Biometric):
    await db.commit()
    await db.refresh(biometric)
    return biometric

async def delete(db: AsyncSession, biometric: Biometric):
    await db.delete(biometric)
    await db.commit()