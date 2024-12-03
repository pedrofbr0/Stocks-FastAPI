# app/exceptions.py
class StocksFastAPIError(Exception):
    """Base exception class for Stocks FastAPI."""
    def __init__(self, message: str = "An error occurred", error_detail: dict = None, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.error_detail = error_detail or {}
        self.status_code = status_code

class ExternalAPIError(StocksFastAPIError):
    """Exception for external API errors."""
    pass
        
class MarketWatchDataScrapeError(StocksFastAPIError):
    """Exception for scraping errors."""
    pass

class InvalidAPIResponseError(StocksFastAPIError):
    """Exception for invalid API responses."""
    pass

class InvalidAPIRequestError(StocksFastAPIError):
    """Exception for invalid API requests."""
    pass
