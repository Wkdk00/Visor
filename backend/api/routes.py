from fastapi import APIRouter

from api.biometric.routes import router as biometric_router
from api.department.routes import router as department_router
from api.employee.routes import router as employee_router
from api.position.routes import router as position_router
from api.system.health import router as health_router
from api.zone.routes import router as zone_router

router = APIRouter()

router.include_router(biometric_router, prefix="/biometrics", tags=["Biometrics"])
router.include_router(department_router, prefix="/departments", tags=["Departments"])
router.include_router(employee_router, prefix="/employees", tags=["Employees"])
router.include_router(position_router, prefix="/positions", tags=["Positions"])
router.include_router(zone_router, prefix="/zones", tags=["Zones"])

router.include_router(health_router, tags=["System"])