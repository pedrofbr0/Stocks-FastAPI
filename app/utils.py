# app/utils.py
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

def convert_market_cap_to_decimal(value: str) -> Decimal:
    """
    Convert a string value to a Decimal.
    """
    multipliers = {
        "T": Decimal("1e12"),
        "B": Decimal("1e9"),
        "M": Decimal("1e6"),
        "K": Decimal("1e3")
    }
    
    # Get the multiplier from the last character of the value
    unit = value[-1]
    multiplier = multipliers.get(unit.upper(), None)
    if multiplier:
        number = value[:-1]
        try:
            return Decimal(number) * multiplier
        except InvalidOperation:
            raise ValueError(f"Invalid number format: {number}")
    else:
        try:
            return Decimal(value)
        except InvalidOperation:
            raise ValueError(f"Invalid value: {value}")

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

def get_db_url():
    # Get the database credentials from the .env file.
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    # Return a URL connection string to the database.
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"

def get_polygon_base_url():
    return os.getenv("POLYGON_BASE_URL")

def get_polygon_api_key():
    return os.getenv("POLYGON_API_KEY")

def get_marketwatch_base_url():
    return os.getenv("MARKETWATCH_BASE_URL")
