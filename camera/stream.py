from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import cv2

app = FastAPI()
cap = cv2.VideoCapture(0)

@app.websocket("/ws/video")
async def video_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            await websocket.send_bytes(buf.tobytes())
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Producer error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)