import asyncio
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

app = FastAPI()
cap = cv2.VideoCapture(0)

def grab_frame():
    """Синхронная функция чтения и кодирования вынесена отдельно"""
    ret, frame = cap.read()
    if not ret:
        return False, None
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return True, buf.tobytes()

@app.websocket("/ws/video")
async def video_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Читаем кадр в отдельном потоке, не блокируя event-loop
            ret, frame_bytes = await run_in_threadpool(grab_frame)
            
            if not ret:
                break
                
            await websocket.send_bytes(frame_bytes)
            
            # Магическая строка: отдает управление обратно FastAPI
            # чтобы он мог ответить на закрытие соединения или системные пакеты
            await asyncio.sleep(0.001) 
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Producer error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)