# app/exceptions.py
class ExternalAPIError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_detail: dict = None):
        self.message = message
        self.status_code = status_code
        self.error_detail = error_detail or {}
        super().__init__(message)
        
class MarketWatchDataError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_detail: dict = None):
        self.message = message
        self.status_code = status_code
        self.error_detail = error_detail or {}
        super().__init__(message)

class DatabaseError(Exception):
    def __init__(self, message: str, error_detail: dict = None):
        self.message = message
        self.error_detail = error_detail or {}
        super().__init__(message)