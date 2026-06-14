import cv2
import numpy as np
import onnxruntime as ort
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import os

from core.config import IDEAL_PATH, VECTOR_THRESHOLD, IDEAL_FACES, MODEL_RECOGNITION_PATH
from core.decorators import safe_execute

class QdrantRecognizer:
    def __init__(self):
        # Явно душим попытки лезть в CUDA для лица, чтобы не триггерить ошибку DLL на хосте
        # В докере это тоже сэкономит видеопамять для YOLO
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        self.session = ort.InferenceSession(
            MODEL_RECOGNITION_PATH, 
            sess_options=opts,
            providers=['CPUExecutionProvider'] # Строго CPU, как у InsightFace
        )
        self.input_name = self.session.get_inputs()[0].name
        
        self.client = QdrantClient(":memory:")
        self.client.create_collection(
            collection_name="test",
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )
        self._load_ideal_vectors(IDEAL_PATH)
    
    @safe_execute()
    def _load_ideal_vectors(self, ideal_path: str) -> None:
        points = []
        for idx, (filename, full_name) in enumerate(IDEAL_FACES.items()):
            img_path = os.path.join(ideal_path, filename)
            img = cv2.imread(img_path)
            if img is None: continue
            
            vec = self._preprocess_face(img)
            points.append(PointStruct(
                id=idx,
                vector=vec.tolist(),
                payload={"name": full_name, "filename": filename}
            ))

        if points:
            self.client.upsert(collection_name="test", points=points)
    
    def _preprocess_face(self, face: np.ndarray) -> np.ndarray:
        # Полная копия логики InsightFace без сторонних либ
        face = cv2.resize(face, (112, 112))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        
        # Нормализация (127.5 и 128.0 как в твоих логах InsightFace)
        face = (face - 127.5) / 128.0
        face = face.astype(np.float32)
        
        # HWC -> CHW и добавляем размерность батча (1, 3, 112, 112)
        face = np.transpose(face, (2, 0, 1))
        blob = np.expand_dims(face, axis=0)
        
        # Инференс на CPU
        vec = self.session.run(None, {self.input_name: blob})[0][0]
        
        # L2 Нормализация вектора
        return vec / np.linalg.norm(vec)
    
    @safe_execute(default_return="Not defined")
    def scan(self, frame: np.ndarray, box: tuple) -> str:
        x1, y1, x2, y2 = map(int, box)
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        face = frame[y1:y2, x1:x2]
        if face.size == 0: return "Not defined"
        
        vec = self._preprocess_face(face)
        res = self.client.query_points(collection_name="test", query=vec.tolist(), limit=1).points
        
        if res and res[0].score > VECTOR_THRESHOLD:
            return res[0].payload.get("name")
        return "Not defined"