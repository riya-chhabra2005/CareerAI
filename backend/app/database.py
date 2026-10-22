import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# We default to the verified native credentials on localhost
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:prateek@localhost:5432/careerai")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Session factory for DB operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

def check_db_connection() -> bool:
    """
    Executes a SELECT 1 query to verify the connection is alive.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connectivity check failed: {e}")
        return False
