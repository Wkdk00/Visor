from ml.detection import DetectionModel
from services.message import TextArea
from services.person import PersonTemplate
from services.pipeline import Pipeline
from core.thread_storage import ThreadResult
from database.qdrant.qdrant import QdrantRecognizer

class AppContainer:
    """
    Центральный контейнер зависимостей приложения.

    Этот класс управляет жизненным циклом основных сервисов.

    Attributes:
        qdrant (QdrantRecognizer): Клиент базы данных векторов.
        message (TextArea): Сервис отрисовки текста на кадре.
        model (DetectionModel): Класс-обертка для модели детекции.
        person (PersonTemplate): Сервис работы с состоянием пользователей.
        thread_storage (ThreadResult): Временное хранилище результатов обработки.
        pipeline (Pipeline): Основной бизнес-пайплайн обработки кадров.
    """
    def __init__(self):
        self.qdrant = QdrantRecognizer()
        self.message = TextArea()
        self.model = DetectionModel()
        self.person = PersonTemplate()
        self.thread_storage = ThreadResult()

        self.pipeline = Pipeline(
            model=self.model, 
            message=self.message, 
            storage=self.thread_storage, 
            person=self.person, 
            vec_DB=self.qdrant
        )

container = AppContainer()