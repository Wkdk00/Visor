from sqlalchemy.ext.asyncio import AsyncSession
from api.position.repository import get_all, get_by_id, create, update, delete
from api.position.schemas import PositionCreate
from exceptions import NotFoundFromDB
from database.models import Position

async def list_positions(db: AsyncSession, skip: int, limit: int):
    return await get_all(db, skip, limit)

async def retrieve_position(db: AsyncSession, position_id: int):
    position = await get_by_id(db, position_id)
    if not position:
        raise NotFoundFromDB("Position")
    return position

async def create_position(db: AsyncSession, data: PositionCreate):
    db_position = Position(**data.model_dump())
    return await create(db, db_position)

async def update_position(db: AsyncSession, position_id: int, data: PositionCreate):
    db_position = await get_by_id(db, position_id)
    if not db_position :
        raise NotFoundFromDB("Position")
    
    for key, value in data.model_dump().items():
        setattr(db_position, key, value)
        
    return await update(db, db_position)

async def remove_position(db: AsyncSession, position_id: int):
    db_position = await get_by_id(db, position_id)
    if not db_position:
        raise NotFoundFromDB("Position")
        
    await delete(db, db_position)
    return {"ok": True}