# app/main.py
from fastapi import FastAPI, Request, HTTPException, Depends, Response, status
from pydantic import BaseModel
from app.services import fetch_polygon_open_close_stock_data, fetch_marketwatch_and_scrape_stock_data
from app.schemas import *
from datetime import date, timedelta
from decimal import Decimal
from app.data_base import create_tables_if_not_exists, get_db_session
from sqlalchemy.orm import Session
from app.models import Stocks
from app.logger import logger
from cachetools import TTLCache
from app.exceptions import StocksFastAPIError
from fastapi.responses import JSONResponse

app = FastAPI()

# Define a custom exception handler for swagger documentation
@app.exception_handler(StocksFastAPIError)
async def external_api_error_handler(request: Request, exc: StocksFastAPIError):
    if exc.error_detail:
        logger.error(f"Error Details: {exc.error_detail}")
    # Return the error response
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error": exc.error_detail
        }
    )

@app.on_event("startup")
def on_startup():
    create_tables_if_not_exists()

# Define a cache with a size of 1000 and an expiration time of 60 seconds
cache = TTLCache(maxsize=1000, ttl=60)
    
@app.get("/stock/{stock_symbol}", response_model=Stock, tags=["stock"])
async def get_stock_by_symbol(stock_symbol: str, db_session: Session = Depends(get_db_session)):
    """
    Retrieve stock data for a given stock symbol. \n
    Fetch stock values data from Polygon Open/Close API \n
    Fetch performance and competitors stock data from MarketWatch web scraping \n
    :{stock_symbol}: The symbol of the stock to fetch data for, e.g. AAPL.\n
    :RESPONSE: A dictionary containing the stock data.
    """
    
    # Check if the stock is in the cache
    if stock_symbol.upper() in cache:
        logger.info(f"Cache hit for {stock_symbol}")
        return cache[stock_symbol]
    else:
        logger.info(f"Cache miss for {stock_symbol}")
    
    # Check if the stock is already in the database to populate the purchased_amount and purchased_status
    stock_check = db_session.query(Stocks).filter(Stocks.stock_symbol == stock_symbol).first()
    purchased_amount = float(0) if not stock_check else stock_check.purchased_amount
    purchased_status = "Purchased" if stock_check else "Not Purchased"
        
    # yesterday = date.today() - timedelta(days=1) # Using yesterday's data because we don't have acess to today's data
    yesterday = '2024-11-27'
    
    # Fetch data from Polygon API
    polygon_data = await fetch_polygon_open_close_stock_data(stock_symbol, yesterday)
    
    # Fetch data from MarketWatch
    marketwatch_data = await fetch_marketwatch_and_scrape_stock_data(stock_symbol)
    
     # Map Polygon data to StockValues
    stock_values = StockValues(
        open=polygon_data.get("open"),
        high=polygon_data.get("high"),
        low=polygon_data.get("low"),
        close=polygon_data.get("close")
    )

    # Map MarketWatch performance data
    performance = marketwatch_data.get("performance_data", {})
    performance_data = PerformanceData(
        five_days=performance.get("five_days", None),
        one_month=performance.get("one_month", None),
        three_months=performance.get("three_months", None),
        year_to_date=performance.get("year_to_date", None),
        one_year=performance.get("one_year", None)
    )

    # Map MarketWatch competitors data
    competitors = []
    for comp in marketwatch_data.get("competitors_data", []):
        market_cap_data = comp.get("market_cap", {})
        competitor = Competitor(
            name=comp.get("name"),
            market_cap=MarketCap(
                currency=market_cap_data.get("currency"),
                value=Decimal(market_cap_data.get("value", '0'))
            )
        )
        competitors.append(competitor)

    # Create the Stock instance
    stock = Stock(
        status=polygon_data.get("status"),
        purchased_amount=purchased_amount,  # Assuming not purchased yet
        purchased_status=purchased_status,
        request_date=polygon_data.get("from"),
        company_code=stock_symbol.upper(),
        company_name=marketwatch_data.get("company_name", "Unknown"),
        stock_values=stock_values,
        performance_data=performance_data,
        competitors=competitors
    )
    
    # Store the stock data in the cache
    cache[stock_symbol.upper()] = stock
    logger.info(f"Cached data for {stock_symbol}")

    return stock

"""
When other function parameters that are not part of the path parameters are declared, FastAPI automatically assumes they are "query" parameters.
So, to read the request body, a parameter must be declared with the Request type or the Pydantic model type.
"""
@app.post("/stock/{stock_symbol}", response_model=AmountResponse, status_code=201, tags=["stock"]) # Modified to return 201 status code when successful, according to assignment requirements
async def update_stock_amount(stock_symbol: str, amount: Amount, db_session: Session = Depends(get_db_session)):
    """
    Update stock purchase amount, persist the data in a database and return a message presenting the amount purchased for given stock symbol.\n
    :{stock_symbol}: The symbol of the stock to fetch data for, e.g. AAPL.\n
    :REQUEST BODY: The amount of stock to purchase inside "amount" key.\n
    :db_session: The database session.\n
    :REPONSE: A message presenting the amount purchased for given stock.
    """
    stock = db_session.query(Stocks).filter(Stocks.stock_symbol == stock_symbol.upper()).first()
    if not stock:
        # If the stock is not found, create a new record
        stock = Stocks(
            stock_symbol=stock_symbol,
            purchased_amount=Decimal(amount.amount)
            )
        db_session.add(stock)

    else:
        # If the stock is found, update the amount
        stock.purchased_amount += Decimal(amount.amount)
        
    db_session.commit()
    logger.info(f"Updated purchased amount for {stock_symbol}")
        
    # Invalidate cache for the stock symbol
    if stock_symbol in cache:
        del cache[stock_symbol]
        logger.info(f"Invalidated cache for {stock_symbol}")
        
    return {"message":f"{amount.amount} units of stock {stock_symbol} were added to your stock record"}

@app.get("/stock/open_close/{stock_symbol}/{date}", response_model=PolygonOpenCloseStockDataResponse, tags=["polygon"])
async def get_open_close_stock_values_polygon_api(stock_symbol: str, date: str):
    """
    Fetch open/close stock data from the Polygon API for the given stock symbol and date.\n
    :{stock_symbol}: The symbol of the stock to fetch data for, e.g. AAPL.\n
    :{date}: The date to fetch data for in the format YYYY-MM-DD. e.g. 2023-04-28.\n
    :RESPONSE: A dictionary containing the polygon open/close API stock data.
    """
    return await fetch_polygon_open_close_stock_data(stock_symbol, date)

@app.get("/stock/marketwatch/{stock_symbol}", response_model=MarketWatchStockDataResponse, tags=["marketwatch"])
async def get_marketwatch_stock_data_scrape(stock_symbol: str):
    """
    Fetch marketwatch stock data through data scraping given stock symbol.\n
    :{stock_symbol}: The symbol of the stock to fetch data for, e.g. AAPL.\n
    :RESPONSE: A dictionary containing the polygon open/close API stock data.
    """
    return await fetch_marketwatch_and_scrape_stock_data(stock_symbol)