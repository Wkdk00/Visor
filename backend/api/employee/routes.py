from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db import get_db
from api.employee.schemas import Employee as EmployeeSchema, EmployeeCreate
from api.employee.service import list_employees, retrieve_employee, create_employee, update_employee, remove_employee

router = APIRouter()

@router.get("/", response_model=List[EmployeeSchema])
async def get_employees(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await list_employees(db, skip, limit)

@router.get("/{employee_id}", response_model=EmployeeSchema)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    return await retrieve_employee(db, employee_id)

@router.post("/", response_model=EmployeeSchema, status_code=status.HTTP_201_CREATED)
async def post_employee(employee: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    return await create_employee(db, employee)

@router.put("/{employee_id}", response_model=EmployeeSchema)
async def put_employee(employee_id: int, employee: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    return await update_employee(db, employee_id, employee)

@router.delete("/{employee_id}")
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    return await remove_employee(db, employee_id)