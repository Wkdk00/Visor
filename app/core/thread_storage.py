import threading

class ThreadResult:
    """Потокобезопасное хранилище для строкового результата.

    Позволяет безопасно записать результат вычисления в одном потоке и прочитать
    его в другом с автоматической очисткой после чтения.
    
    Attributes:
        text (str | None): Сохраненный текст.
        lock (threading.Lock): Примитив синхронизации.
    """
    def __init__(self):
        self.text = None
        self.lock = threading.Lock()

    def put(self, text: str) -> None:
        """Сохраняет текст в хранилище.

        Args:
            text (str): Хранящийся текст
        """
        with self.lock: self.text = text

    def get_and_clear(self) -> str | None:
        """Возвращает текущий текст и очищает хранилище.

        Returns:
            str | None: Текст, если он был установлен, иначе None.
        """
        with self.lock:
            if self.text:
                res = self.text
                self.text = None
                return res
            return None