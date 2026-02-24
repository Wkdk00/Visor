import pytesseract, cv2, numpy as np

def ocr(
        frame: np.ndarray,
        box: tuple[float, float, float, float]
        ) -> str:
    """Функция для распознавания Должности и ФИО сотрудника
    с бейджа. Функция из исходного фрейма оставляет только бейдж,
    преобразует его и выполняет OCR с помощью tesseract.

    Args:
        frame (np.ndarray): Кадр с видеопотока в формате BGR
        box (tuple[float, float, float, float]): рамка бейджа (x1, y1, x2, y2)

    Returns:
        str: Должность и ФИО сотрудника
    """
    frame = frame[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, frame = cv2.threshold(frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(frame, lang='rus')
    text = text.replace("\n", " ")
    return text