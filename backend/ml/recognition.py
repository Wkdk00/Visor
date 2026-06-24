import onnxruntime as ort
import cv2
import numpy as np

from core.config import MODEL_RECOGNITION_PATH
from core.decorators import safe_execute

class RecognitionModel:
    """Класс-обёртка для INSIGHTFACE ONNX модели распознавания лиц."""
    def __init__(self):
        self.session = ort.InferenceSession(
            MODEL_RECOGNITION_PATH, 
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name

    @safe_execute(default_return=np.zeros(512, dtype=np.float32))
    def preprocess_face(self, face: np.ndarray) -> np.ndarray:
        """Выполняет препроцессинг изображения лица и извлекает векторный эмбеддинг.

        Args:
            face (np.ndarray): Изображение лица (BGR).

        Returns:
            np.ndarray: Векторный эмбеддинг лица.
        """
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

        face = cv2.resize(face, (112, 112))
        face = (face - 127.5) / 128.0
        face = face.astype(np.float32)

        face = np.transpose(face, (2, 0, 1))

        input_tensor = face[None, ...]
        vec = self.session.run(None, {self.input_name: input_tensor})[0][0]
        vec = vec / np.linalg.norm(vec)
        return vec