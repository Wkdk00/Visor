import cv2
import numpy as np
import onnxruntime as ort

from core.config import MODEL_ALIGNMENT_PATH, REFERENCE_LANDMARKS


class AlignmentModel:
    """Класс для детекции ключевых точек лица и его выравнивания.

    Использует YOLOv8-Face модель для поиска 5 ключевых точек лица
    (глаза, нос, углы рта) и применяет аффинное преобразование для
    получения канонического изображения лица размером 112x112,
    готового для подачи в модель распознавания.

    Attributes:
        session (ort.InferenceSession): ONNX Runtime сессия модели выравнивания.
        input_name (str): Имя входного тензора модели.
        input_shape (tuple): Размер входного изображения модели (H, W).
        arcface_dst (np.ndarray): Эталонные координаты 5 точек для ArcFace.
    """
    
    def __init__(self):
        self.session = ort.InferenceSession(
            MODEL_ALIGNMENT_PATH,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = tuple(map(int, self.session.get_inputs()[0].shape[2:]))
        self.arcface_dst = REFERENCE_LANDMARKS

    def _preprocess(self, frame: np.ndarray) -> tuple:
        """Выполняет предобработку кадра алгоритмом Letterbox для модели выравнивания.

        Масштабирует изображение с сохранением пропорций и добавляет серые отступы
        до размера, требуемого моделью. Возвращает нормализованный тензор и параметры
        для обратного масштабирования координат.

        Args:
            frame (np.ndarray): Исходный кадр в формате BGR.

        Returns:
            tuple: Подготовленный тензор изображения (np.ndarray), коэффициент масштабирования (float),
                отступ слева (float) и отступ сверху (float).
        """
        h, w = frame.shape[:2]
        new_h, new_w = self.input_shape
        
        scale = min(new_h / h, new_w / w)
        new_unpad = int(w * scale), int(h * scale)
        
        if (h, w) != tuple(new_unpad[::-1]):
            frame = cv2.resize(frame, new_unpad, interpolation=cv2.INTER_LINEAR)
        
        dw, dh = (new_w - new_unpad[0]) / 2, (new_h - new_unpad[1]) / 2
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        
        frame = cv2.copyMakeBorder(frame, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        blob = frame[..., ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
        
        return np.expand_dims(np.ascontiguousarray(blob), 0), scale, left, top

    def align(self, face_img: np.ndarray) -> np.ndarray | None:
        """Детектирует лицо, находит ключевые точки и выполняет аффинное выравнивание.

        Прогоняет кадр через YOLOv8-Face, извлекает 5 landmarks (глаза, нос, углы рта),
        вычисляет матрицу преобразования к стандартным координатам ArcFace и применяет
        warpAffine для получения канонического изображения лица.

        Args:
            face_img (np.ndarray): Исходный кадр в формате BGR.

        Returns:
            np.ndarray | None: Выровненное изображение лица размером 112x112 в формате BGR
        """
        tensor, scale, pad_w, pad_h = self._preprocess(face_img)
        outputs = self.session.run(None, {self.input_name: tensor})[0][0]
        
        boxes, confs = outputs[:, :4], outputs[:, 4]
        landmarks = outputs[:, 6:21].reshape(-1, 5, 3)[:, :, :2]
        
        mask = confs > 0.4
        boxes, confs, landmarks = boxes[mask], confs[mask], landmarks[mask]
        
        if not len(boxes):
            return None
        
        boxes[:, [0, 2]] = (boxes[:, [0, 2]] - pad_w) / scale
        boxes[:, [1, 3]] = (boxes[:, [1, 3]] - pad_h) / scale
        landmarks = (landmarks - np.array([pad_w, pad_h])) / scale
        
        indices = cv2.dnn.NMSBoxes(
            np.column_stack((boxes[:, 0], boxes[:, 1], boxes[:, 2] - boxes[:, 0], boxes[:, 3] - boxes[:, 1])).tolist(),
            confs.tolist(), 0.4, 0.4
        )
        
        if not len(indices):
            return None
        
        best_idx = max(indices.flatten(), key=lambda i: confs[i])
        best_landmarks = landmarks[best_idx]
        
        matrix = cv2.estimateAffinePartial2D(best_landmarks, self.arcface_dst, method=cv2.LMEDS)[0]
        if matrix is None:
            return None
        
        return cv2.warpAffine(face_img, matrix, (112, 112), borderMode=cv2.BORDER_REFLECT)