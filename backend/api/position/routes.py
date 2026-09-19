from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db import get_db
from api.position.schemas import Position as PositionSchema, PositionCreate
from api.position.service import list_positions, retrieve_position, create_position, update_position, remove_position

router = APIRouter()

@router.get("/", response_model=List[PositionSchema])
async def get_positions(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await list_positions(db, skip, limit)

@router.get("/{position_id}", response_model=PositionSchema)
async def get_position(position_id: int, db: AsyncSession = Depends(get_db)):
    return await retrieve_position(db, position_id)

@router.post("/", response_model=PositionSchema, status_code=status.HTTP_201_CREATED)
async def post_position(position: PositionCreate, db: AsyncSession = Depends(get_db)):
    return await create_position(db, position)

@router.put("/{position_id}", response_model=PositionSchema)
async def put_position(position_id: int, position: PositionCreate, db: AsyncSession = Depends(get_db)):
    return await update_position(db, position_id, position)

@router.delete("/{position_id}")
async def delete_position(position_id: int, db: AsyncSession = Depends(get_db)):
    return await remove_position(db, position_id)