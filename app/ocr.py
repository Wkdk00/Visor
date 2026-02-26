import cv2
import numpy as np
import pytesseract

def ocr(frame: np.ndarray, box: tuple[float, float, float, float]) -> str:
    """Распознаёт текст в указанной области кадра с помощью Tesseract OCR.

    Args:
        frame (np.ndarray): Исходный фрейм в BGR
        box (tuple[float, float, float, float]): Ограничивающая рамка текста

    Returns:
        str: Текст с бейджика
    """
    x1, y1, x2, y2 = map(int, box)
    roi = frame[y1:y2, x1:x2]
    
    if roi.size == 0:
        return ""

    roi = cv2.resize(roi, (0, 0), fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    kernel = np.ones((3,3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    binary = cv2.bitwise_not(binary)
    
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(binary, lang='rus', config=config)
    
    return ' '.join(text.split())