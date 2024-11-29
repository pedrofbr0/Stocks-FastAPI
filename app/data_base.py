# app/data_base.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from app.utils import get_db_url

# Load the database connection URL from config.py
DATABASE_URL = get_db_url()

if not database_exists(DATABASE_URL):
    create_database(DATABASE_URL)
    
# Create the engine for connecting to the database (Factory pattern)
engine = create_engine(DATABASE_URL, echo=True)

# SessionLocal for interacting with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def create_tables_if_not_exists():
    Base.metadata.create_all(bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()