import cv2
import numpy as np
import onnxruntime as ort
from core.config import MODEL_DETECTION_PATH, CONFIDENCE
from core.decorators import safe_execute

class DetectionModel:
    """Класс-обёртка для YOLO ONNX модели детекции объектов."""
    def __init__(self):
        self.session = ort.InferenceSession(
            MODEL_DETECTION_PATH,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape[2:] 
        
        self.DICT_CLASSES = {
            0: ("face", (0, 255, 0)),
            1: ("cap", (255, 0, 0)),
            2: ("mask", (0, 0, 255)),
            3: ("glasses", (255, 255, 0)),
            4: ("badge", (255, 255, 255))
        }

    def _preprocess(self, frame: np.ndarray) -> tuple[np.ndarray, float, float, float]:
        """Выполняет предобработку кадра алгоритмом Letterbox и нормализацию.

        Args:
            frame (np.ndarray): Исходный кадр в BGR.

        Returns:
            tuple[np.ndarray, float, float, float]: Подготовленный тензор изображения, коэффициент масштабирования, отступ слева и отступ сверху.
        """
        shape = frame.shape[:2]
        new_shape = self.input_shape
        
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = (new_shape[1] - new_unpad[0]) / 2, (new_shape[0] - new_unpad[1]) / 2
        
        if shape[::-1] != new_unpad:
            frame = cv2.resize(frame, new_unpad, interpolation=cv2.INTER_LINEAR)
            
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        
        frame = cv2.copyMakeBorder(frame, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        
        # BGR -> RGB, HWC -> CHW, нормализация и принудительное выравнивание в памяти (КРИТИЧНО для ONNX)
        blob = frame[..., ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
        blob = np.ascontiguousarray(blob)
        
        return np.expand_dims(blob, axis=0), r, left, top

    def _postprocess(self, preds: np.ndarray, ratio: float, pad_w: float, pad_h: float) -> list[dict]:
        """Обрабатывает сырые предсказания модели, применяя фильтрацию и NMS.

        Args:
            preds (np.ndarray): Сырые предсказания, полученные от модели.
            ratio (float): Коэффициент масштабирования из этапа предобработки.
            pad_w (float): Значение отступа слева из этапа предобработки.
            pad_h (float): Значение отступа сверху из этапа предобработки.

        Returns:
            list[dict]: Список обнаруженных объектов с bbox, conf, cls.
        """
        boxes, scores = preds[:, :4], preds[:, 4:]
        class_ids = np.argmax(scores, axis=1)
        confs = np.max(scores, axis=1)
        
        # Фильтрация по уверенности
        mask = confs > CONFIDENCE
        boxes, confs, class_ids = boxes[mask], confs[mask], class_ids[mask]
        
        if len(boxes) == 0:
            return []

        # Возврат координат в масштаб исходного кадра (из [cx, cy, w, h] в [x1, y1, w, h])
        x1 = (boxes[:, 0] - boxes[:, 2] / 2 - pad_w) / ratio
        y1 = (boxes[:, 1] - boxes[:, 3] / 2 - pad_h) / ratio
        w  = boxes[:, 2] / ratio
        h  = boxes[:, 3] / ratio
        
        # Multi-class NMS: искусственно разносим классы, чтобы они не подавляли друг друга
        max_wh = 7680  # Константа из кода Ultralytics
        c = class_ids * max_wh
        x1_offset = x1 + c
        y1_offset = y1 + c
        
        nms_boxes = np.column_stack((x1_offset, y1_offset, w, h)).tolist()
        
        # Порог IoU 0.7 - это дефолт YOLOv8. 0.45 слишком жестко удалял рамки.
        indices = cv2.dnn.NMSBoxes(nms_boxes, confs.tolist(), CONFIDENCE, 0.7)
        
        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                results.append({
                    "bbox": np.array([x1[i], y1[i], x1[i] + w[i], y1[i] + h[i]]),
                    "conf": float(confs[i]),
                    "cls": int(class_ids[i])
                })
        return results

    @safe_execute(default_return=[])
    def predict(self, frame: np.ndarray) -> list[dict]:
        """Пайплайн детекции: препроцессинг -> инференс -> постпроцессинг.

        Args:
            frame (np.ndarray): Исходный кадр в BGR.

        Returns:
            list[Dict]: Список обнаруженных объектов с bbox, conf, cls.
        """
        tensor, ratio, pad_w, pad_h = self._preprocess(frame)
        preds = self.session.run(None, {self.input_name: tensor})[0][0].T
        return self._postprocess(preds, ratio, pad_w, pad_h)
    
    @safe_execute(default_return=None)
    def draw(
        self, 
        frame: np.ndarray, 
        boxes: list[dict[str, int | float]], 
        classes: list[int] = [0, 1, 2, 3, 4], 
        confidence: float = CONFIDENCE
    ) -> np.ndarray:
        """Отрисовывает bounding boxes на кадре.

        Args:
            frame (np.ndarray): Исходный кадр.
            boxes (List[Dict]): Список объектов для отрисовки.
            classes (List[int]): Список классов для фильтрации.
            confidence (float): Порог уверенности для отрисовки.

        Returns:
            np.ndarray: Кадр с отрисованными bounding boxes.
        """
        for box in boxes:
            if box["cls"] in classes and box["conf"] > confidence:
                x1, y1, x2, y2 = map(int, box["bbox"])
                cv2.rectangle(frame, (x1, y1), (x2, y2), self.DICT_CLASSES[box["cls"]][1], 3)
        return frame