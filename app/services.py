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
from fastapi import HTTPException, status
from app.exceptions import ExternalAPIError, MarketWatchDataScrapeError
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
            
            # Parse the response JSON
            json_response = response.json()
            
            # Validate the response JSON using the schema
            json_response_validated = PolygonOpenCloseStockDataResponse(**json_response)
            
            logger.info(f"Successfully fetched {get_polygon_base_url()} data for {stock_symbol} on {date}")
            logger.debug(f"Response: {response.json()}")
            
            return json_response
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise InvalidAPIResponseError(
                message="Failed to fetch data from external API.",
                status_code=response.status_code if response else status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"error": str(e)}
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise InvalidAPIResponseError(
                message="Invalid data format received from external API.",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=e.errors()
            )

        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            raise InvalidAPIResponseError(
                message="An unexpected error occurred while processing the API response.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details=e.errors()
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
            logger.info(f"Successfully fetched {get_marketwatch_base_url()} data for {stock_symbol}")
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise HTTPException(status_code=response.status_code, detail=f"An error occurred while fetching MarketWatch data. ERROR: {e}")
            
        except Exception as e:
            logger.error("An unexpected error occurred while fetching MarketWatch.")
            raise ExternalAPIError(
                message="An unexpected error occurred while fetching MarketWatch.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_detail={e.errors()}
            )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.info(f"Successfully got {get_marketwatch_base_url()} for {stock_symbol} html  for scraping")

        # Parse company_name
        company_name = soup.find(
            'h1', {'class': 'company__name'}).get_text(strip=True)
        if(company_name):
            logger.info(f"Successfully got company_name from {get_marketwatch_base_url()} for {stock_symbol}: {company_name}")

        # Parse performance table
        # Search by text with the help of lambda function
        preformance_text = 'Performance'
        performance_table = soup.find(
            lambda tag: tag.name == "span" and preformance_text in tag.text).parent.parent.parent
        performance_data = {}
        if performance_table:
            try:
                rows = performance_table.find_all('tr', {'class': 'table__row'})
                for row in rows:
                    period = convert_period_to_best_practice(
                        row.find('td', {'class': 'table__cell'}).get_text(strip=True))
                    value = row.find('li', {'class': re.compile(r'\bvalue\b')}).get_text(
                        strip=True)  # Use regex to match a specific class within the class attribute
                    performance_data[period] = convert_performance_percentage_to_float(
                        value)
                logger.info(f"Successfully got performance data from {get_marketwatch_base_url()} for {stock_symbol}")
                logger.debug(f"Performance data: {performance_data}")
            except Exception as e:
                logger.error(f"Error occurred while parsing MarketWatch data: {e}")
                raise MarketWatchDataError(
                    message="An error occurred while parsing MarketWatch data.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error_detail=e
                )

        # Parse competitors table
        competitors_table = soup.find(
            'table', {'aria-label': 'Competitors data table'})
        competitors_data = []

        # Regex pattern to match market cap values form currency and value separation
        pattern = r"^(.*?)\s*([\d.,]+[kMBT]?)$"

        if competitors_table:
            try:
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
                logger.info(f"Successfully got competitors data from {get_marketwatch_base_url()} for {stock_symbol}")
                logger.debug(f"Competitors data: {competitors_data}")
            except Exception as e:
                logger.error(f"Error occurred while parsing MarketWatch data: {e}")
                raise MarketWatchDataError(
                    message="An error occurred while parsing MarketWatch data.",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error_detail=e
                )

        return {
            'company_name': company_name,
            'performance_data': performance_data,
            'competitors_data': competitors_data
        }