from ultralytics import YOLO
import cv2, numpy as np
from Levenshtein import ratio
from utils import class_count, check_motionless, check_PPE_intersections
from message import TextArea
from qdrant import QdrantRecognizer
from ocr import ocr
import sqlite3
from time import time
import threading

connection = sqlite3.connect('Employee.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INTEGER PRIMARY KEY,
name TEXT NOT NULL,
post TEXT NOT NULL
)
''')

connection.commit()

cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', (1, 'Астанин Георгий Константинович', 'УЧАСТНИК'))
cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', (2, 'Кудрин Ролан Михайлович', 'УЧАСТНИК'))
cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', (3, 'Богомолова Ева Анатольевна', 'УЧАСТНИК'))
cursor.execute('INSERT INTO Users (id, name, post) VALUES (?, ?, ?)', (4, 'Вразовский Владислав Александрович', 'ЭКСПЕРТ'))

def process_worker(func, frame, box, storage):
    text = func(frame, box)
    storage.put(text)

def search_post(name: str) -> str:
    """Функция для поиска должности сотрудника по ФИО
    в базе данных.

    Args:
        name (str): ФИО сотрудника

    Returns:
        str: Должность сотрудника
    """
    cursor.execute("SELECT post FROM Users WHERE name = ? LIMIT 1", (name,))
    result = cursor.fetchone()
    return result[0] if result else ""

class ThreadResult:
    def __init__(self):
        self.text = None
        self.lock = threading.Lock()

    def put(self, text: str):
        with self.lock:
            self.text = text

    def get_and_clear(self):
        with self.lock:
            if self.text:
                res = self.text
                self.text = None
                return res
            return None

class PersonTemplate:
    """Класс для управления состоянием идентификации сотрудника.

    Реализует логику многоэтапной верификации личности, объединяя данные 
    от распознавания лица (векторная база) и OCR (чтение бейджа). 
    Отслеживает текущий этап обработки через конечный автомат состояний 
    (STATE_DICT) и выполняет финальное сравнение данных для подтверждения 
    личности.

    Workflow:
        1. unregistered - начальное состояние, данных нет.
        2. vectorized - получено имя из распознавания лица.
        3. ocr - получено имя с бейджа (OCR).
        4. verify - данные сверены, личность подтверждена.
        5. error - критическая ошибка обработки.

    Attributes:
        vector_name (str): ФИО сотрудника из векторной базы (face recognition).
        vector_post (str): Должность сотрудника из реляционной БД.
        OCR_name (str): ФИО сотрудника, распознанное с бейджа (OCR).
        STATE_DICT (dict): Маппинг кодов состояний в текстовые описания.
        THRESHOLD (float): Порог схожести строк для подтверждения личности (0.7).
        ALPHABET (str): Валидные символы для OCR.
    """
    def __init__(self):
        self.vector_name = ""
        self.vector_post = ""
        self.OCR_name = ""
        self.STATE_DICT = {0:"unregistered", 1:"vectorized", 2:"ocr", 3:"verify", 4:"error"}
        self.THRESHOLD = 0.7
        self.ALPHABET = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

    def state(self) -> str:
        """Метод для получения текущего состояния обработки.

        Returns:
            str: Одно из значений: 'unregistered', 'vectorized', 'ocr', 'verify', 'error'.
        """
        len_vec = len(self.vector_name)
        len_ocr = len(self.OCR_name)
        if len_vec == 0 and len_ocr == 0:
            return self.STATE_DICT[0]
        elif len_vec > 0 and len_ocr == 0:
            return self.STATE_DICT[1]
        elif len_vec > 0 and len_ocr > 0:
            return self.STATE_DICT[2]
        return self.STATE_DICT[3]
    
    def clear(self) -> None:
        """
        Метод для очистки информации о текущем работнике
        """
        self.vector_name = ""
        self.OCR_name = ""
        self.vector_post = ""

    def set_vector_name(self, vec_name: str) -> None:
        """Метод для добавления ФИО работника,
        полученного с помощью распознавания лица
        (из векторной базы данных).

        Args:
            vec_name (str): ФИО работника
        """
        self.vector_name = vec_name

    def set_ocr_name(self, ocr_name: str):
        """Метод для добавления ФИО работника,
        полученного с бейджа (OCR). Сразу убраны
        лишние символы, которые могли возникнуть из-за OCR

        Args:
            ocr_name (str): ФИО работника
        """
        self.OCR_name = ""
        for symbol in ocr_name:
            if symbol in self.ALPHABET:
                self.OCR_name += symbol

    def comparsion_vector_ocr(self) -> bool:
        """Метод для сравнения ФИО из векторной БД
        и ФИО с бейджа. С бейджа был получен текст вида
        СОТРУДНИКИвановИванИванович. Для получения должности
        из распознавания лица возьмем должность из реляционной БД.

        Returns:
            bool: True если личность подтверждена иначе False
        """
        self.vector_post = search_post(self.vector_name)
        employee = (self.vector_post + self.vector_name).replace(" ", "")
        compare = ratio(employee, self.OCR_name)
        if compare > self.THRESHOLD:
            return True
        return False


class Model:
    def __init__(self):
        self.model = YOLO(r'C:\Users\Админ\Desktop\python\cv\runs\detect\train4\weights\best.pt')
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
        xyxy = boxes.xyxy.cpu().numpy()
        conf = boxes.conf.cpu().numpy()
        cls = boxes.cls.cpu().numpy()
        results = []
        for i in range(len(boxes)):
            if conf[i] > 0.4:
                results.append({
                    "bbox": xyxy[i],
                    "conf": conf[i],
                    "cls": int(cls[i])
                })
                self.ex = True
        return results

    def draw_rectangles(
            self,
            frame: np.ndarray,
            boxes: list[dict],
            classes: list = [0, 1, 2, 3, 4],
            confidence: float = 0.4) -> np.ndarray:
        for box in boxes:
            x1, y1, x2, y2 = box["bbox"]
            conf = box["conf"]
            cls = box["cls"]
            if cls in classes and conf>confidence:
                cv2.rectangle(frame,(int(x1),int(y1)), (int(x2),int(y2)), self.DICT_CLASSES[cls][1], 3)
        return frame

    def check_camera(self, frame: np.ndarray) -> None:
        if self.ex == True or self.counter == self.FREQUENCY:
            objects = self.predict_yolo(frame)
            frame = self.draw_rectangles(frame, objects)
            self.counter = 0
            if message.empty():
                self.detect_pipeline(frame, objects)
        self.counter += 1

    def detect_pipeline(self, frame: np.ndarray, objects: list[dict]) -> None:
        count_objects, length = class_count(objects)
        if person.state() == "unregistered":
            if count_objects[0] > 1:
                message.add_text(text="There must be only 1 person in the camera", type="alert")
            if not check_PPE_intersections(objects):
                message.add_text(text="Please remove the PPE", type="alert")
            else:
                person_bbox = [box for box in objects if box["cls"] == 0][0]["bbox"]
                scanner = check_motionless(person_bbox)
                if scanner:
                    threading.Thread(target=process_worker, args=(qdrant.scan, frame, person_bbox, thread_storage)).start()

            name = thread_storage.get_and_clear()
            if name:
                message.add_text(text=name, type="name")
                person.set_vector_name(name)
    
        elif person.state() == "vectorized":
            if count_objects[4] == 1:
                badge_bbox = [box for box in objects if box["cls"] == 4][0]["bbox"]
                scanner = check_motionless(badge_bbox)
                if scanner:
                    threading.Thread(target=process_worker, args=(ocr, frame, badge_bbox, thread_storage)).start()

            ocr_name = thread_storage.get_and_clear()
            if ocr_name:
                person.set_ocr_name(ocr_name)
                print(ocr_name)
                message.add_text(text=ocr_name, type="name")

        elif person.state() == "ocr":
            if person.comparsion_vector_ocr():
                message.add_text(text="success", type="notice")
                person.clear()
            else:
                message.add_text(text="error", type="alert")
                person.clear()


cap = cv2.VideoCapture(0)
model = Model()
qdrant = QdrantRecognizer()
message = TextArea()
person = PersonTemplate()
thread_storage = ThreadResult()
while True:
    start = time()
    ret, frame = cap.read()
    if not ret: break
    model.check_camera(frame)
    key = cv2.waitKey(1) & 0xFF
    frame = cv2.flip(frame, 1)
    message.print_text(frame)
    end = time()
    print(int((end - start) * 1000))
    cv2.imshow('Webcamera', frame)
    if key == ord('q'): break

connection.close()
cap.release()
cv2.destroyAllWindows()