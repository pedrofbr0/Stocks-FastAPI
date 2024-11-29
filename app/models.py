# app/models.py
from app.data_base import Base
from sqlalchemy import Column, Integer, String, DECIMAL

class Stocks(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String, index=True, unique=True)
    purchased_amount = Column(DECIMAL(10, 4))