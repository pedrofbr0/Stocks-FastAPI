# app/main.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from .services import fetch_polygon_open_close_stock_data, fetch_marketwatch_and_scrape_stock_data
from .schemas import *
from datetime import date, timedelta
from decimal import Decimal


# class Amount(BaseModel):
#     amount: float

app = FastAPI()

@app.get("/stock/{stock_symbol}")
async def get_stock(stock_symbol: str):
    
    yesterday = date.today() - timedelta(days=2) # Fetch yesterday's data because we don't have acess to today's data
    print(yesterday)
    
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
@app.post("/stock/{stock_symbol}")
async def update_stock_amount(stock_symbol: str, request: Request):
    print(await request.json())
    req_dict = await request.json()
    return f'{req_dict["amount"]} units of stock {stock_symbol} were added to your stock record'
# async def update_stock_amount(stock_symbol: str, amount: Amount):
#     print(amount)
#     return f'{amount.amount} units of stock {stock_symbol} were added to your stock record'

@app.get("/stock/open_close/{stock_symbol}/{date}")
async def get_open_close(stock_symbol: str, date: str):
    return await fetch_polygon_open_close_stock_data(stock_symbol, date)

@app.get("/stock/marketwatch/{stock_symbol}")
async def get_marketwatch(stock_symbol: str):
    return await fetch_marketwatch_and_scrape_stock_data(stock_symbol)