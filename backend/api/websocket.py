import asyncio
import logging
from fastapi import WebSocket
from workers.stream import fetch, process

logger = logging.getLogger(__name__)

async def ws_stream_handler(ws: WebSocket) -> None:
    """
    Обработчик WebSocket-соединения для потоковой передачи видео.

    Данная функция управляет жизненным циклом потока:
    1. Принимает входящее соединение.
    2. Создает независимые очереди (raw_q, proc_q) для конкретного клиента.
    3. Запускает фоновые задачи (fetch и process) как `asyncio.Task`.
    4. Транслирует обработанные кадры обратно клиенту через WebSocket.

    Args:
        ws (WebSocket): Инстанс соединения FastAPI.
    """
    await ws.accept()
    raw_q = asyncio.Queue(maxsize=1)
    proc_q = asyncio.Queue(maxsize=1)
    
    t1 = asyncio.create_task(fetch(raw_q))
    t2 = asyncio.create_task(process(raw_q, proc_q))
    
    try:
        while True:
            await ws.send_bytes(await proc_q.get())
    except Exception as e:
        logger.info(f"Stream closed: {e}")
    finally:
        t1.cancel()
        t2.cancel()