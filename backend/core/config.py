from enum import Enum
import os, numpy as np
from dotenv import load_dotenv

load_dotenv()

MODEL_DETECTION_PATH = os.getenv("MODEL_DETECTION_PATH")
MODEL_RECOGNITION_PATH = os.getenv("MODEL_RECOGNITION_PATH")
MODEL_ALIGNMENT_PATH = os.getenv("MODEL_ALIGNMENT_PATH")
IDEAL_PATH = os.getenv("IDEAL_PATH")
PRODUCER_URL = os.getenv("PRODUCER_URL")
THRESHOLD = 0.7
VECTOR_THRESHOLD = 0.5
CONFIDENCE = 0.4
MOTIONLESS_FRAME = 30

IDEAL_FACES = {
    "goshadorm.jpg": "Астанин Георгий Константинович",
    "ronnn.jpg": "Иванов Иван Иванович",
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

REFERENCE_LANDMARKS = np.array([
    [38.2946, 51.6963], [73.5318, 51.5014], 
    [56.0252, 71.7366], 
    [41.5493, 92.3655], [70.7299, 92.2041]
], dtype=np.float32)