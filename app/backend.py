import asyncio
import logging
from time import time

import cv2
import numpy as np
import websockets
from fastapi import FastAPI, WebSocket
from starlette.concurrency import run_in_threadpool

from app.config import PRODUCER_URL
from app.decorators import safe_execute
from app.message import TextArea
from app.model_detection import Model
from app.person import PersonTemplate
from app.pipeline import Pipeline
from app.thread_storage import ThreadResult
from app.qdrant import QdrantRecognizer


qdrant = QdrantRecognizer()
message = TextArea()

app = FastAPI()
raw_q = asyncio.Queue(maxsize=1)
proc_q = asyncio.Queue(maxsize=1)

model = Model()
person = PersonTemplate()
thread_storage = ThreadResult()
pipeline = Pipeline(model=model, message=message, storage=thread_storage, person=person, vec_DB=qdrant)

logger = logging.getLogger(__name__)

@safe_execute(default_return=None)
def heavy_logic(frame: np.ndarray) -> np.ndarray | None:
    """Выполняет основную логику обработки кадра через Pipeline.

    Прогоняет кадр через конвейер детекции, распознавания и OCR и возвращает
    готовый кадр.

    Args:
        frame (np.ndarray): Исходный кадр видеопотока в BGR.

    Returns:
        np.ndarray: Обработанный кадр.
    """
    start = time()
    frame = pipeline.check_camera(frame)
    frame = cv2.flip(frame, 1)
    message.print_text(frame)
    latency = int((time() - start) * 1000)
    cv2.putText(frame, f"{latency}ms", (10, frame.shape[0] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    return frame


async def fetch() -> None:
    """Получает видеопоток через WebSocket.

    Подключается к PRODUCER_URL, декодирует полученные JPEG-кадры
    и помещает их в очередь raw_q для последующей обработки.
    При ошибке соединения выполняет повторное подключение через 1 секунду.
    """
    async with websockets.connect(PRODUCER_URL) as ws:
        while True:
            try:
                data = await ws.recv()
                frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    while not raw_q.empty(): 
                        await raw_q.get()
                    await raw_q.put(frame)
            except Exception as e:
                print(f"Fetch error: {e}")
                await asyncio.sleep(1)

@safe_execute()
async def process() -> None:
    """
    Задача обработки видеопотока (Consumer/Processor).
    
    Забирает сырые кадры из `raw_q`, выполняет тяжелую логику 
    (детекция, распознавание, OCR) в отдельном потоке, чтобы не блокировать 
    event-loop, и помещает результат в `proc_q`.
    """
    while True:
        try:
            frame = await raw_q.get()
            result = await run_in_threadpool(heavy_logic, frame)
            _, buf = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 75])
            while not proc_q.empty(): 
                await proc_q.get()
            await proc_q.put(buf.tobytes())
        except Exception as e:
            print(f"Process error: {e}")

@app.websocket("/ws/processed")
async def stream(ws: WebSocket) -> None:
    """
    WebSocket эндпоинт для стриминга обработанного видео клиенту.
    
    Управляет жизненным циклом подключения:
    1. Принимает соединение.
    2. Запускает фоновые задачи `fetch` и `process`.
    3. В цикле отправляет данные из `proc_q` клиенту.
    4. При разрыве соединения корректно отменяет фоновые задачи.
    
    Args:
        ws (WebSocket): Объект WebSocket соединения.
    
    Raises:
        WebSocketDisconnect: При разрыве соединения клиентом.
        Exception: При критических ошибках стриминга.
    """
    await ws.accept()
    t1 = asyncio.create_task(fetch())
    t2 = asyncio.create_task(process())
    try:
        while True:
            await ws.send_bytes(await proc_q.get())
    except Exception as e:
        logger.error(f"Stream error: {e}", exc_info=True)
    finally:
        t1.cancel()
        t2.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)