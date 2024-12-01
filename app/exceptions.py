# app/exceptions.py
class StocksFastAPIError(Exception):
    """base exception class"""
    def __init__(self, message: str = "Service is unavailable", status_code: int = 500, error_detail: dict = None):
        self.message = message
        self.status_code = status_code
        self.error_detail = error_detail or {}
        super().__init__(self.message, self.status_code, self.error_detail)

class ExternalAPIError(StocksFastAPIError):
    pass
        
class MarketWatchDataScrapeError(StocksFastAPIError):
    pass

class InvalidAPIResponseError(StocksFastAPIError):
    pass
