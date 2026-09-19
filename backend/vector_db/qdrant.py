import cv2, os, numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from core.config import IDEAL_PATH, VECTOR_THRESHOLD, CHUNK_SIZE
from core.decorators import safe_execute
from ml import RecognitionModel
from repositories import get_employees_count, get_employees_for_vector_init

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
            self._load_ideal_vectors()
    
    @safe_execute()
    async def _load_ideal_vectors(self) -> None:
        """Загружает и векторизует эталонные изображения сотрудников.
        
        Args:
            ideal_path (str): Путь к папке с идеальными изображениями.
        """
        total = await get_employees_count()

        points_batch = list()

        for offset in range(0, total, CHUNK_SIZE):
            employees = await get_employees_for_vector_init(offset, CHUNK_SIZE)
            
            for emp_id, full_name, photo_path in employees:
                if photo_path is None:
                    print(f"️ {full_name} (id={emp_id}) без фото")
                    continue
                
                img = cv2.imread(photo_path)
                if img is None:
                    print(f"Не удалось загрузить фото для {full_name}")
                    continue
                
                vec = self.recognizer.preprocess_face(img)
                
                points_batch.append(PointStruct(
                    id=emp_id,
                    vector=vec,
                    payload={"name": full_name}
                ))

            if points_batch:
                self.client.upsert(collection_name="test", points=points_batch)
                points_batch.clear()
    
    @safe_execute(default_return="Not defined")
    def scan(self, frame: np.ndarray, box: tuple[float, float, float, float]) -> str:
        """Векторизует лицо по рамке и ищет совпадение в базе.

        Args:
            frame: Кадр с видеопотока (BGR)
            box: Рамка лица (x1, y1, x2, y2)

        Returns:
            ФИО сотрудника или "Not defined"
        """
        # Препроцессинг
        vec = self.recognizer.preprocess_face(frame)
        
        # Поиск в Qdrant
        res = self.client.query_points(collection_name="test", query=vec, limit=1).points

        # Возврат результата по порогу схожести
        if res and res[0].score > VECTOR_THRESHOLD:
            return res[0].payload.get("name")
        return "Not defined"