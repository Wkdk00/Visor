import asyncio
import cv2
import numpy as np
import websockets
from time import time
from starlette.concurrency import run_in_threadpool
from setup import container
from core.config import PRODUCER_URL

def heavy_logic(frame: np.ndarray) -> np.ndarray | None:
    """
    Выполняет тяжелую вычислительную логику над кадром (детекция, распознавание).
    
    Args:
        frame (np.ndarray): Исходный кадр в формате BGR.
        
    Returns:
        np.ndarray | None: Обработанный кадр с отрисованным текстом и latency, 
                           либо None в случае ошибки обработки.
    """
    start = time()
    frame = container.pipeline.check_camera(frame)
    frame = cv2.flip(frame, 1)
    container.message.print_text(frame)
    latency = int((time() - start) * 1000)
    cv2.putText(frame, f"{latency}ms", (10, frame.shape[0] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    return frame

async def fetch(raw_q: asyncio.Queue) -> None:
    """
    Асинхронный воркер для захвата кадров по WebSocket.
    
    Поддерживает постоянное соединение с Producer. Если очередь переполнена,
    старый кадр удаляется, чтобы обрабатывался только самый актуальный (для минимизации задержки).
    
    Args:
        raw_q (asyncio.Queue): Очередь для передачи сырых кадров в процесс обработки.
    """
    while True:
        try:
            async with websockets.connect(PRODUCER_URL, ping_interval=None) as ws:
                while True:
                    data = await ws.recv()
                    frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        while not raw_q.empty(): 
                            try: raw_q.get_nowait()
                            except asyncio.QueueEmpty: break
                        raw_q.put_nowait(frame)
        except Exception as e:
            await asyncio.sleep(1)

async def process(raw_q: asyncio.Queue, proc_q: asyncio.Queue) -> None:
    """
    Воркер обработки кадров.
    
    Забирает сырой кадр из raw_q, отправляет его в ThreadPool для выполнения `heavy_logic`,
    после чего кодирует результат в JPEG и кладет в proc_q для дальнейшей отправки.
    
    Args:
        raw_q (asyncio.Queue): Очередь с входящими сырыми кадрами.
        proc_q (asyncio.Queue): Очередь с обработанными кадрами (байты JPEG).
    """
    while True:
        try:
            frame = await raw_q.get()
            result = await run_in_threadpool(heavy_logic, frame)
            if result is None: continue
            
            _, buf = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 75])
            while not proc_q.empty(): 
                try: proc_q.get_nowait()
                except asyncio.QueueEmpty: break
            proc_q.put_nowait(buf.tobytes())
        except asyncio.CancelledError:
            break