import cv2
import numpy as np
import asyncio
import threading
import sqlite3
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
import httpx  # pip install httpx

# Ваши импорты
from ultralytics import YOLO
from Levenshtein import ratio
from utils import class_count, check_motionless, check_PPE_intersections
from message import TextArea
from qdrant import QdrantRecognizer
import pytesseract

# ==========================================
# 1. ВАША БИЗНЕС-ЛОГИКА (Без изменений)
# ==========================================

connection = sqlite3.connect('Employee.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, post TEXT NOT NULL)''')
connection.commit()
# ... ваши INSERT ...

def ocr(frame: np.ndarray, box: tuple) -> str:
    frame = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, frame = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(frame, lang='rus')
    return text.replace("\n", " ")

def search_post(name: str) -> str:
    cursor.execute("SELECT post FROM Users WHERE name = ? LIMIT 1", (name,))
    result = cursor.fetchone()
    return result[0] if result else ""

class ThreadResult:
    def __init__(self): self.text = None; self.lock = threading.Lock()
    def put(self, text):
        with self.lock: self.text = text
    def get_and_clear(self):
        with self.lock:
            if self.text: res = self.text; self.text = None; return res
            return None

class PersonTemplate:
    def __init__(self):
        self.vector_name = ""; self.vector_post = ""; self.OCR_name = ""
        self.STATE_DICT = {0:"unregistered", 1:"vectorized", 2:"ocr", 3:"verify", 4:"error"}
        self.THRESHOLD = 0.7
        self.ALPHABET = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"
    
    def state(self) -> str:
        if not self.vector_name and not self.OCR_name: return self.STATE_DICT[0]
        elif self.vector_name and not self.OCR_name: return self.STATE_DICT[1]
        elif self.vector_name and self.OCR_name: return self.STATE_DICT[2]
        return self.STATE_DICT[3]
    
    def clear(self): self.vector_name = ""; self.OCR_name = ""; self.vector_post = ""
    def set_vector_name(self, n): self.vector_name = n
    def set_ocr_name(self, n):
        self.OCR_name = "".join(s for s in n if s in self.ALPHABET)
    def comparsion_vector_ocr(self) -> bool:
        self.vector_post = search_post(self.vector_name)
        employee = (self.vector_post + self.vector_name).replace(" ", "")
        return ratio(employee, self.OCR_name) > self.THRESHOLD

class Model:
    def __init__(self):
        self.model = YOLO(r'C:\Users\Админ\Desktop\python\cv\runs\detect\train4\weights\best.pt')
        self.counter = 0; self.ex = False; self.FREQUENCY = 45
        self.DICT_CLASSES = {0:("face",(0,255,0)), 1:("cap",(255,0,0)), 2:("mask",(0,0,255)), 3:("glasses",(255,255,0)), 4:("badge",(255,255,255))}

    def predict_yolo(self, frame):
        pred = self.model(frame, verbose=False)
        boxes = pred[0].boxes
        results = []
        for i in range(len(boxes)):
            if boxes.conf[i] > 0.4:
                results.append({"bbox": boxes.xyxy[i].cpu().numpy(), "conf": boxes.conf[i].cpu().numpy(), "cls": int(boxes.cls[i].cpu().numpy())})
                self.ex = True
        return results

    def draw_rectangles(self, frame, boxes, classes=[0,1,2,3,4], confidence=0.4):
        for box in boxes:
            if box["cls"] in classes and box["conf"] > confidence:
                x1,y1,x2,y2 = map(int, box["bbox"])
                cv2.rectangle(frame, (x1,y1), (x2,y2), self.DICT_CLASSES[box["cls"]][1], 3)
        return frame

    def check_camera(self, frame):
        # Ваша логика частоты кадров
        if self.ex or self.counter == self.FREQUENCY:
            objects = self.predict_yolo(frame)
            frame = self.draw_rectangles(frame, objects)
            self.counter = 0
            if message.empty(): self.detect_pipeline(frame, objects)
        self.counter += 1
        return frame

    def detect_pipeline(self, frame, objects):
        count_objects, length = class_count(objects)
        if person.state() == "unregistered":
            if count_objects[0] > 1: message.add_text("There must be only 1 person", "alert")
            if not check_PPE_intersections(objects): message.add_text("Please remove the PPE", "alert")
            else:
                p_box = [b for b in objects if b["cls"]==0][0]["bbox"]
                if check_motionless(p_box):
                    threading.Thread(target=process_worker, args=(qdrant.scan, frame, p_box, thread_storage)).start()
            if name := thread_storage.get_and_clear():
                message.add_text(name, "name"); person.set_vector_name(name)
        elif person.state() == "vectorized":
            if count_objects[4] == 1:
                b_box = [b for b in objects if b["cls"]==4][0]["bbox"]
                if check_motionless(b_box):
                    threading.Thread(target=process_worker, args=(ocr, frame, b_box, thread_storage)).start()
            if ocr_name := thread_storage.get_and_clear():
                person.set_ocr_name(ocr_name); message.add_text(ocr_name, "name")
        elif person.state() == "ocr":
            if person.comparsion_vector_ocr(): message.add_text("success", "notice")
            else: message.add_text("error", "alert")
            person.clear()

