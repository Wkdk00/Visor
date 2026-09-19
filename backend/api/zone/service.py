from sqlalchemy.ext.asyncio import AsyncSession
from api.zone.repository import get_all, get_by_id, create, update, delete
from api.zone.schemas import ZoneCreate
from database.models import Zone
from exceptions import NotFoundFromDB
    
async def list_zones(db: AsyncSession, skip: int, limit: int):
    return await get_all(db, skip, limit)

async def retrieve_zone(db: AsyncSession, zone_id: int):
    zone = await get_by_id(db, zone_id)
    if not zone:
        raise NotFoundFromDB("Zone")
    return zone

async def create_zone(db: AsyncSession, data: ZoneCreate):
    db_zone = Zone(**data.model_dump())
    return await create(db, db_zone)

async def update_zone(db: AsyncSession, zone_id: int, data: ZoneCreate):
    db_zone = await get_by_id(db, zone_id)
    if not db_zone:
        raise NotFoundFromDB("Zone")

    for key, value in data.model_dump().items():
        setattr(db_zone, key, value)

    return await update(db, db_zone)

async def remove_zone(db: AsyncSession, zone_id: int):
    db_zone = await get_by_id(db, zone_id)
    if not db_zone:
        raise NotFoundFromDB("Zone")

    await delete(db, db_zone)
    return {"ok": True}