from sqlalchemy.ext.asyncio import AsyncSession
from api.department.repository import get_all, get_by_id, create, update, delete
from api.department.schemas import DepartmentCreate
from database.models import Department
from exceptions import NotFoundFromDB

async def list_departments(db: AsyncSession, skip: int, limit: int):
    return await get_all(db, skip, limit)

async def retrieve_department(db: AsyncSession, department_id: int):
    department = await get_by_id(db, department_id)
    if not department:
        raise NotFoundFromDB("Department")
    return department

async def create_department(db: AsyncSession, data: DepartmentCreate):
    db_department = Department(**data.model_dump())
    return await create(db, db_department)

async def update_department(db: AsyncSession, department_id: int, data: DepartmentCreate):
    db_department = await get_by_id(db, department_id)
    if not db_department:
        raise NotFoundFromDB("Department")
    
    for key, value in data.model_dump().items():
        setattr(db_department, key, value)
        
    return await update(db, db_department)

async def remove_department(db: AsyncSession, department_id: int):
    db_department = await get_by_id(db, department_id)
    if not db_department:
        raise NotFoundFromDB("Department")
        
    await delete(db, db_department)
    return {"ok": True}