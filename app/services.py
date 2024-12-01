# app/services.py
from dotenv import load_dotenv, find_dotenv
import os
import httpx
from bs4 import BeautifulSoup
import re
from decimal import Decimal
from app.utils import (
    convert_market_cap_to_decimal, 
    convert_performance_percentage_to_float, 
    convert_period_to_best_practice, 
    get_polygon_base_url, 
    get_polygon_api_key, 
    get_marketwatch_base_url, 
    get_marketwatch_base_url
)
from fastapi import HTTPException
from app.exceptions import ExternalAPIError, MarketWatchDataError
from app.logger import logger

async def fetch_polygon_open_close_stock_data(stock_symbol: str, date: str):
    """
    Fetch open/close stock data from the Polygon API for the given symbol and date.\n
    {stock_symbol}: The symbol of the stock to fetch data for, e.g. AAPL.\n
    {date}: The date to fetch data for in the format YYYY-MM-DD. e.g. 2023-04-28.\n
    RESPONSE: A dictionary containing the polygon open/close API stock data.
    """
    url = f"{get_polygon_base_url()}/{stock_symbol}/{date}"
    params = {"adjusted": "true", "apiKey": get_polygon_api_key()}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            # error_message = f"HTTP error occurred while fetching Polygon data: {e}"
            error_status_code = e.response.status_code if e.response else 500
            error_content = e.response.text[:500] if e.response else "No response content"
            
            # # Log the error
            # logger.error(error_message)
            # logger.debug(f"Response content: {error_content}")
            
            # Attempt to parse the external API's error message
            error_message_from_api = ""
            if e.response and 'application/json' in e.response.headers.get('Content-Type', ''):
                try:
                    error_json = e.response.json()
                    error_message_from_api = error_json.get('message', '')
                except ValueError:
                    pass  # Response is not valid JSON
                
            # Construct the error message
            error_message = (
                f"HTTP error occurred while fetching Polygon: {e}"
                f"External API message: {error_message_from_api}"
            )

            # Log the error details
            logger.error(error_message)
            logger.error(f"Response content: {error_content}")
            
            # Raise custom exception with error details
            raise ExternalAPIError(
                message=error_message,
                status_code=error_status_code,
                error_detail={"content": error_content}
            )
        except Exception as e:
            # Log unexpected errors
            logger.exception("An unexpected error occurred while fetching Polygon.")
            raise ExternalAPIError(
                message="An unexpected error occurred while fetching Polygon.",
                status_code=500,
                error_detail={"error": str(e)}
            )

async def fetch_marketwatch_and_scrape_stock_data(stock_symbol: str):
    """
    Fetch performance and competitors data from MarketWatch for the given stock symbol.
    :param stock_symbol: The symbol of the stock to fetch data for.
    :return: A dictionary containing the stock data.
    """
    url = f"{get_marketwatch_base_url()}/{stock_symbol.lower()}"
    
    # Some websites need headers to be set in order to be correctly scraped. Tested some headers and these worked for MarketWatch.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            # html_content = response.text
        except httpx.HTTPError as e:
            # Extract error information
            # error_message = f"HTTP error occurred while fetching MarketWatch data: {e}"
            error_status_code = e.response.status_code if e.response else 500
            error_content = e.response.text[:500] if e.response else "No response content"

           # Attempt to parse the error message if available
            error_message_from_api = "No error message provided."
            # MarketWatch may not return a JSON error, so we can include the response text
            error_message = (
                f"HTTP error occurred while fetching MarketWatch: {e}"
                f"External API message: {error_content}"
            )

            # Log the error details
            logger.error(error_message)

            # Raise custom exception with error details
            raise ExternalAPIError(
                message=error_message,
                status_code=error_status_code,
                error_detail={"content": error_content}
            )
            
        except Exception as e:
            # Log unexpected errors
            logger.exception("An unexpected error occurred while fetching MarketWatch.")
            raise ExternalAPIError(
                message="An unexpected error occurred while fetching MarketWatch.",
                status_code=500,
                error_detail={"error": str(e)}
            )
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse company_name
        company_name = soup.find(
            'h1', {'class': 'company__name'}).get_text(strip=True)

        # Parse performance table
        # Search by text with the help of lambda function
        preformance_text = 'Performance'
        performance_table = soup.find(
            lambda tag: tag.name == "span" and preformance_text in tag.text).parent.parent.parent
        # performance_table = soup.find('span', {'class': 'performance'})
        performance_data = {}
        if performance_table:
            rows = performance_table.find_all('tr', {'class': 'table__row'})
            for row in rows:
                period = convert_period_to_best_practice(
                    row.find('td', {'class': 'table__cell'}).get_text(strip=True))
                value = row.find('li', {'class': re.compile(r'\bvalue\b')}).get_text(
                    strip=True)  # Use regex to match a specific class within the class attribute
                performance_data[period] = convert_performance_percentage_to_float(
                    value)

        # Parse competitors table
        competitors_table = soup.find(
            'table', {'aria-label': 'Competitors data table'})
        competitors_data = []

        # Regex pattern to match market cap values form currency and value separation
        pattern = r"([^\w\s\d]+)\s*(\d[\d.,]*(?:[M|B|T]?)?)"

        if competitors_table:
            rows = competitors_table.find('tbody').find_all('tr')
            for row in rows:
                name = row.find(
                    'td', {'class': 'table__cell w50'}).get_text(strip=True)
                change = row.find('td', {'class': 'table__cell w25'}).find(
                    'bg-quote').get_text(strip=True)
                market_cap = row.find(
                    'td', {'class': 'table__cell w25 number'}).get_text(strip=True)
                regex_match = re.match(pattern, market_cap.strip())
                if regex_match:
                    market_cap_currency, market_cap_value = regex_match.groups()
                competitors_data.append({
                    'name': name,
                    'change': change,
                    'market_cap': {
                        'currency': market_cap_currency,
                        'value': convert_market_cap_to_decimal(market_cap_value)
                    } if regex_match else {
                        'currency': None,
                        'value': None
                    }
                })

        return {
            'company_name': company_name,
            'performance_data': performance_data,
            'competitors_data': competitors_data
        }