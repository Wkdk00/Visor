import asyncio
import threading
from time import time
from typing import Callable

import cv2
import numpy as np
import websockets
from fastapi import FastAPI, WebSocket
from Levenshtein import ratio
from starlette.concurrency import run_in_threadpool
from ultralytics import YOLO

from app.message import TextArea
from app.ocr import ocr
from app.person import PersonTemplate
from app.thread_storage import ThreadResult
from app.qdrant import QdrantRecognizer
from app.utils import class_count, check_motionless, check_PPE_intersections

model = YOLO(r'C:\Users\Админ\Desktop\python\cv\runs\detect\train4\weights\best.pt')
qdrant = QdrantRecognizer()
message = TextArea()

class Model:
    def __init__(self):
        self.model = model
        self.counter = 0
        self.ex = False
        self.FREQUENCY = 45
        self.DICT_CLASSES = {
            0:("face", (0, 255, 0)),
            1:("cap", (255, 0, 0)),
            2:("mask", (0, 0, 255)),
            3:("glasses", (255, 255, 0)),
            4:("badge", (255, 255, 255))
        }

    def predict_yolo(self, frame: np.ndarray) -> list[dict]:
        pred = self.model(frame, verbose=False)
        boxes = pred[0].boxes
        results = []
        for i in range(len(boxes)):
            if boxes.conf[i] > 0.4:
                results.append({
                    "bbox": boxes.xyxy[i].cpu().numpy(),
                    "conf": boxes.conf[i].cpu().numpy(),
                    "cls": int(boxes.cls[i].cpu().numpy())
                })
                self.ex = True
        if len(results) == 0:
            self.ex = False
        return results

    def draw_rectangles(self, frame, boxes, classes: list = [0,1,2,3,4], confidence=0.4):
        for box in boxes:
            if box["cls"] in classes and box["conf"] > confidence:
                x1, y1, x2, y2 = map(int, box["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), self.DICT_CLASSES[box["cls"]][1], 3)
        return frame

    def check_camera(self, frame):
        if self.ex or self.counter == self.FREQUENCY:
            objects = self.predict_yolo(frame)
            frame = self.draw_rectangles(frame, objects)
            self.counter = 0
            if message.empty():
                frame = self.detect_pipeline(frame, objects)
        self.counter += 1
        return frame

    def detect_pipeline(self, frame, objects):
        count_objects, _ = class_count(objects)
        
        if person.state() == "unregistered":
            if count_objects[0] > 1:
                message.add_text("There must be only 1 person in the camera", "alert")
            elif not check_PPE_intersections(objects):
                message.add_text("Please remove the PPE", "alert")
            else:
                person_bbox = [b for b in objects if b["cls"] == 0][0]["bbox"]
                if check_motionless(person_bbox):
                    threading.Thread(target=process_worker, 
                                   args=(qdrant.scan, frame, person_bbox, thread_storage)).start()
            name = thread_storage.get_and_clear()
            if name:
                message.add_text(name, "name")
                person.set_vector_name(name)
    
        elif person.state() == "vectorized":
            if count_objects[4] == 1:
                badge_bbox = [b for b in objects if b["cls"] == 4][0]["bbox"]
                if check_motionless(badge_bbox):
                    threading.Thread(target=process_worker, 
                                   args=(ocr, frame, badge_bbox, thread_storage)).start()
            ocr_name = thread_storage.get_and_clear()
            if ocr_name:
                person.set_ocr_name(ocr_name)
                print(f"OCR: {ocr_name}")
                message.add_text(ocr_name, "name")

        elif person.state() == "ocr":
            if person.comparsion_vector_ocr():
                message.add_text("SUCCESS", "notice")
            else:
                message.add_text("ERROR", "alert")
            person.clear()
        
        return frame

def process_worker(
        func: Callable,
        frame: np.ndarray,
        box: tuple[float, float, float, float],
        storage: ThreadResult) -> None:
    try:
        text = func(frame, box)
        storage.put(text)
    except Exception as e:
        print(f"Worker error: {e}")

thread_storage = ThreadResult()
app = FastAPI()
PRODUCER_URL = "ws://localhost:8080/ws/video"
raw_q = asyncio.Queue(maxsize=1)
proc_q = asyncio.Queue(maxsize=1)

person = PersonTemplate()
model_processor = Model()

def heavy_logic(frame: np.ndarray) -> np.ndarray:
    start = time()
    frame = model_processor.check_camera(frame, person, message)
    frame = cv2.flip(frame, 1)
    message.print_text(frame)
    latency = int((time() - start) * 1000)
    cv2.putText(frame, f"{latency}ms", (10, frame.shape[0] - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    return frame

async def fetch():
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

async def process():
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
async def stream(ws: WebSocket):
    await ws.accept()
    t1 = asyncio.create_task(fetch())
    t2 = asyncio.create_task(process())
    try:
        while True:
            await ws.send_bytes(await proc_q.get())
    except Exception as e:
        print(f"Stream error: {e}")
    finally:
        t1.cancel()
        t2.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)