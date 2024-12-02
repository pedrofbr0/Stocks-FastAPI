# tests/test_main.py

import pytest
from httpx import AsyncClient
from app.main import app
from app.data_base import get_db_session, Base, engine
from sqlalchemy.orm import sessionmaker
from app.models import Stocks
from unittest.mock import patch

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# Override the get_db_session dependency


def override_get_db_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Apllly the override to the app
app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_get_stock_by_symbol(setup_database):
    stock_symbol = "AAPL"

    with patch("app.services.fetch_polygon_open_close_stock_data") as mock_polygon, \
            patch("app.services.fetch_marketwatch_and_scrape_stock_data") as mock_marketwatch:

        mock_polygon.return_value = {
            "status": "OK",
            "from": "2024-11-27",
            "symbol": "AAPL",
            "open": 234.465,
            "high": 235.69,
            "low": 233.8101,
            "close": 234.93,
            "volume": 31604402,
            "afterHours": 235.2,
            "preMarket": 235.5
        }

        mock_marketwatch.return_value = {
            'company_name': 'Apple Inc.',
            'performance_data': {
                'five_days': 0.05,
                'one_month': 0.10,
                'three_months': 0.15,
                'year_to_date': 0.20,
                'one_year': 0.25
            },
            'competitors_data': []
        }

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(f"/stock/{stock_symbol}")
        assert response.status_code == 200
        data = response.json()
        assert data["company_code"] == "AAPL"


@pytest.mark.asyncio
async def test_update_stock_amount(setup_database):
    stock_symbol = "AAPL"
    payload = {"amount": 10}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(f"/stock/{stock_symbol}", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "message" in data

    # Verificar se o estoque foi atualizado
    db = TestingSessionLocal()
    stock = db.query(Stocks).filter(
        Stocks.stock_symbol == stock_symbol).first()
    assert stock is not None
    assert float(stock.purchased_amount) == 10
    db.close()
