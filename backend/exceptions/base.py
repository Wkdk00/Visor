class VisorError(Exception):
    pass

class NotFoundFromDB(VisorError):
    def __init__(self, entity: str | None):
        self.entity = entity
        
        if self.entity:
            message = f"{self.entity} not found"
        else:
            message = "Not found"

        super().__init__(message) 