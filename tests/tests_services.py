# tests/tests_services.py
import pytest
from app.services import fetch_polygon_open_close_stock_data, fetch_marketwatch_and_scrape_stock_data
from app.exceptions import InvalidAPIResponseError
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_fetch_polygon_success():
    stock_symbol = "AAPL"
    date = "2024-11-27"
    expected_response = {
        "status": "OK",
        "from": "2024-11-27",
        "symbol": "AAPL",
        "open": 234.465,
        "high": 235.69,
        "low": 233.8101,
        "close": 234.93,
        "volume": 31604402,
        "afterHours": 235.2,
        "preMarket": 235.5
    }

    with patch("app.services.fetch_polygon_open_close_stock_data") as mock_request:
        mock_request.return_value = AsyncMock(json=AsyncMock(return_value=expected_response))
        response = await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert response == expected_response

@pytest.mark.asyncio
async def test_fetch_polygon_http_error():
    stock_symbol = "INVALID"
    date = "2024-11-28"

    with patch("app.services.fetch_polygon_open_close_stock_data") as mock_request:
        mock_request.side_effect = ExternalAPIError(
            message="HTTP error occurred",
            status_code=404,
            error_detail={"content": "Not Found"}
        )
        with pytest.raises(ExternalAPIError) as exc_info:
            await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert exc_info.value.status_code == 404
        
@pytest.mark.asyncio
async def test_fetch_polygon_http_error():
    stock_symbol = "AAPL"
    date = "2024-11-28"

    with patch("app.services.fetch_polygon_open_close_stock_data") as mock_request:
        mock_request.side_effect = InvalidAPIResponseError(
            message="HTTP error occurred",
            status_code=404,
            error_detail={"content": "Not Found"}
        )
        with pytest.raises(InvalidAPIResponseError) as exc_info:
            await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert exc_info.value.status_code == 404