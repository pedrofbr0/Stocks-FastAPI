from dotenv import load_dotenv, find_dotenv
import os
import httpx
from bs4 import BeautifulSoup
import re
from decimal import Decimal

load_dotenv(find_dotenv())

def convert_market_cap_to_decimal(value: str) -> Decimal:
    """
    Convert a string value to a Decimal.
    """
    multipliers = {
        "T": 1000000000000,
        "B": 1000000000,
        "M": 1000000,
        "K": 1000
    }
    
    # Get the multiplier from the last character of the value
    multiplier = multipliers.get(value[-1], 0)
    return Decimal(value[:-1]) * multiplier

def convert_performance_percentage_to_float(value: str) -> float:
    """
    Convert a percentage string to a float.
    """
    return float(value.strip('%')) / 100

def convert_period_to_best_practice(period: str) -> str:
    """
    Convert a period string to a best practice period string.
    """
    conversion = {
        "5 Day": "five_days",
        "1 Month": "one_month",
        "3 Month": "three_months",
        "YTD": "year_to_date",
        "1 Year": "one_year"
    }
    return conversion.get(period, period.lower().replace(" ", "_"))

async def fetch_polygon_open_close_stock_data(symbol: str, date: str):
    """
    Fetch open/close stock data from the Polygon API.
    """
    url = f"{os.getenv('POLYGON_BASE_URL')}/{symbol}/{date}"
    params = {"adjusted": "true", "apiKey": os.getenv("POLYGON_API_KEY")}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching Polygon data: {e}")
            return None
        
async def fetch_marketwatch_and_scrape_stock_data(stock_symbol: str):
    """
    Fetch performance and competitors data from MarketWatch.
    """
    url = f"{os.getenv('MARKETWATCH_BASE_URL')}/{stock_symbol.lower()}"
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
            html_content = response.text
        except httpx.HTTPError as e:
            print(f"HTTP error occurred while fetching MarketWatch data: {e}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Parse company_name
        company_name = soup.find('h1', {'class': 'company__name'}).get_text(strip=True)
        
        # Parse performance table
        # Search by text with the help of lambda function
        preformance_text = 'Performance'
        performance_table = soup.find(lambda tag: tag.name == "span" and preformance_text in tag.text).parent.parent.parent
        # performance_table = soup.find('span', {'class': 'performance'})
        performance_data = {}
        if performance_table:
            rows = performance_table.find_all('tr', {'class': 'table__row'})
            for row in rows:
                period = convert_period_to_best_practice(row.find('td', {'class': 'table__cell'}).get_text(strip=True))
                value = row.find('li', {'class': re.compile(r'\bvalue\b')}).get_text(strip=True) # Use regex to match a specific class within the class attribute
                performance_data[period] = convert_performance_percentage_to_float(value)

        # Parse competitors table
        competitors_table = soup.find('table', {'aria-label': 'Competitors data table'})
        competitors_data = []
        
        # Regex pattern to match market cap values form currency and value separation
        pattern = r"([^\w\s\d]+)\s*(\d[\d.,]*(?:[M|B|T]?)?)"
        
        if competitors_table:
            rows = competitors_table.find('tbody').find_all('tr')
            for row in rows:
                name = row.find('td', {'class': 'table__cell w50'}).get_text(strip=True)
                change = row.find('td', {'class': 'table__cell w25'}).find('bg-quote').get_text(strip=True)
                market_cap = row.find('td', {'class': 'table__cell w25 number'}).get_text(strip=True)
                regex_match = re.match(pattern,market_cap.strip())
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