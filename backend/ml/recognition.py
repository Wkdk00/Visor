import cv2
import numpy as np
import onnxruntime as ort

from core.config import MODEL_RECOGNITION_PATH
from core.decorators import safe_execute
from ml.alignment import AlignmentModel


class RecognitionModel:
    """Класс-обёртка для распознавания лиц с автоматическим выравниванием.

    Объединяет две ONNX модели: AlignmentModel для детекции ключевых точек
    и аффинного выравнивания лица, и основную модель распознавания для
    извлечения биометрического эмбеддинга.

    Attributes:
        rec_session (ort.InferenceSession): ONNX Runtime сессия модели распознавания.
        rec_input_name (str): Имя входного тензора модели распознавания.
        aligner (AlignmentModel): Экземпляр модели выравнивания лиц.
    """
    
    def __init__(self):
        self.rec_session = ort.InferenceSession(
            MODEL_RECOGNITION_PATH,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.rec_input_name = self.rec_session.get_inputs()[0].name
        self.aligner = AlignmentModel()

    @safe_execute(default_return=np.zeros(512, dtype=np.float32))
    def preprocess_face(self, face: np.ndarray) -> np.ndarray:
        """Метод предобратки и векторизации лица.
        
        С помощью Модели выравнивания, лицо приводится к размеру 112x112 и основные ориентиры лица (глаза, нос, рот)
        выравниваются под нужный шаблон. После чего, выравненное лицо передается в модель распознавания для получения вектора признаков.

        Args:
            face (np.ndarray): Изображение лица в формате BGR.

        Returns:
            np.ndarray: Вектор признаков лица размерности 512.
        """
        aligned_face = self.aligner.align(face) if self.aligner else None
        
        if aligned_face is None:
            aligned_face = cv2.resize(face, (112, 112))
        
        aligned_rgb = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2RGB)
        input_tensor = (np.transpose(aligned_rgb.astype(np.float32), (2, 0, 1)) - 127.5) / 128.0
        vec = self.rec_session.run(None, {self.rec_input_name: input_tensor[None, ...]})[0][0]
        
        return vec / np.linalg.norm(vec)