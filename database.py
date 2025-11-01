from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ----------------------------------------------
# 1. Engine Setup
# ----------------------------------------------

# Use a SQLite file named 'sql_app.db' in the project root
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# The connect_args={'check_same_thread': False} is necessary 
# for SQLite with FastAPI because FastAPI handles concurrent requests.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# ----------------------------------------------
# 2. Session Setup
# ----------------------------------------------

# SessionLocal is the class used to create database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class which your SQLAlchemy models will inherit from.
Base = declarative_base()

# ----------------------------------------------
# 3. Dependency Injection
# ----------------------------------------------

def get_db():
    """A FastAPI dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()