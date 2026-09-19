import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import get_all, get_by_id, create, update, delete
from .schemas import BiometricCreate
from core.config import BIOMETRIC_STORAGE
from database.models import Biometric
from exceptions import NotFoundFromDB

STORAGE_DIR = Path(BIOMETRIC_STORAGE)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

async def list_biometrics(db: AsyncSession, skip: int, limit: int):
    return await get_all(db, skip, limit)

async def retrieve_biometric(db: AsyncSession, biometric_id: int):
    biometric = await get_by_id(db, biometric_id)
    if not biometric:
        raise NotFoundFromDB("Biometric")
    return biometric

async def retrieve_photo(db: AsyncSession, biometric_id: int) -> str:
    biometric = await get_by_id(db, biometric_id)
    if not biometric:
        raise NotFoundFromDB("Biometric")
    return biometric.photo_path

async def create_biometric(db: AsyncSession, data: BiometricCreate, file: UploadFile):
    filename = f"{data.employee_id}.jpg"
    file_path = STORAGE_DIR / filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    db_biometric = Biometric(employee_id=data.employee_id, photo_path=str(file_path))
    return await create(db, db_biometric)

async def update_biometric(db: AsyncSession, biometric_id: int, data: BiometricCreate, file: UploadFile):
    db_biometric = await get_by_id(db, biometric_id)
    if not db_biometric:
        raise NotFoundFromDB("Biometric")
    
    file_path = STORAGE_DIR / f"{db_biometric.employee_id}.jpg"
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return await update(db, db_biometric)

async def remove_biometric(db: AsyncSession, biometric_id: int):
    db_biometric = await get_by_id(db, biometric_id)
    if not db_biometric:
        raise NotFoundFromDB("Biometric")
    
    photo_path = Path(db_biometric.photo_path)
    if photo_path.exists():
        photo_path.unlink()
    
    await delete(db, db_biometric)
    return {"ok": True}