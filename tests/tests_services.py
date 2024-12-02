# tests/test_services.py

import pytest
from app.services import fetch_polygon_open_close_stock_data, fetch_marketwatch_and_scrape_stock_data
from app.exceptions import InvalidAPIResponseError, ExternalAPIError
from unittest.mock import patch, AsyncMock
import httpx

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

    with patch("app.services.httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value=expected_response)
        mock_get.return_value = mock_response

        response = await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert response == expected_response

@pytest.mark.asyncio
async def test_fetch_polygon_http_error():
    stock_symbol = "INVALID"
    date = "2024-11-27"

    with patch("app.services.httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Not Found",
            request=httpx.Request('GET', 'url'),
            response=httpx.Response(status_code=404)
        )
        mock_get.return_value = mock_response

        with pytest.raises(InvalidAPIResponseError) as exc_info:
            await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_fetch_polygon_validation_error():
    stock_symbol = "AAPL"
    date = "2024-11-27"
    invalid_response = {"invalid": "data"}

    with patch("app.services.httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value=invalid_response)
        mock_get.return_value = mock_response

        with pytest.raises(InvalidAPIResponseError) as exc_info:
            await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert exc_info.value.status_code == 400
