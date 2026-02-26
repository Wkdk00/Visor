from insightface.app import FaceAnalysis
import cv2, os, numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

class QdrantRecognizer:
    """Распознавание лиц на базе InsightFace с векторным поиском в Qdrant.
    
    Класс инициализирует модель детекции лиц, создаёт векторную базу данных
    с эталонными изображениями сотрудников и предоставляет метод для поиска
    совпадений в реальном времени.
    
    Attributes:
        recognizer: Модель InsightFace для извлечения эмбеддингов лиц.
        client: Клиент Qdrant для хранения и поиска векторов.
        IDEAL_PATH: Путь к директории с эталонными изображениями.
    """
    def __init__(self):
        app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(320, 320))
        self.recognizer = app.models['recognition']
        
        self.client = QdrantClient(":memory:")
        self.client.create_collection(
            collection_name="test",
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )
        
        self.IDEAL_PATH = r"C:\tmp\ideal"
        self._load_ideal_vectors(self.IDEAL_PATH)
    
    def _load_ideal_vectors(self, ideal_path: str):
        """Загружает и векторизует эталонные изображения сотрудников."""
        
        vectors = []
        names = [
            "Астанин Георгий Константинович",
            "Кудрин Ролан Михайлович",
            "Богомолова Ева Анатольевна",
            "Вразовский Владислав Александрович"
        ]
        
        for filename in ['goshadorm.jpg', 'ron.jpg', 'eva.jpg', 'vlad.jpg']:
            img_path = os.path.join(ideal_path, filename)
            img = cv2.imread(img_path)

            vec = self._preprocess_face(img)
            
            vectors.append(vec)
        
        # Upsert в Qdrant
        self.client.upsert(collection_name="test", points=[
            PointStruct(id=i+1, vector=vectors[i], payload={"name": names[i]})
            for i in range(len(vectors))
        ])
    
    def _preprocess_face(self, face: np.ndarray) -> np.ndarray:
        """Выполняет препроцессинг изображения лица и извлекает векторный эмбеддинг.

        Args:
            face (np.ndarray): Изображение лица (BGR).

        Returns:
            np.ndarray: Векторный эмбеддинг лица.
        """
        face = cv2.resize(face, (112, 112))
        face = (face - 127.5) / 128.0
        face = face.astype(np.float32)
        face = np.transpose(face, (2, 0, 1))
        vec = self.recognizer.forward(face[None, ...])[0]
        vec = vec / np.linalg.norm(vec)
        return vec
    
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
        vec = self._preprocess_face(face)
        
        # Поиск в Qdrant
        res = self.client.query_points(collection_name="test", query=vec, limit=1).points
        
        # Возврат результата по порогу схожести
        if res and res[0].score > 0.95:
            return res[0].payload.get("name")
        return "Not defined"