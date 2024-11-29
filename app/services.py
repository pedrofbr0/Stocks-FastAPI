from dotenv import load_dotenv, find_dotenv
import os
import httpx

load_dotenv(find_dotenv())
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