from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db import get_db
from .schemas import Biometric as BiometricSchema, BiometricCreate
from .service import list_biometrics, retrieve_biometric, retrieve_photo, create_biometric, update_biometric, remove_biometric

router = APIRouter()

@router.get("/", response_model=List[BiometricSchema])
async def get_biometrics(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await list_biometrics(db, skip, limit)

@router.get("/{biometric_id}", response_model=BiometricSchema)
async def get_biometric(biometric_id: int, db: AsyncSession = Depends(get_db)):
    return await retrieve_biometric(db, biometric_id)

@router.get("/{biometric_id}/photo")
async def get_photo(biometric_id: int, db: AsyncSession = Depends(get_db)):
    photo_path = await retrieve_photo(db, biometric_id)
    return FileResponse(photo_path, media_type="image/jpeg")


@router.post("/", response_model=BiometricSchema, status_code=status.HTTP_201_CREATED)
async def post_biometric(
    data: BiometricCreate = Depends(),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await create_biometric(db, data, file)


@router.put("/{biometric_id}", response_model=BiometricSchema)
async def put_biometric(
    biometric_id: int,
    data: BiometricCreate = Depends(),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    return await update_biometric(db, biometric_id, data, file)

@router.delete("/{biometric_id}")
async def delete_biometric(biometric_id: int, db: AsyncSession = Depends(get_db)):
    return await remove_biometric(db, biometric_id)