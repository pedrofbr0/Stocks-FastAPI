from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal
from datetime import date

class MarketCap(BaseModel):
    currency: str
    value: Decimal

class Competitor(BaseModel):
    name: str
    market_cap: MarketCap

class PerformanceData(BaseModel):
    five_days: float
    one_month: float
    three_months: float
    year_to_date: float
    one_year: float

class StockValues(BaseModel):
    open: float
    high: float
    low: float
    close: float

class Stock(BaseModel):
    status: str
    purchased_amount: Decimal = Field(..., description="Amount of stock purchased")
    purchased_status: str
    request_date: date = Field(..., description="Always in the YYYY-MM-DD format")
    company_code: str
    company_name: str
    stock_values: StockValues
    performance_data: PerformanceData
    competitors: List[Competitor]