from __future__ import annotations

import threading, numpy as np
from typing import Callable, TYPE_CHECKING

from app.config import ClassesNames, PersonStates
from app.decorators import safe_execute
from app.ocr import ocr
from app.utils import class_count, check_motionless, check_PPE_intersections

if TYPE_CHECKING:
    from app.message import TextArea
    from app.model_detection import Model
    from app.person import PersonTemplate
    from app.thread_storage import ThreadResult
    from app.qdrant import QdrantRecognizer

class Pipeline:
    """Основной конвейер обработки видеопотока.
    
    Управляет частотой кадров, маршрутизирует логику по состояниям человека
    и координирует работу моделей детекции, распознавания лиц и OCR.
    
    Attributes:
        model: YOLO модель детекции объектов.
        message: UI компонент для отображения сообщений.
        person: Объект состояния идентификации сотрудника.
        storage: Потокобезопасное хранилище результатов.
        vec_DB: Qdrant клиент для векторного поиска лиц.
    """
    def __init__(
            self,
            model: Model,
            message: TextArea,
            storage: ThreadResult,
            person: PersonTemplate, 
            vec_DB: QdrantRecognizer):
        self.model = model
        self.message = message
        self.person = person
        self.storage = storage
        self.vec_DB = vec_DB
        self.counter = 0
        self.ex = False
        self.FREQUENCY = 45

    @safe_execute(default_return=None)
    def check_camera(self, frame: np.ndarray) -> np.ndarray | None:
        """Метод для оптимизации пайплайна.

        Запускаем YOLO-модель только раз в 1.5 секунды (FREQUENCY)
        либо если что-то распознали на прошлом кадре.

        Args:
            frame (np.ndarray): Исходный кадр видеопотока.

        Returns:
            np.ndarray | None: Обработанный кадр.
        """
        if self.ex or self.counter == self.FREQUENCY:
            objects = self.model.predict(frame)
            frame = self.model.draw(frame, objects)
            self.counter = 0
            self.ex = True
            if self.message.empty() and len(objects):
                frame = self.detect_pipeline(frame, objects)
        else:
            self.ex = False
            self.counter += 1
        return frame

    @safe_execute(default_return=None)
    def detect_pipeline(
        self,
        frame: np.ndarray,
        objects: list[dict[str, int | float]]
        ) -> np.ndarray | None:
        """Маршрутизирует логику обработки в зависимости от состояния обработки.

        Args:
            frame (np.ndarray): Исходный кадр.
            objects (list[dict]): Список обнаруженных объектов.

        Returns:
            np.ndarray | None: Обработанный кадр.
        """
        counts, _ = class_count(objects)
        
        if self.person.state() == PersonStates.UNREGISTERED:
            self._handle_unregistered(counts, objects, frame)

        elif self.person.state() == PersonStates.VECTORIZED:
            self._handle_vectorized(counts, objects, frame)

        elif self.person.state() == PersonStates.OCR_READY:
            self._handle_ocr_ready()
        
        return frame
    
    @safe_execute()
    def _handle_unregistered(
        self, 
        counts: dict[int, int], 
        objects: list[dict[str, int | float]], 
        frame: np.ndarray
    ) -> None:
        """Обрабатывает состояние UNREGISTERED (первичная регистрация лица).

        Проверяет количество людей в кадре, наличие СИЗ и при успешной 
        валидации запускает процесс векторизации лица для регистрации.

        Args:
            counts (dict[int, int]): Словарь с количеством объектов по классам.
            objects (list[dict]): Список обнаруженных объектов.
            frame (np.ndarray): Исходный кадр.
        """
        if counts[ClassesNames.CLASS_PERSON] > 1:
            self.message.add_text("There must be only 1 person in the camera", "alert")
        elif not check_PPE_intersections(objects):
            self.message.add_text("Please remove the PPE", "alert")
        else:
            self._process_main_bbox(frame, objects, ClassesNames.CLASS_PERSON, self.vec_DB.scan)
                
        self._check_storage(ClassesNames.CLASS_PERSON)

    @safe_execute()
    def _handle_vectorized(self, 
        counts: dict[int, int], 
        objects: list[dict[str, int | float]], 
        frame: np.ndarray
    ) -> None:
        """Обрабатывает состояние VECTORIZED (сканирование бейджа).

        При обнаружении ровно одного бейджа запускает OCR для распознавания
        текста с идентификатора сотрудника.

        Args:
            counts (dict[int, int]): Словарь с количеством объектов по классам.
            objects (list[dict]): Список обнаруженных объектов.
            frame (np.ndarray): Исходный кадр.
        """
        if counts[ClassesNames.CLASS_BADGE] == 1:
            self._process_main_bbox(frame, objects, ClassesNames.CLASS_BADGE, ocr)
        
        self._check_storage(ClassesNames.CLASS_BADGE)

    @safe_execute()
    def _handle_ocr_ready(self) -> None:
        """Обрабатывает состояние OCR_READY (финальная верификация).

        Выполняет сравнение данных из векторной базы (лицо) и OCR (бейдж).
        По результату сравнения выводит SUCCESS или ERROR, затем очищает
        состояние сотрудника для следующего цикла регистрации.
        """
        if self.person.comparison_vector_ocr():
            self.message.add_text("SUCCESS", "notice")
        else:
            self.message.add_text("ERROR", "alert")
        self.person.clear()

    @safe_execute()
    def _check_storage(self, current_cls: int) -> None:
        """Проверяет и обрабатывает результаты из потокобезопасного хранилища.

        Извлекает результат асинхронной обработки (распознавание лица или OCR),
        обновляет соответствующие поля сотрудника и выводит имя в интерфейс.
        После чтения хранилище автоматически очищается.
        
        Args:
            current_cls (int): Класс объекта для обработки (PERSON или BADGE).
        """
        name = self.storage.get_and_clear()
        if name and current_cls == ClassesNames.CLASS_PERSON:
            self.person.set_vector_name(name)
            self.message.add_text(name, "name")
        elif name and current_cls == ClassesNames.CLASS_BADGE:
            self.person.set_ocr_name(name)
            self.message.add_text(name, "name")

    @safe_execute()
    def _process_main_bbox(
        self,
        frame: np.ndarray,
        objects: list[dict[str, int | float]],
        current_cls: int,
        function: Callable) -> None:
        """Запускает асинхронную обработку bounding box в отдельном потоке.

        Извлекает рамку указанного класса, проверяет неподвижность объекта
        и при положительном результате запускает тяжёлую операцию
        в фоновом потоке для блокировки основного цикла обработки.

        Args:
            frame (np.ndarray): Исходный кадр видеопотока.
            objects (list[dict]): Список обнаруженных объектов.
            current_cls (int): Класс объекта для обработки (PERSON или BADGE).
            function (Callable): Функция для выполнения в потоке (scan или ocr).
        """
        bbox = self._get_bbox(objects, current_cls)
        if check_motionless(bbox):
            threading.Thread(target=self.process_worker, 
                args=(function, frame, bbox, self.storage)).start()

    @safe_execute(default_return=(0.0, 0.0, 0.0, 0.0))
    def _get_bbox(
        self,
        bboxes: list[dict[str, int | float]], 
        cls: int
    ) -> tuple[float, float, float, float]:
        """Извлекает bounding box для указанного класса объектов.

        Ищет первый объект с совпадающим классом в списке и возвращает
        его координаты рамки. Если объект не найден, возвращает нулевую
        рамку (обработка ошибки вынесена в декоратор).

        Args:
            bboxes (list[dict]): Список обнаруженных объектов.
            cls (int): Идентификатор класса для поиска.

        Returns:
            tuple: Координаты рамки.
        """
        bbox = [b for b in bboxes if b["cls"] == cls][0]["bbox"]
        return bbox
    
    def process_worker(
            self,
            func: Callable,
            frame: np.ndarray,
            box: tuple[float, float, float, float],
            storage: ThreadResult) -> None:
        """Воркер для выполнения тяжёлых операций в отдельном потоке.
        Операции:
          scan - Векторизация лица.
          ocr -  Считывание текста с бейджика.
        
        Args:
            func (Callable): Функция для выполнения.
            frame (np.ndarray): Кадр для обработки.
            box (tuple): Bounding box обрабатываемой области.
            storage (ThreadResult): Хранилище для результата.
        """
        try:
            text = func(frame, box)
            storage.put(text)
        except Exception as e:
            # Декоратор не сработает для thread target
            import logging
            logging.getLogger(__name__).error(f"Worker error in {func.__name__}: {e}", exc_info=True)