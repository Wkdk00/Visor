from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.requests import Request

from .base import NotFoundFromDB

async def not_found_handler(request: Request, exc: NotFoundFromDB):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

def register_exception_handlers(app):
    app.add_exception_handler(NotFoundFromDB, not_found_handler)