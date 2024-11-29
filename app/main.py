# app/main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from .services import fetch_polygon_open_close_stock_data, fetch_marketwatch_and_scrape_stock_data


# class Amount(BaseModel):
#     amount: float

app = FastAPI()

@app.get("/stock/{stock_symbol}")
async def get_stock(stock_symbol: str):
    return {"stock_symbol": stock_symbol}

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