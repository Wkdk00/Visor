from sqlalchemy.ext.asyncio import AsyncSession
from api.employee.repository import get_all, get_by_id, create, update, delete
from api.employee.schemas import EmployeeCreate
from database.models import Employee
from exceptions import NotFoundFromDB

async def list_employees(db: AsyncSession, skip: int, limit: int):
    return await get_all(db, skip, limit)

async def retrieve_employee(db: AsyncSession, employee_id: int):
    employee = await get_by_id(db, employee_id)
    if not employee:
        raise NotFoundFromDB("Employee")
    return employee

async def create_employee(db: AsyncSession, data: EmployeeCreate):
    db_employee = Employee(**data.model_dump())
    return await create(db, db_employee)

async def update_employee(db: AsyncSession, employee_id: int, data: EmployeeCreate):
    db_employee = await get_by_id(db, employee_id)
    if not db_employee:
        raise NotFoundFromDB("Employee")
    
    for key, value in data.model_dump().items():
        setattr(db_employee, key, value)
        
    return await update(db, db_employee)

async def remove_employee(db: AsyncSession, employee_id: int):
    db_employee = await get_by_id(db, employee_id)
    if not db_employee:
        raise NotFoundFromDB("Employee")
        
    await delete(db, db_employee)
    return {"ok": True}