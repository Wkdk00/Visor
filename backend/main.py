"""
    Application Entry point.
"""
import uvicorn
from fastapi import FastAPI, WebSocket
from api.routes import router
from api.websocket import ws_stream_handler
from database.db import Base, engine
from exceptions import register_exception_handlers

app = FastAPI()
app.include_router(router, prefix="/api/v1")
register_exception_handlers(app)

@app.on_event("startup")
async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.websocket("/ws/processed")
async def stream(ws: WebSocket) -> None:
    """
    WebSocket-эндпоинт для получения обработанного видеопотока.

    Принимает входящее WebSocket-соединение и делегирует его обработку.

    Args:
        ws (WebSocket): Incoming WebSocket client.
    """
    await ws_stream_handler(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)