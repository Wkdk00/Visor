import logging
import functools
from typing import Callable, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

if not logger.handlers:
    handler = logging.FileHandler('errors.log', encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def safe_execute(default_return: Any = None):
    """
    Декоратор для обработки исключений.
    
    Args:
        default_return: Значение, которое вернётся при ошибке (чтобы приложение не падало).
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Ошибка в функции '{func.__name__}': {type(e).__name__} - {e}"
                )
                return default_return
        return wrapper
    return decorator