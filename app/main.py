# app/main.py
from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from app.services import fetch_polygon_open_close_stock_data, fetch_marketwatch_and_scrape_stock_data
from app.schemas import *
from datetime import date, timedelta
from decimal import Decimal
from app.data_base import create_tables_if_not_exists, get_db_session
from sqlalchemy.orm import Session
from app.models import Stocks

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_tables_if_not_exists()

@app.get("/stock/{stock_symbol}")
async def get_stock(stock_symbol: str):
    """
    Retrieve stock data for a given symbol. Fetch stock values data from Polygon Open/Close API 
    and do some web scraping on MarketWatch to get performance data and competitors data for the stock.
    :param stock_symbol: The symbol of the stock to retrieve data for.
    :return: A dictionary containing the stock data.
    :raises HTTPException: If the stock data is not found.
    """
    
    yesterday = date.today() - timedelta(days=2) # Using yesterday's data because we don't have acess to today's data
    
    # Fetch data from Polygon API
    polygon_data = await fetch_polygon_open_close_stock_data(stock_symbol, yesterday)
    if not polygon_data:
        raise HTTPException(status_code=404, detail="Stock data not found from Polygon API")
    
    # Fetch data from MarketWatch
    marketwatch_data = await fetch_marketwatch_and_scrape_stock_data(stock_symbol)
    if not marketwatch_data:
        raise HTTPException(status_code=404, detail="Stock data not found from MarketWatch")
    
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
        five_days=performance.get("five_days", 0.0),
        one_month=performance.get("one_month", 0.0),
        three_months=performance.get("three_months", 0.0),
        year_to_date=performance.get("year_to_date", 0.0),
        one_year=performance.get("one_year", 0.0)
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
        purchased_amount=Decimal('0'),  # Assuming not purchased yet
        purchased_status="Not Purchased",
        request_date=polygon_data.get("from"),
        company_code=stock_symbol.upper(),
        company_name=marketwatch_data.get("company_name") or "N/A",
        stock_values=stock_values,
        performance_data=performance_data,
        competitors=competitors
    )

    return stock

"""
When other function parameters that are not part of the path parameters are declared, FastAPI automatically assumes they are "query" parameters.
So, to read the request body, a parameter must be declared with the Request type or the Pydantic model type.
"""
@app.post("/stock/{stock_symbol}", status_code=201) # Modified to return 201 status code when successful, according to assignment requirements
async def update_stock_amount(stock_symbol: str, amount: Amount, db_session: Session = Depends(get_db_session)):
    """
    Update stock purchase amount, persist the data in a database and return a message presenting the amount purchased for given stock.
    :param stock_symbol: The symbol of the stock to update the amount.
    :param amount: The amount of stock to purchase.
    :param db_session: The database session.
    :return: A message presenting the amount purchased for given stock.
    """
    stock = db_session.query(Stocks).filter(Stocks.stock_symbol == stock_symbol).first()
    if not stock:
        # If the stock is not found, create a new record
        stock = Stocks(
            stock_symbol=stock_symbol,
            purchased_amount=Decimal(amount.amount)
            )
        db_session.add(stock)
        db_session.commit()
    else:
        # If the stock is found, update the amount
        stock.purchased_amount += Decimal(amount.amount)
        db_session.commit()
        
    return f'{amount.amount} units of stock {stock_symbol} were added to your stock record'