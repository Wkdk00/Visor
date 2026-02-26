from Levenshtein import ratio
from app.database import cursor

class PersonTemplate:
    def __init__(self):
        self.vector_name = ""
        self.vector_post = ""
        self.OCR_name = ""
        self.STATE_DICT = {0:"unregistered", 1:"vectorized", 2:"ocr", 3:"verify", 4:"error"}
        self.THRESHOLD = 0.7
        self.ALPHABET = "АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя"

    def state(self):
        if not self.vector_name and not self.OCR_name: return self.STATE_DICT[0]
        elif self.vector_name and not self.OCR_name: return self.STATE_DICT[1]
        elif self.vector_name and self.OCR_name: return self.STATE_DICT[2]
        return self.STATE_DICT[3]
    
    def clear(self):
        self.vector_name = ""
        self.OCR_name = ""
        self.vector_post = ""

    def set_vector_name(self, vec_name: str):
        self.vector_name = vec_name

    def set_ocr_name(self, ocr_name: str):
        self.OCR_name = "".join(s for s in ocr_name if s in self.ALPHABET)

    def comparsion_vector_ocr(self):
        cursor.execute("SELECT post FROM Users WHERE name = ? LIMIT 1", (self.vector_name,))
        result = cursor.fetchone()
        self.vector_post = result[0] if result else ""
        employee = (self.vector_post + self.vector_name).replace(" ", "")
        return ratio(employee, self.OCR_name) > self.THRESHOLD