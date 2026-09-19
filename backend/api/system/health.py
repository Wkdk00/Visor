import asyncio
from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db 
from setup import container

router = APIRouter()

@router.get("/health")
async def check_health(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    health_status = {
        "status": "ok",
        "database": "disconnected",
        "vector_db": "disconnected"
    }
    
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"

    try:
        await asyncio.to_thread(container.qdrant.client.get_collections)
        health_status["vector_db"] = "connected"
    except Exception as e:
        health_status["vector_db"] = f"error: {str(e)}"

    if "error" in health_status["database"] or "error" in health_status["vector_db"]:
        health_status["status"] = "degraded"
        return JSONResponse(
            content=health_status, 
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return JSONResponse(content=health_status, status_code=status.HTTP_200_OK)