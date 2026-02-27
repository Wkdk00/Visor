from enum import Enum


MODEL_PATH = r'C:\Users\Админ\Desktop\python\cv\runs\detect\train4\weights\best.pt'
IDEAL_PATH = r"C:\tmp\ideal"
PRODUCER_URL = "ws://localhost:8080/ws/video"
THRESHOLD = 0.7
VECTOR_THRESHOLD = 0.95
CONFIDENCE = 0.4

IDEAL_FACES = {
    "goshadorm.jpg": "Астанин Георгий Константинович",
    "ron.jpg": "Иванов Иван Иванович",
    "eva.jpg": "Андреев Андрей Андреевич",
    "vlad.jpg": "Петров Петр Петрович"
}

class ClassesNames:
    CLASS_PERSON = 0
    CLASS_CAP = 1
    CLASS_MASK = 2
    CLASS_GLASSES = 3
    CLASS_BADGE = 4


class PersonStates(Enum):
    UNREGISTERED = "unregistered"
    VECTORIZED = "vectorized"
    OCR_READY = "ocr"
    ERROR = "error"