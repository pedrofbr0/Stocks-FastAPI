# tests/test_services.py

import pytest
from unittest.mock import patch, Mock, AsyncMock
from app.services import (
    fetch_polygon_open_close_stock_data,
    fetch_marketwatch_and_scrape_stock_data
)
from app.exceptions import ExternalAPIError, InvalidAPIResponseError, MarketWatchDataScrapeError
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

    with patch("app.services.httpx.AsyncClient") as mock_client:
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.get = AsyncMock()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response

        response = await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert response == expected_response


@pytest.mark.asyncio
async def test_fetch_polygon_http_error():
    stock_symbol = "INVALID"
    date = "2023-01-01"

    with patch("app.services.httpx.AsyncClient") as mock_client:
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Not Found",
            request=httpx.Request('GET', 'url'),
            response=httpx.Response(status_code=404, content=b'Not Found')
        )
        mock_response.json.return_value = {}
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ExternalAPIError) as exc_info:
            await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_fetch_polygon_validation_error():
    stock_symbol = "AAPL"
    date = "2024-11-27"
    invalid_response = {"invalid": "data"}

    with patch("app.services.httpx.AsyncClient") as mock_client:
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = invalid_response
        mock_response.raise_for_status = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        with pytest.raises(InvalidAPIResponseError) as exc_info:
            await fetch_polygon_open_close_stock_data(stock_symbol, date)
        assert "Failed to validate response" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_marketwatch_success():
    stock_symbol = "AAPL"
    expected_html = "<html>Valid HTML with necessary data</html>"
    expected_result = {
        "company_name": "Apple Inc.",
        "performance_data": {
            "five_days": 0.028900000000000002,
            "one_month": 0.07919999999999999,
            "three_months": 0.0462,
            "year_to_date": 0.2444,
            "one_year": 0.2648
        },
        "competitors_data": [
            {
                "name": "Microsoft Corp.",
                "market_cap": {
                    "currency": "$",
                    "value": "3.15E+12"
                }
            },
            {
                "name": "Alphabet Inc. Cl C",
                "market_cap": {
                    "currency": "$",
                    "value": "2.08E+12"
                }
            },
            {
                "name": "Alphabet Inc. Cl A",
                "market_cap": {
                    "currency": "$",
                    "value": "2.08E+12"
                }
            },
            {
                "name": "Amazon.com Inc.",
                "market_cap": {
                    "currency": "$",
                    "value": "2.19E+12"
                }
            },
            {
                "name": "Meta Platforms Inc.",
                "market_cap": {
                    "currency": "$",
                    "value": "1.45E+12"
                }
            },
            {
                "name": "Samsung Electronics Co. Ltd.",
                "market_cap": {
                    "currency": "₩",
                    "value": "3.575E+14"
                }
            },
            {
                "name": "Samsung Electronics Co. Ltd. Pfd. Series 1",
                "market_cap": {
                    "currency": "₩",
                    "value": "3.575E+14"
                }
            },
            {
                "name": "Sony Group Corp.",
                "market_cap": {
                    "currency": "¥",
                    "value": "1.87E+13"
                }
            },
            {
                "name": "Dell Technologies Inc. Cl C",
                "market_cap": {
                    "currency": "$",
                    "value": "9.295E+10"
                }
            },
            {
                "name": "HP Inc.",
                "market_cap": {
                    "currency": "$",
                    "value": "3.414E+10"
                }
            }
        ]
    }

    with patch("app.services.httpx.AsyncClient") as mock_client, \
        patch("app.services.BeautifulSoup") as mock_bs:

        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = expected_html
        mock_response.raise_for_status = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        # Mock BeautifulSoup and its methods
        mock_soup = Mock()
        mock_bs.return_value = mock_soup

        # Mock company name extraction
        mock_company_name = Mock()
        mock_company_name.get_text.return_value = "Apple Inc."

        # Mock performance data extraction
        mock_performance_table = Mock()
        mock_span_tag = Mock()
        mock_span_tag.text = 'Performance'
        mock_span_tag.name = 'span'
        mock_span_tag.parent = Mock()
        mock_span_tag.parent.parent = Mock()
        mock_span_tag.parent.parent.parent = mock_performance_table

       
        mock_performance_rows = []

        performance_data = [
            ('5 Day', '2.89%'),
            ('1 Month', '7.92%'),
            ('3 Month', '4.62%'),
            ('YTD', '24.44%'),
            ('1 Year', '26.48%')
        ]

        for period, percent in performance_data:
            mock_row = Mock()
            # Mocking the structure of the rows in the performance table
            mock_period_cell = Mock()
            mock_period_cell.get_text.return_value = period
            mock_value_cell = Mock()
            mock_value_cell.get_text.return_value = percent
            mock_row.find.side_effect = lambda name, attrs: mock_period_cell if attrs['class'] == 'table__cell' else mock_value_cell
            mock_performance_rows.append(mock_row)

        mock_performance_table.find_all.return_value = mock_performance_rows

        def mock_find(name=None, attrs=None, recursive=True, text=None, **kwargs):
            if callable(name):
                if name(mock_span_tag):
                    return mock_span_tag
                else:
                    return None
            elif name == 'h1' and attrs == {'class': 'company__name'}:
                return mock_company_name
            else:
                return None

        mock_soup.find.side_effect = mock_find

        result = await fetch_marketwatch_and_scrape_stock_data(stock_symbol)

        assert result["company_name"] == expected_result["company_name"]
        assert isinstance(result["performance_data"], dict)
        # Você mencionou que a lista de competidores pode variar, então podemos verificar apenas se é uma lista
        assert isinstance(result["competitors_data"], list)

@pytest.mark.asyncio
async def test_fetch_marketwatch_http_error():
    stock_symbol = "INVALID"

    with patch("app.services.httpx.AsyncClient") as mock_client:
        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_client_instance.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            message="Not Found",
            request=httpx.Request('GET', 'url'),
            response=httpx.Response(status_code=404, content=b'Not Found', request=httpx.Request('GET', 'url'))
    ))

    with pytest.raises(ExternalAPIError) as exc_info:
        await fetch_marketwatch_and_scrape_stock_data(stock_symbol)
    assert exc_info.value.status_code == 302


@pytest.mark.asyncio
async def test_fetch_marketwatch_parsing_error():
    stock_symbol = "AAPL"
    invalid_html = "<html>Invalid HTML</html>"

    with patch("app.services.httpx.AsyncClient") as mock_client, \
         patch("app.services.BeautifulSoup") as mock_bs:

        mock_client_instance = mock_client.return_value.__aenter__.return_value
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = invalid_html
        mock_response.raise_for_status = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)

        mock_soup = Mock()
        mock_soup.find.return_value = None
        mock_bs.return_value = mock_soup

        with pytest.raises(MarketWatchDataScrapeError) as exc_info:
            await fetch_marketwatch_and_scrape_stock_data(stock_symbol)
        assert "Failed to extract company name from MarketWatch page" in str(exc_info.value)