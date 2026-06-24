"""
    Точка входа в приложение.
"""
import uvicorn
from fastapi import FastAPI, WebSocket
from api.websocket import ws_stream_handler

app = FastAPI()

@app.websocket("/ws/processed")
async def stream(ws: WebSocket) -> None:
    """
    WebSocket-эндпоинт для получения обработанного видеопотока.

    Принимает входящее WebSocket-соединение и делегирует его обработку.

    Args:
        ws (WebSocket): Входящий WebSocket-клиент.
    """
    await ws_stream_handler(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)