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
from app.exceptions import InvalidAPIResponseError, MarketWatchDataScrapeError, ExternalAPIError
from app.logger import logger
from app.schemas import PolygonOpenCloseStockDataResponse
from pydantic import ValidationError

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
        
        except ValidationError as e:
            logger.error(f"Validation error while parsing data from Polygon: {e}")
            raise InvalidAPIResponseError(
                message="Failed to validate response from external API.",
                error_detail={"error": str(e)},
                status_code=500
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching data from Polygon: {e}")
            raise ExternalAPIError(
            message=f"Failed to fetch data from external API. {e}",
            error_detail={"error": e.response.content.decode("utf-8")},
            status_code=e.response.status_code
        )
        
        except Exception as e:
            logger.exception(f"Unexpected error while fetching data from Polygon: {e}")
            status_code = e.response.status_code if hasattr(e, 'response') else 500
            error_content = e.response.content.decode("utf-8") if hasattr(e, 'response') and e.response.content else str(e)
            raise ExternalAPIError(
                message=f"An unexpected error occurred while fetching data from external API. {e}",
                error_detail={"error": error_content},
                status_code=status_code
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
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while fetching URL from Marketwatch: {e}")
            raise ExternalAPIError(
            message=f"Failed to fetch URL. {e}",
            error_detail={"error": e.response.content.decode("utf-8")},
            status_code=e.response.status_code
        )
            
        except Exception as e:
            logger.exception(f"Unexpected error during scraping for {stock_symbol}: {e}")
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else 500
            error_content = e.response.content.decode("utf-8") if hasattr(e, 'response') and e.response and e.response.content else str(e)
            raise MarketWatchDataScrapeError(
                message=f"An unexpected error occurred during data scraping. {e}",
                error_detail={"error": error_content},
                status_code=status_code
            )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.info(f"Successfully got {get_marketwatch_base_url()} for {stock_symbol} html  for scraping")

        # Parse company_name
        company_name = soup.find(
            'h1', {'class': 'company__name'})
        if(company_name):
            company_name = company_name.get_text(strip=True)
            logger.info(f"Successfully got company_name from {get_marketwatch_base_url()} for {stock_symbol}: {company_name}")
        else:
            logger.error(f"Failed to extract company name for {stock_symbol}")
            raise MarketWatchDataScrapeError(
                message=f"Failed to extract company name from MarketWatch page for {stock_symbol}.",
                error_detail={"error": "Company name not found in page."},
                status_code=500
            )
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
                logger.exception(f"Unexpected error during scraping for {stock_symbol}: {e}")
                raise MarketWatchDataScrapeError(
                    message=f"An unexpected error occurred during data scraping. {e}",
                    error_detail={"error": e.response.content.decode("utf-8")},
                    status_code=status.HTTP_204_NO_CONTENT
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
                logger.exception(f"Unexpected error during scraping for {stock_symbol}: {e}")
                raise MarketWatchDataScrapeError(
                    message=f"An unexpected error occurred during data scraping. {e}",
                    error_detail={"error": e.response.content.decode("utf-8")},
                    status_code=status.HTTP_204_NO_CONTENT
                )

        return {
            'company_name': company_name,
            'performance_data': performance_data,
            'competitors_data': competitors_data
        }