from ultralytics import YOLO
import cv2, numpy as np
from app.config import MODEL_PATH, CONFIDENCE
from app.decorators import safe_execute

class Model:
    """Класс-обёртка для YOLO модели детекции объектов.
    
    Предоставляет методы для предсказания и визуализации результатов.
    
    Attributes:
        model: Загруженная YOLO модель.
        DICT_CLASSES: Словарь классов для отрисовки {id: (name, color)}.
    """
    def __init__(self):
        self.model = YOLO(MODEL_PATH)
        self.DICT_CLASSES = {
            0:("face", (0, 255, 0)),
            1:("cap", (255, 0, 0)),
            2:("mask", (0, 0, 255)),
            3:("glasses", (255, 255, 0)),
            4:("badge", (255, 255, 255))
        }

    @safe_execute(default_return=[])
    def predict(self, frame: np.ndarray) -> list[dict]:
        """Выполняет предсказание объектов на кадре.

        Args:
            frame (np.ndarray): Исходный кадр в BGR.

        Returns:
            list[Dict]: Список обнаруженных объектов с bbox, conf, cls.
        """
        pred = self.model(frame, verbose=False, conf=CONFIDENCE)
        boxes = pred[0].boxes
        results = []
        for i in range(len(boxes)):
            results.append({
                "bbox": boxes.xyxy[i].cpu().numpy(),
                "conf": boxes.conf[i].cpu().numpy(),
                "cls": int(boxes.cls[i].cpu().numpy())
            })
        return results
    
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