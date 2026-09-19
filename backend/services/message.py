import cv2
from typing import Literal
import numpy as np

class TextArea:
    """Класс для отображения текстовых уведомлений на видеокадре.

    Из-за того, что каждый кадр мы можем выловить разные предупреждения
    текст может отображаться на 1-2 кадра. Это выглядит непрофессионально
    и нечитабельно. Данный класс решает эту проблему: текст отображается 
    определенное количество кадров, после чего автоматически очищается.

    Attributes:
        text (str): Текущий отображаемый текст.
        counter (int): Счетчик кадров отображения текущего сообщения.
        FREQUENCY (int): Длительность отображения сообщения в кадрах.
        DICT_TYPE (dict): Конфигурация стилей для разных типов сообщений.
        type (str): Тип текущего сообщения.
    """
    def __init__(self):
        self.text = ""
        self.counter = 0
        self.FREQUENCY = 45
        self.DICT_TYPE = {
            "name":{"color": (255,0,0), "place":(90, 40)},
            "alert":{"color": (0,0,255), "place":(90, 440)},
            "notice":{"color": (0,255,0), "place":(90, 440)}
        }
        self.type = ""

    def add_text(self, text: str, type: Literal["name", "alert", "notice"]) -> None:
        """Метод для добавления текста в буффер.

        Args:
            text (str): Текст сообщения
            type (str): Тип сообщения

        Raises:
            ValueError: Если передан недопустимый тип сообщения.
        """
        if type not in self.DICT_TYPE:
            raise ValueError(f"Недопустимый тип сообщения: {type}")

        if len(self.text) == 0:
            self.text = text
            self.type = type
    
    def empty(self) -> bool:
        """Метод для проверки отображается ли сейчас какой нибудь текст.

        Returns:
            bool: True если буффер пустой иначе False
        """
        return True if len(self.text) == 0 else False
    
    def print_text(self, frame: np.ndarray) -> np.ndarray:
        """Метод для отображения текста на видеокадре.

        Args:
            frame (np.ndarray): Исходный фрейм

        Returns:
            np.ndarray: Фрейм с добавленным на него текстом

        Raises:
            ValueError: Ошибка в передаче фрейма.
        """
        if frame.size == 0:
            raise ValueError(f"frame пустой")
        
        if len(frame.shape) != 3:
            raise ValueError(f"frame должен иметь 3 измерения. Получено: {len(frame.shape)}")
        
        if len(self.text) == 0:
            return frame
        elif self.counter < self.FREQUENCY and len(self.text) > 0:
            place = self.DICT_TYPE[self.type]["place"]
            color = self.DICT_TYPE[self.type]["color"]
            cv2.putText(frame, self.text, place, cv2.FONT_HERSHEY_COMPLEX, 1.0, color)
            self.counter +=1
        elif self.counter >= self.FREQUENCY:
            self.counter = 0
            self.text = ""
            self.type = ""
        return frame