from Levenshtein import ratio
from app.database import cursor
from app.config import PersonStates, THRESHOLD
from app.decorators import safe_execute

class PersonTemplate:
    """Класс для управления состоянием идентификации сотрудника.

    Реализует логику многоэтапной верификации личности, объединяя данные 
    от распознавания лица (векторная база) и OCR (чтение бейджа). 
    Отслеживает текущий этап обработки через конечный автомат состояний 
    (STATE_DICT) и выполняет финальное сравнение данных для подтверждения 
    личности.

    Workflow:
        1. unregistered - начальное состояние, данных нет.
        2. vectorized - получено имя из распознавания лица.
        3. ocr - получено имя с бейджа (OCR).
        4. verify - данные сверены, личность подтверждена.
        5. error - критическая ошибка обработки.

    Attributes:
        vector_name (str): ФИО сотрудника из векторной базы (face recognition).
        vector_post (str): Должность сотрудника из реляционной БД.
        OCR_name (str): ФИО сотрудника, распознанное с бейджа (OCR).
        THRESHOLD (float): Порог схожести строк для подтверждения личности.
        ALPHABET (str): Валидные символы для OCR.
    """

    ALPHABET = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

    def __init__(self):
        self.vector_name: str = ""
        self.vector_post: str = ""
        self.OCR_name: str = ""
        self.THRESHOLD = THRESHOLD

    def state(self) -> PersonStates:
        """Метод для получения текущего состояния обработки.

        Returns:
            PersonStates: Одно из значений: 'unregistered', 'vectorized', 'ocr', 'verify', 'error'.
        """
        if not self.vector_name and not self.OCR_name: return PersonStates.UNREGISTERED
        elif self.vector_name and not self.OCR_name: return PersonStates.VECTORIZED
        elif self.vector_name and self.OCR_name: return PersonStates.OCR_READY
        return PersonStates.ERROR
    
    def clear(self) -> None:
        """
        Метод для очистки информации о текущем работнике
        """
        self.vector_name = ""
        self.OCR_name = ""
        self.vector_post = ""

    def set_vector_name(self, vec_name: str) -> None:
        """Метод для добавления ФИО работника,
        полученного с помощью распознавания лица
        (из векторной базы данных).

        Args:
            vec_name (str): ФИО работника
        """
        self.vector_name = vec_name

    def set_ocr_name(self, ocr_name: str) -> None:
        """Метод для добавления ФИО работника,
        полученного с бейджа (OCR). Сразу убраны
        лишние символы, которые могли возникнуть из-за OCR

        Args:
            ocr_name (str): ФИО работника
        """
        self.OCR_name = "".join(s for s in ocr_name if s in self.ALPHABET)

    @safe_execute(default_return=False)
    def comparison_vector_ocr(self) -> bool:
        """Метод для сравнения ФИО из векторной БД
        и ФИО с бейджа. С бейджа был получен текст вида
        СОТРУДНИКИвановИванИванович. Для получения должности
        из распознавания лица возьмем должность из реляционной БД.

        Returns:
            bool: True если личность подтверждена иначе False
        """
        cursor.execute(
            "SELECT post FROM Users WHERE name = ? LIMIT 1", 
            (self.vector_name,)
        )
        result = cursor.fetchone()
        self.vector_post = result[0] if result else ""

        employee = (self.vector_post + self.vector_name).replace(" ", "")
        return ratio(employee, self.OCR_name) > self.THRESHOLD