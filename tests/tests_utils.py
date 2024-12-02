# tests/test_utils.py

import pytest
from decimal import Decimal
from app.utils import (
    convert_market_cap_to_decimal,
    convert_performance_percentage_to_float,
    convert_period_to_best_practice,
    get_db_url,
    get_polygon_base_url,
    get_polygon_api_key,
    get_marketwatch_base_url
)
import os

def test_convert_market_cap_to_decimal():
    assert convert_market_cap_to_decimal("1.5B") == Decimal("1500000000")
    assert convert_market_cap_to_decimal("2.3M") == Decimal("2300000")
    assert convert_market_cap_to_decimal("500K") == Decimal("500000")
    assert convert_market_cap_to_decimal("1T") == Decimal("1000000000000")
    with pytest.raises(ValueError):
        convert_market_cap_to_decimal("Invalid")

def test_convert_performance_percentage_to_float():
    assert convert_performance_percentage_to_float("15%") == 0.15
    assert convert_performance_percentage_to_float("-5%") == -0.05
    with pytest.raises(ValueError):
        convert_performance_percentage_to_float("Invalid")

def test_convert_period_to_best_practice():
    assert convert_period_to_best_practice("5 Day") == "five_days"
    assert convert_period_to_best_practice("1 Month") == "one_month"
    assert convert_period_to_best_practice("YTD") == "year_to_date"
    assert convert_period_to_best_practice("Custom Period") == "custom_period"

def test_get_db_url(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_pass")

    expected_url = "postgresql+psycopg2://test_user:test_pass@localhost:5432/test_db"
    assert get_db_url() == expected_url

def test_get_polygon_base_url(monkeypatch):
    monkeypatch.setenv("POLYGON_BASE_URL", "https://api.polygon.io")
    assert get_polygon_base_url() == "https://api.polygon.io"

def test_get_polygon_api_key(monkeypatch):
    monkeypatch.setenv("POLYGON_API_KEY", "test_api_key")
    assert get_polygon_api_key() == "test_api_key"

def test_get_marketwatch_base_url(monkeypatch):
    monkeypatch.setenv("MARKETWATCH_BASE_URL", "https://www.marketwatch.com")
    assert get_marketwatch_base_url() == "https://www.marketwatch.com"