def process_worker(func, frame, box, storage):
    storage.put(func(frame, box))

# ==========================================
# 2. АСИНХРОННЫЙ КОНВЕЙЕР (Low Latency)
# ==========================================

app = FastAPI()
PRODUCER_URL = "http://localhost:8080/video"

# Очереди с размером 1 = всегда обрабатываем только последний кадр
raw_queue = asyncio.Queue(maxsize=1)
processed_queue = asyncio.Queue(maxsize=1)

# Глобальные экземпляры
model = Model()
qdrant = QdrantRecognizer()
message = TextArea()
person = PersonTemplate()
thread_storage = ThreadResult()

async def capture_task():
    """Фон: Скачивает кадры и кладет ТОЛЬКО самый свежий в raw_queue"""
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', PRODUCER_URL) as resp:
            buffer = b''
            async for chunk in resp.aiter_bytes(chunk_size=1024):
                buffer += chunk
                start = buffer.find(b'\xff\xd8')
                end = buffer.find(b'\xff\xd9')
                if start != -1 and end != -1:
                    jpg = buffer[start:end+2]
                    buffer = buffer[end+2:]
                    
                    # Frame Skipping: если очередь полна, выкидываем старый кадр
                    if raw_queue.full():
                        try: raw_queue.get_nowait()
                        except asyncio.QueueEmpty: pass
                    await raw_queue.put(jpg)

def heavy_processing_sync(jpg_bytes: bytes) -> bytes:
    """Sync функция: декодирует, обрабатывает YOLO, кодирует обратно"""
    # 1. Decode
    frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None: return None
    
    # 2. Process (Ваша логика)
    frame = model.check_camera(frame)
    
    # 3. Post-process
    frame = cv2.flip(frame, 1)
    message.print_text(frame)
    
    # 4. Encode (Снижаем качество до 75 для скорости сети)
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return buf.tobytes()

async def processing_worker():
    """Фон: Берет сырые кадры, обрабатывает в threadpool, кладет результат"""
    while True:
        jpg = await raw_queue.get()
        # Выносим CPU-bound задачу в отдельный поток, чтобы не блокировать asyncio
        result = await run_in_threadpool(heavy_processing_sync, jpg)
        
        if result:
            # Frame Skipping на выходе: если клиент не успевает, выкидываем старый результат
            if processed_queue.full():
                try: processed_queue.get_nowait()
                except asyncio.QueueEmpty: pass
            await processed_queue.put(result)
        raw_queue.task_done()

async def gen_stream():
    """Генератор для FastAPI: отдает готовые байты"""
    # Запускаем фоновые задачи
    asyncio.create_task(capture_task())
    asyncio.create_task(processing_worker())
    
    while True:
        # Ждем готовый обработанный кадр
        frame_bytes = await processed_queue.get()
        if frame_bytes:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        processed_queue.task_done()

@app.get("/processed")
async def processed():
    return StreamingResponse(gen_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    import uvicorn
    # http/2 может помочь с мультипарт стримингом
    uvicorn.run(app, host="0.0.0.0", port=8081, http='h11')