import cv2, os, numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from core.config import IDEAL_PATH, VECTOR_THRESHOLD, IDEAL_FACES
from core.decorators import safe_execute
from ml.recognition import RecognitionModel

class QdrantRecognizer:
    """Распознавание лиц на базе модели InsightFace с векторным поиском в Qdrant.
    
    Класс инициализирует модель детекции лиц, создаёт векторную базу данных
    с эталонными изображениями сотрудников и предоставляет метод для поиска
    совпадений в реальном времени.
    
    Attributes:
        recognizer: Модель InsightFace для извлечения эмбеддингов лиц.
        client: Клиент Qdrant для хранения и поиска векторов.
        IDEAL_PATH: Путь к директории с эталонными изображениями.
    """
    def __init__(self):
        self.recognizer = RecognitionModel()
        self.client = QdrantClient(host="qdrant", port=6333)
        if not self.client.collection_exists(collection_name="test"):
            self.client.create_collection(
                collection_name="test",
                vectors_config=VectorParams(size=512, distance=Distance.COSINE)
            )
            
            self.IDEAL_PATH = IDEAL_PATH
            self._load_ideal_vectors(self.IDEAL_PATH)
    
    @safe_execute()
    def _load_ideal_vectors(self, ideal_path: str) -> None:
        """Загружает и векторизует эталонные изображения сотрудников.
        
        Args:
            ideal_path (str): Путь к папке с идеальными изображениями.
        """
        points = []
        for idx, (filename, full_name) in enumerate(IDEAL_FACES.items()):
            img_path = os.path.join(ideal_path, filename)
            img = cv2.imread(img_path)

            vec = self.recognizer.preprocess_face(img)
            
            points.append(PointStruct(
                id=idx,
                vector=vec, 
                payload={"name": full_name, "filename": filename}
            ))

        self.client.upsert(collection_name="test", points=points)
    
    @safe_execute(default_return="Not defined")
    def scan(self, frame: np.ndarray, box: tuple[float, float, float, float]) -> str:
        """Векторизует лицо по рамке и ищет совпадение в базе.

        Args:
            frame: Кадр с видеопотока (BGR)
            box: Рамка лица (x1, y1, x2, y2)

        Returns:
            ФИО сотрудника или "Not defined"
        """
        # Crop лица по рамке
        x1, y1, x2, y2 = map(int, box)
        face = frame[y1:y2, x1:x2]
        
        # Препроцессинг
        vec = self.recognizer.preprocess_face(face)
        
        # Поиск в Qdrant
        res = self.client.query_points(collection_name="test", query=vec, limit=1).points

        # Возврат результата по порогу схожести
        if res and res[0].score > VECTOR_THRESHOLD:
            return res[0].payload.get("name")
        return "Not defined"