from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db import get_db
from api.zone.schemas import Zone as ZoneSchema, ZoneCreate
from api.zone.service import list_zones, retrieve_zone, create_zone, update_zone, remove_zone

router = APIRouter()

@router.get("/", response_model=List[ZoneSchema])
async def get_zones(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await list_zones(db, skip, limit)

@router.get("/{zone_id}", response_model=ZoneSchema)
async def get_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    return await retrieve_zone(db, zone_id)

@router.post("/", response_model=ZoneSchema, status_code=status.HTTP_201_CREATED)
async def post_zone(zone: ZoneCreate, db: AsyncSession = Depends(get_db)):
    return await create_zone(db, zone)

@router.put("/{zone_id}", response_model=ZoneSchema)
async def put_zone(zone_id: int, zone: ZoneCreate, db: AsyncSession = Depends(get_db)):
    return await update_zone(db, zone_id, zone)

@router.delete("/{zone_id}")
async def delete_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    return await remove_zone(db, zone_id)