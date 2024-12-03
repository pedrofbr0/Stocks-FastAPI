# app/schemas.py
from pydantic import BaseModel, Field, model_validator
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
    purchased_amount: Decimal = Field(...,
                                      description="Amount of stock purchased")
    purchased_status: str
    request_date: date = Field(...,
                               description="Always in the YYYY-MM-DD format")
    company_code: str
    company_name: str
    stock_values: StockValues
    performance_data: PerformanceData
    competitors: List[Competitor]


class Amount(BaseModel):
    amount: Decimal = Field(..., description="Amount of stock to purchase. Must be a positive number. Values below 4 decimal will not be persisted.", example="5.33")

    @model_validator(mode="after")
    def validate_amount(self):
        if self.amount is None:
            raise ValueError("'amount' cannot be null.")
        if self.amount < 0:
            raise ValueError("'amount' must be a positive number.")
        if self.amount.as_tuple().exponent < -4:
            raise ValueError("'amount' must have at most 4 decimal places.")
        return self


class AmountResponse(BaseModel):
    message: str = Field(
        ..., description="\{amount.amount\} units of stock \{stock_symbol\} were added to your stock record")


class PolygonOpenCloseStockDataResponse(BaseModel):
    after_hours: float = Field(..., alias="afterHours")
    close: float
    from_: date = Field(..., alias="from",
                        description="The date in the format YYYY-MM-DD")
    high: float
    low: float
    open: float
    pre_market: float = Field(..., alias="preMarket")
    status: str
    volume: int


class MarketWatchStockDataResponse(BaseModel):
    company_name: str
    performance_data: PerformanceData
    competitors_data: List[Competitor]
