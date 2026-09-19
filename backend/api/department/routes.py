from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db import get_db
from api.department.schemas import Department as DepartmentSchema, DepartmentCreate
from api.department.service import list_departments, retrieve_department, create_department, update_department, remove_department

router = APIRouter()

@router.get("/", response_model=List[DepartmentSchema])
async def get_departments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await list_departments(db, skip, limit)

@router.get("/{department_id}", response_model=DepartmentSchema)
async def get_department(department_id: int, db: AsyncSession = Depends(get_db)):
    return await retrieve_department(db, department_id)

@router.post("/", response_model=DepartmentSchema, status_code=status.HTTP_201_CREATED)
async def post_department(department: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    return await create_department(db, department)

@router.put("/{department_id}", response_model=DepartmentSchema)
async def put_department(department_id: int, department: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    return await update_department(db, department_id, department)

@router.delete("/{department_id}")
async def delete_department(department_id: int, db: AsyncSession = Depends(get_db)):
    return await remove_department(db, department_id)