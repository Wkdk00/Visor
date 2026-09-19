from collections import deque

from core.config import MOTIONLESS_FRAME
from core.decorators import safe_execute

from cpp_iou import calculate_iou

@safe_execute(default_return=False)
def check_PPE_intersections(boxes: list[dict]) -> bool:
    """Проверяет пересечение СИЗ с лицом человека.

    Args:
        boxes (list[dict]): Список обнаруженных объектов.

    Returns:
        bool: True если СИЗ не пересекаются с человеком, иначе False
    """
    person = [box for box in boxes if box["cls"] == 0]
    if len(person) == 1:
        person_bbox = person[0]["bbox"]
        PPE = [1, 2, 3]
        for box in boxes:
            if box["cls"] not in PPE:
                continue
            if boxes_intersect(person_bbox, box["bbox"]):
                return False
        return True
    return False

@safe_execute(default_return=0)
def IoU(
        box1: tuple[float, float, float, float],
        box2: tuple[float, float, float, float]
    ) -> float:
    """Вычисляет коэффициент пересечения для двух рамок.

    Вся логика вычисления IoU реализована на C++ для повышения производительности.

    Args:
        box1 (tuple[float, float, float, float]): Первая рамка (x1, y1, x2, y2).
        box2 (tuple[float, float, float, float]): Вторая рамка (x1, y1, x2, y2).

    Returns:
        float: Значение IoU (0 - нет пересечения, 1 - полное совпадение).
    """
    return calculate_iou(box1, box2)

motionless = deque()

@safe_execute(default_return=False)
def check_motionless(
        bbox: tuple[float, float, float, float]) -> bool:
    """Проверяет, находится ли объект в неподвижном состоянии.

    Анализирует положение объекта за последние 30 кадров. Если IoU между
    текущей и первой рамкой в очереди больше 0.9, объект считается неподвижным.

    Args:
        bbox (tuple[float, float, float, float]): Текущая рамка объекта (x1, y1, x2, y2).

    Returns:
        bool: True если объект не двигается (IoU > 0.9), иначе False.
    """
    motionless.append(bbox)
    if len(motionless) < MOTIONLESS_FRAME:
        return False
    elif len(motionless) > MOTIONLESS_FRAME:
        motionless.popleft()

    area = IoU(bbox, motionless[0])
    if area > 0.9:
        motionless.clear()
        return True
    return False

@safe_execute(default_return=({}, 0))
def class_count(boxes: list[dict]) -> tuple[dict, int]:
    """Подсчитывает количество объектов каждого класса.

    Args:
        boxes (list[dict]): Список обнаруженных объектов.

    Returns:
        tuple[dict, int]: Кортеж из:
            - hashmap (dict): Словарь {class_id: count} для классов 0-4.
            - length (int): Общее количество объектов.
    """
    length = len(boxes)
    
    hashmap = {0:0, 1:0, 2:0, 3:0, 4:0}
    for box in boxes:
        cls = int(box["cls"])
        hashmap[cls] +=1
    return hashmap, length

@safe_execute(default_return=False)
def boxes_intersect(
        box1: tuple[float, float, float, float],
        box2: tuple[float, float, float, float]
    ) -> bool:
    """Проверяет наличие пересечения между двумя рамками.

    Args:
        box1 (tuple[float, float, float, float]): Первая рамка (x1, y1, x2, y2).
        box2 (tuple[float, float, float, float]): Вторая рамка (x1, y1, x2, y2).

    Returns:
        bool: True если рамки пересекаются, иначе False.

    Raises:
        ValueError: If min coordinate > max.
    """
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    if x1_min > x1_max or y1_min > y1_max:
        raise ValueError(f"Invalid box1 coordinates: min > max")
    if x2_min > x2_max or y2_min > y2_max:
        raise ValueError(f"Invalid box2 coordinates: min > max")

    if x1_max < x2_min or x2_max < x1_min:
        return False
    if y1_max < y2_min or y2_max < y1_min:
        return False

    return True